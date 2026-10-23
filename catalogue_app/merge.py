import sqlite3
from datetime import datetime
from .db import connect

def merge_catalogs(local_con, remote_db_path, progress_callback=None):
    local_con.execute("PRAGMA foreign_keys = ON")
    remote = sqlite3.connect(remote_db_path)
    remote.row_factory = sqlite3.Row
    
    # Check if remote has volumes
    try:
        remote_vols = remote.execute("SELECT * FROM volumes").fetchall()
    except sqlite3.OperationalError:
        remote.close()
        raise ValueError("Le fichier sélectionné n'est pas un catalogue valide.")

    def log(msg):
        if progress_callback:
            progress_callback(msg)
        else:
            print(msg)

    changes_made = 0

    for r_vol in remote_vols:
        vname = r_vol["name"]
        l_vol = local_con.execute("SELECT * FROM volumes WHERE name=?", (vname,)).fetchone()
        
        # Determine if remote is newer
        r_time = r_vol["scanned_at"] or ""
        l_time = l_vol["scanned_at"] or "" if l_vol else ""
        
        if not l_vol or r_time > l_time:
            log(f"Mise à jour du volume '{vname}' (distant plus récent ou nouveau).")
            
            # Save manual tags from local before deletion
            manual_tags = []
            if l_vol:
                q = """SELECT f.path_norm, t.name, t.kind 
                       FROM files f
                       JOIN file_tags ft ON ft.file_id = f.id
                       JOIN tags t ON ft.tag_id = t.id
                       WHERE f.volume_id = ? AND t.kind = 'manuelle'"""
                manual_tags = local_con.execute(q, (l_vol["id"],)).fetchall()
                
                # Delete local volume (will cascade to files and file_tags if foreign_keys is ON)
                local_con.execute("DELETE FROM volumes WHERE id=?", (l_vol["id"],))
            
            # Insert remote volume
            note = r_vol["note"] if not l_vol else (l_vol["note"] or r_vol["note"])
            priority = r_vol["priority"] if not l_vol else (l_vol["priority"] or r_vol["priority"])
            
            cur = local_con.execute("""INSERT INTO volumes (name, serial, last_path, scanned_at, file_count, total_size, note, priority)
                                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                                    (vname, r_vol["serial"], r_vol["last_path"], r_vol["scanned_at"],
                                     r_vol["file_count"], r_vol["total_size"], note, priority))
            new_vol_id = cur.lastrowid
            
            # Transfer files
            log(f"  -> Importation de {r_vol['file_count']} fichiers...")
            r_files = remote.execute("SELECT * FROM files WHERE volume_id=?", (r_vol["id"],)).fetchall()
            
            cols = ["volume_id", "rel_path", "folder", "name", "name_lower", "name_norm", "path_norm", "ext", "category", "size", "mtime", "quick_hash", "app", "camera", "lens", "duration", "width", "height", "fps", "codec", "shot_date", "meta"]
            
            # Fast insert for files
            file_rows = []
            for rf in r_files:
                file_rows.append(tuple([new_vol_id] + [rf[c] for c in cols[1:]]))
            
            local_con.executemany(f"INSERT INTO files ({','.join(cols)}) VALUES ({','.join('?'*len(cols))})", file_rows)
            
            # Build a mapping from remote file ID to local file ID
            # Since we inserted sequentially, we could use lastrowid but fetching is safer
            # Actually, since we need to migrate tags, we need the mapping.
            # path_norm is unique per volume.
            l_files = local_con.execute("SELECT id, path_norm FROM files WHERE volume_id=?", (new_vol_id,)).fetchall()
            l_file_map = {row["path_norm"]: row["id"] for row in l_files}
            
            # Transfer remote tags
            log(f"  -> Récupération des étiquettes distantes...")
            r_tags_q = """SELECT f.path_norm, t.name, t.kind 
                          FROM files f
                          JOIN file_tags ft ON ft.file_id = f.id
                          JOIN tags t ON ft.tag_id = t.id
                          WHERE f.volume_id = ?"""
            r_file_tags = remote.execute(r_tags_q, (r_vol["id"],)).fetchall()
            
            # Combine remote tags + saved local manual tags
            all_tags_to_apply = r_file_tags + manual_tags
            
            # Insert any missing tags in local DB
            unique_tags = {(t["name"], t["kind"]) for t in all_tags_to_apply}
            for t_name, t_kind in unique_tags:
                local_con.execute("INSERT OR IGNORE INTO tags (name, kind) VALUES (?, ?)", (t_name, t_kind))
            
            # Get local tag IDs
            l_tags = local_con.execute("SELECT id, name, kind FROM tags").fetchall()
            l_tag_map = {(row["name"], row["kind"]): row["id"] for row in l_tags}
            
            # Create file_tags links
            ft_inserts = []
            seen_ft = set()
            for t in all_tags_to_apply:
                lf_id = l_file_map.get(t["path_norm"])
                lt_id = l_tag_map.get((t["name"], t["kind"]))
                if lf_id and lt_id and (lf_id, lt_id) not in seen_ft:
                    ft_inserts.append((lf_id, lt_id))
                    seen_ft.add((lf_id, lt_id))
            
            local_con.executemany("INSERT OR IGNORE INTO file_tags (file_id, tag_id) VALUES (?, ?)", ft_inserts)
            
            changes_made += 1
            log(f"  -> Volume '{vname}' fusionné avec succès.")

    local_con.commit()
    remote.close()
    
    if changes_made == 0:
        log("Aucune mise à jour requise. Le catalogue local est déjà à jour.")
    else:
        log(f"Fusion terminée : {changes_made} volume(s) mis à jour.")

    return changes_made

