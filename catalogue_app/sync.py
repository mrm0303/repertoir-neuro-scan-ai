import sqlite3
import os
from .db import *
from .utils import *

def merge_databases(dest_path: str, src_path: str, progress_cb=None):
    """
    Fusionne la base `src_path` dans `dest_path`.
    """
    if not progress_cb:
        progress_cb = lambda msg: None
        
    progress_cb(f"Connexion à la base source : {os.path.basename(src_path)}...")
    src = sqlite3.connect(src_path)
    src.row_factory = sqlite3.Row
    dest = connect(dest_path)
    
    # 1. Fusionner les volumes
    src_vols = src.execute("SELECT * FROM volumes").fetchall()
    vol_map = {} # src_vol_id -> dest_vol_id
    
    for v in src_vols:
        # Check if volume exists by name
        row = dest.execute("SELECT id FROM volumes WHERE name=?", (v["name"],)).fetchone()
        if row:
            dest_vol_id = row["id"]
            dest_scan = dest.execute("SELECT scanned_at FROM volumes WHERE id=?", (dest_vol_id,)).fetchone()["scanned_at"]
            if (v["scanned_at"] or "") > (dest_scan or ""):
                dest.execute("UPDATE volumes SET scanned_at=?, file_count=?, total_size=? WHERE id=?",
                             (v["scanned_at"], v["file_count"], v["total_size"], dest_vol_id))
        else:
            cur = dest.execute("INSERT INTO volumes (name, label, scanned_at, file_count, total_size, note, priority) VALUES (?, ?, ?, ?, ?, ?, ?)",
                               (v["name"], v["label"], v["scanned_at"], v["file_count"], v["total_size"], v["note"], v["priority"]))
            dest_vol_id = cur.lastrowid
        vol_map[v["id"]] = dest_vol_id
        
    # 2. Fusionner les tags
    src_tags = src.execute("SELECT * FROM tags").fetchall()
    tag_map = {} # src_tag_id -> dest_tag_id
    for t in src_tags:
        row = dest.execute("SELECT id FROM tags WHERE name=? AND kind=?", (t["name"], t["kind"])).fetchone()
        if row:
            tag_map[t["id"]] = row["id"]
        else:
            cur = dest.execute("INSERT INTO tags (name, kind) VALUES (?, ?)", (t["name"], t["kind"]))
            tag_map[t["id"]] = cur.lastrowid
            
    # 3. Fusionner les fichiers
    for src_vid, dest_vid in vol_map.items():
        progress_cb(f"Fusion des fichiers du volume {src_vid}...")
        
        src_files = src.execute("SELECT * FROM files WHERE volume_id=?", (src_vid,)).fetchall()
        inserted = 0
        file_map = {}
        
        for f in src_files:
            row = dest.execute("SELECT id FROM files WHERE volume_id=? AND path_norm=?", (dest_vid, f["path_norm"])).fetchone()
            if row:
                file_map[f["id"]] = row["id"]
            else:
                cols = ("volume_id", "rel_path", "folder", "name", "name_lower", "name_norm",
                        "path_norm", "ext", "category", "size", "mtime", "quick_hash", "app",
                        "camera", "lens", "duration", "width", "height", "fps", "codec",
                        "shot_date", "meta")
                vals = [dest_vid] + [f[c] for c in cols[1:]]
                cur = dest.execute(f"INSERT INTO files ({','.join(cols)}) VALUES ({','.join('?'*len(cols))})", vals)
                file_map[f["id"]] = cur.lastrowid
                inserted += 1
                
        progress_cb(f"{inserted} nouveaux fichiers ajoutés.")
        
        # 4. Fusionner les file_tags
        progress_cb(f"Fusion des étiquettes...")
        src_ft = src.execute("SELECT ft.file_id, ft.tag_id FROM file_tags ft JOIN files f ON ft.file_id=f.id WHERE f.volume_id=?", (src_vid,)).fetchall()
        for ft in src_ft:
            d_fid = file_map.get(ft["file_id"])
            d_tid = tag_map.get(ft["tag_id"])
            if d_fid and d_tid:
                dest.execute("INSERT OR IGNORE INTO file_tags (file_id, tag_id) VALUES (?, ?)", (d_fid, d_tid))
                
    dest.commit()
    src.close()
    dest.close()
    progress_cb("Fusion terminée avec succès !")
