"""
Module d'import / export de catalogues portables (.catpkg / JSON gzip).
Permet le partage de catalogues entre machines, la collaboration en équipe,
la sauvegarde hors-ligne et la synchronisation sans dépendance cloud imposée.
"""

import os
import json
import gzip
import sqlite3
import base64
from datetime import datetime
from .utils import normalize, human_size

MAGIC_HEADER = "CATALOGUE_DISQUES_PACKAGE_V1"

def export_catalog(con, output_path, volume_ids=None, include_embeddings=True, progress_cb=None):
    """
    Exporte un ou plusieurs volumes (ou tout le catalogue) dans une archive compressée .catpkg.
    """
    if volume_ids:
        placeholders = ",".join("?" for _ in volume_ids)
        vol_rows = con.execute(f"SELECT * FROM volumes WHERE id IN ({placeholders})", volume_ids).fetchall()
    else:
        vol_rows = con.execute("SELECT * FROM volumes").fetchall()
        
    if not vol_rows:
        raise ValueError("Aucun disque sélectionné pour l'export.")
        
    export_data = {
        "format": MAGIC_HEADER,
        "exported_at": datetime.now().isoformat(),
        "volumes": [],
        "files": [],
        "tags": [],
        "file_tags": [],
        "embeddings": []
    }
    
    vol_id_map = {}
    for vr in vol_rows:
        v_dict = dict(vr)
        export_data["volumes"].append(v_dict)
        vol_id_map[v_dict["id"]] = v_dict["name"]
        
    vids = list(vol_id_map.keys())
    v_placeholders = ",".join("?" for _ in vids)
    
    # 1. Fetch files
    files_query = f"SELECT * FROM files WHERE volume_id IN ({v_placeholders})"
    f_rows = con.execute(files_query, vids).fetchall()
    total_files = len(f_rows)
    
    file_id_set = set()
    for idx, fr in enumerate(f_rows):
        f_dict = dict(fr)
        export_data["files"].append(f_dict)
        file_id_set.add(f_dict["id"])
        if progress_cb and idx % 2000 == 0:
            progress_cb(f"Export des fichiers : {idx}/{total_files}", idx, total_files)
            
    # 2. Fetch tags and file_tags
    if file_id_set:
        f_ids_list = list(file_id_set)
        # Fetch in chunks
        chunk_size = 900
        for i in range(0, len(f_ids_list), chunk_size):
            chunk = f_ids_list[i:i + chunk_size]
            p_chunk = ",".join("?" for _ in chunk)
            ft_rows = con.execute(
                f"""SELECT ft.file_id, t.name, t.kind 
                   FROM file_tags ft 
                   JOIN tags t ON t.id = ft.tag_id 
                   WHERE ft.file_id IN ({p_chunk})""", chunk).fetchall()
            for r in ft_rows:
                export_data["file_tags"].append({
                    "file_id": r["file_id"],
                    "tag_name": r["name"],
                    "tag_kind": r["kind"]
                })
                
        # 3. Fetch embeddings if requested
        if include_embeddings:
            for i in range(0, len(f_ids_list), chunk_size):
                chunk = f_ids_list[i:i + chunk_size]
                p_chunk = ",".join("?" for _ in chunk)
                emb_rows = con.execute(
                    f"SELECT file_id, embedding FROM file_embeddings WHERE file_id IN ({p_chunk})", chunk).fetchall()
                for er in emb_rows:
                    if er["embedding"]:
                        export_data["embeddings"].append({
                            "file_id": er["file_id"],
                            "emb_b64": base64.b64encode(er["embedding"]).decode('ascii')
                        })
                        
    if progress_cb:
        progress_cb("Compression et écriture sur disque...", total_files, total_files)
        
    with gzip.open(output_path, "wt", encoding="utf-8") as gz:
        json.dump(export_data, gz, ensure_ascii=False)
        
    return {
        "volumes_count": len(export_data["volumes"]),
        "files_count": len(export_data["files"]),
        "tags_count": len(export_data["file_tags"]),
        "embeddings_count": len(export_data["embeddings"]),
        "path": output_path
    }


def import_catalog(con, input_path, progress_cb=None):
    """
    Importe une archive .catpkg dans la base de données courante.
    Fusionne intelligemment sans écraser les autres disques.
    """
    if progress_cb:
        progress_cb("Lecture de l'archive...", 0, 0)
        
    with gzip.open(input_path, "rt", encoding="utf-8") as gz:
        data = json.load(gz)
        
    if data.get("format") != MAGIC_HEADER:
        raise ValueError("Format de fichier de catalogue invalide ou corrompu.")
        
    volumes = data.get("volumes", [])
    files = data.get("files", [])
    file_tags = data.get("file_tags", [])
    embeddings = data.get("embeddings", [])
    
    vol_old_to_new = {}
    
    # 1. Traitement des volumes
    for v in volumes:
        orig_name = v["name"]
        target_name = orig_name
        # Si le volume existe déjà, on vérifie s'il faut le renommer (ex: MonDisque (Importé))
        existing = con.execute("SELECT id FROM volumes WHERE name = ?", (target_name,)).fetchone()
        suffix_idx = 1
        while existing:
            target_name = f"{orig_name} (Import {suffix_idx})"
            existing = con.execute("SELECT id FROM volumes WHERE name = ?", (target_name,)).fetchone()
            suffix_idx += 1
            
        con.execute(
            """INSERT INTO volumes (name, serial, last_path, scanned_at, file_count, total_size, note, priority)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (target_name, v.get("serial"), v.get("last_path"), v.get("scanned_at"),
             v.get("file_count", 0), v.get("total_size", 0), v.get("note", "") + " [Importé]", v.get("priority", 0))
        )
        new_vol_id = con.execute("SELECT last_insert_rowid() as id").fetchone()["id"]
        vol_old_to_new[v["id"]] = new_vol_id
        
    con.commit()
    
    # 2. Traitement des fichiers
    total_files = len(files)
    file_old_to_new = {}
    
    file_cols = [
        "rel_path", "folder", "name", "name_lower", "name_norm", "path_norm",
        "ext", "category", "size", "mtime", "quick_hash", "app", "camera",
        "lens", "duration", "width", "height", "fps", "codec", "shot_date", "meta"
    ]
    
    insert_sql = f"""
        INSERT INTO files (volume_id, {", ".join(file_cols)})
        VALUES (?, {", ".join("?" for _ in file_cols)})
    """
    
    batch = []
    for idx, f in enumerate(files):
        old_fid = f["id"]
        old_vid = f["volume_id"]
        new_vid = vol_old_to_new.get(old_vid)
        if not new_vid:
            continue
            
        row_vals = [new_vid] + [f.get(c) for c in file_cols]
        cur = con.execute(insert_sql, row_vals)
        new_fid = cur.lastrowid
        file_old_to_new[old_fid] = new_fid
        
        if progress_cb and idx % 2000 == 0:
            progress_cb(f"Import des fichiers : {idx}/{total_files}", idx, total_files)
            con.commit()
            
    con.commit()
    
    # 3. Traitement des tags
    from .db import TagCache
    tc = TagCache(con)
    tag_pairs = []
    for ft in file_tags:
        new_fid = file_old_to_new.get(ft["file_id"])
        if new_fid:
            tid = tc.id_for(ft["tag_name"], ft.get("tag_kind", "auto"))
            tag_pairs.append((new_fid, tid))
            
    if tag_pairs:
        con.executemany("INSERT OR IGNORE INTO file_tags (file_id, tag_id) VALUES (?, ?)", tag_pairs)
        con.commit()
        
    # 4. Traitement des embeddings
    emb_pairs = []
    for emb in embeddings:
        new_fid = file_old_to_new.get(emb["file_id"])
        if new_fid and emb.get("emb_b64"):
            raw_blob = base64.b64decode(emb["emb_b64"])
            emb_pairs.append((new_fid, raw_blob))
            
    if emb_pairs:
        con.executemany("INSERT OR REPLACE INTO file_embeddings (file_id, embedding) VALUES (?, ?)", emb_pairs)
        con.commit()
        
    return {
        "volumes_imported": len(volumes),
        "files_imported": len(file_old_to_new),
        "tags_imported": len(tag_pairs),
        "embeddings_imported": len(emb_pairs)
    }
