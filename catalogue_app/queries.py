import os, sqlite3
from .config import *
from .utils import *
from .db import *

SEARCH_FIELDS = {
    "partout": None,
    "nom": "name_norm",
    "dossier / chemin": "folder",
    "caméra": "camera",
    "extension": "ext",
    "codec vidéo/audio": "codec",
    "métadonnées (exif)": "meta",
    "logiciel (app)": "app",
}
SORT_FIELDS = {
    "taille": "f.size",
    "nom": "f.name_norm",
    "date": "f.mtime",
    "durée": "f.duration",
    "disque": "v.name",
    "caméra": "f.camera",
    "dossier": "f.folder",
    "définition": "f.width",
}
YEAR_EXPR = ("COALESCE(NULLIF(substr(f.shot_date,1,4),''), "
             "strftime('%Y', f.mtime, 'unixepoch'))")


def search_files(con, text="", category=None, global_cat=None, volume_id=None, volume_ids=None, camera=None,
                 tags=None, min_size_mb=0, field="partout", year_from=None,
                 year_to=None, sort="taille", desc=True, limit=5000, file_ids=None):
    sql = ["SELECT f.*, v.name AS volume_name FROM files f",
           "JOIN volumes v ON v.id = f.volume_id WHERE 1=1"]
    args = []
    
    if file_ids is not None:
        if file_ids:
            sql.append(f"AND f.id IN ({','.join(file_ids)})")
        else:
            sql.append("AND 1=0") # No results
    words = [w for w in normalize(text).split() if w]
    col = SEARCH_FIELDS.get(field)
    
    # Tentative d'accélération FTS5 plein texte (gain x10 à x50 sur gros volume)
    used_fts = False
    if words:
        try:
            # Vérifier si FTS5 est actif
            has_fts = con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='files_fts'").fetchone()
            if has_fts:
                # Construire la requête FTS5
                fts_terms = []
                for w in words:
                    # Échapper les guillemets
                    clean_w = w.replace('"', '')
                    if clean_w:
                        if field == "nom":
                            fts_terms.append(f'name: "{clean_w}"*')
                        elif field in ("dossier / chemin", "dossier"):
                            fts_terms.append(f'folder: "{clean_w}"*')
                        elif field == "caméra":
                            fts_terms.append(f'camera: "{clean_w}"*')
                        elif field in ("métadonnées (exif)", "meta"):
                            fts_terms.append(f'meta: "{clean_w}"*')
                        elif col is None: # Partout
                            fts_terms.append(f'"{clean_w}"*')
                
                if fts_terms:
                    fts_query = " AND ".join(fts_terms)
                    sql.append("AND f.id IN (SELECT rowid FROM files_fts WHERE files_fts MATCH ?)")
                    args.append(fts_query)
                    used_fts = True
        except Exception:
            used_fts = False

    # Fallback classique LIKE si FTS5 n'a pas été utilisé
    if not used_fts and words:
        for word in words:
            if col is None:
                sql.append("AND (f.name_norm LIKE ? OR f.path_norm LIKE ?)")
                args += [f"%{word}%"] * 2
            elif col in ("folder", "camera", "ext"):
                sql.append(f"AND LOWER(f.{col}) LIKE ?")
                args.append(f"%{word}%")
            else:
                sql.append(f"AND f.{col} LIKE ?")
                args.append(f"%{word}%")
    if category and category != "toutes":
        sql.append("AND f.category = ?")
        args.append(category)
    if global_cat and global_cat != "(toutes)":
        sql.append("AND f.global_cat = ?")
        args.append(global_cat)
    if volume_id:
        sql.append("AND f.volume_id = ?")
        args.append(volume_id)
    if volume_ids:
        placeholders = ",".join("?" for _ in volume_ids)
        sql.append(f"AND f.volume_id IN ({placeholders})")
        args.extend(volume_ids)
    if camera:
        sql.append("AND f.camera LIKE ?")
        args.append(f"%{camera}%")
    for tag in (tags or []):
        tag = tag.strip()
        if not tag:
            continue
        if tag.startswith("ia:"):
            # Use LIKE so that searching 'ia:homme' matches 'ia:un homme avec chapeau'
            sql.append("""AND EXISTS (SELECT 1 FROM file_tags ft JOIN tags t ON t.id=ft.tag_id
                                      WHERE ft.file_id=f.id AND t.name LIKE ? COLLATE NOCASE)""")
            args.append(f"%{tag}%")
        else:
            sql.append("""AND EXISTS (SELECT 1 FROM file_tags ft JOIN tags t ON t.id=ft.tag_id
                                      WHERE ft.file_id=f.id AND t.name = ? COLLATE NOCASE)""")
            args.append(tag)
    if year_from:
        sql.append(f"AND {YEAR_EXPR} >= ?")
        args.append(str(year_from))
    if year_to:
        sql.append(f"AND {YEAR_EXPR} <= ?")
        args.append(str(year_to))
    if min_size_mb:
        sql.append("AND f.size >= ?")
        args.append(int(float(min_size_mb) * 1024 * 1024))
    order = SORT_FIELDS.get(sort, "f.size")
    sql.append(f"ORDER BY {order} IS NULL, {order} {'DESC' if desc else 'ASC'} LIMIT ?")
    args.append(limit)
    return [dict(r) for r in con.execute(" ".join(sql), args).fetchall()]


def list_projects(con, text="", vols=None):
    sql = ["""SELECT f.*, v.name AS volume_name FROM files f
              JOIN volumes v ON v.id = f.volume_id WHERE f.category = 'projet'"""]
    args = []
    if vols:
        p = ",".join(["?"]*len(vols))
        sql.append(f"AND v.name IN ({p})")
        args += vols
    if text.strip():
        sql.append("AND (f.name_norm LIKE ? OR f.path_norm LIKE ?)")
        args += [f"%{normalize(text)}%"] * 2
    sql.append("ORDER BY f.mtime DESC LIMIT 5000")
    return [dict(r) for r in con.execute(" ".join(sql), args).fetchall()]


def stats(con):
    v = con.execute("SELECT COUNT(*) n, COALESCE(SUM(total_size),0) s FROM volumes").fetchone()
    by_cat = con.execute("SELECT category, COUNT(*) n, COALESCE(SUM(size),0) s "
                         "FROM files GROUP BY category ORDER BY s DESC").fetchall()
    f = {
        "n": sum((r["n"] or 0) for r in by_cat),
        "s": sum((r["s"] or 0) for r in by_cat),
    }
    return v, f, by_cat


def locations_across_disks(con, min_disks=2, by="projet"):
    if by != "projet":
        raise ValueError(f"Grouping by {by} is not supported yet.")

    query = '''
        SELECT v.name AS volume_name, f.rel_path, f.size
        FROM files f
        JOIN volumes v ON f.volume_id = v.id
    '''
    
    projects = {}
    for row in con.execute(query):
        vol_name = row["volume_name"]
        rel_path = row["rel_path"]
        vol_size = row["size"] or 0
        
        proj_name = rel_path.replace('\\', '/').split('/')[0]
        
        if proj_name not in projects:
            projects[proj_name] = {"disks": {}}
            
        if vol_name not in projects[proj_name]["disks"]:
            projects[proj_name]["disks"][vol_name] = {"files": 0, "size": 0}
            
        projects[proj_name]["disks"][vol_name]["files"] += 1
        projects[proj_name]["disks"][vol_name]["size"] += vol_size
            
    result = []
    for proj_name, data in projects.items():
        if len(data["disks"]) >= min_disks:
            disks_list = []
            for v_name, d_data in data["disks"].items():
                disks_list.append({
                    "volume": v_name,
                    "files": d_data["files"],
                    "size": d_data["size"]
                })
            disks_list.sort(key=lambda d: d["volume"])
            
            total_size = sum(d["size"] for d in disks_list)
            max_size = max((d["size"] for d in disks_list), default=0)
            
            result.append({
                "name": proj_name,
                "n_disks": len(disks_list),
                "total_size": total_size,
                "redundant_size": total_size - max_size,
                "disks": disks_list
            })
            
    result.sort(key=lambda r: r["name"])
    return result


# ---------------------------------------------------------------------------
# Doublons et plan de réduction (Fichiers & Dossiers)
# ---------------------------------------------------------------------------

def build_cat_ext_filter(categories=None, extensions=None):
    """
    Construit les clauses SQL et arguments pour filtrer par catégories et/ou extensions.
    Prend en compte 'disk_image' qui cible les fichiers ISO, DMG, IMG...
    """
    clauses = []
    args = []

    if extensions:
        clean_exts = []
        if isinstance(extensions, str):
            clean_exts = [e.strip().lstrip(".").lower() for e in extensions.replace(",", " ").split() if e.strip()]
        else:
            clean_exts = [e.lstrip(".").lower() for e in extensions if e]
        if clean_exts:
            placeholders = ",".join("?" for _ in clean_exts)
            clauses.append(f"LOWER(f.ext) IN ({placeholders})")
            args.extend(clean_exts)

    if categories:
        cat_subclauses = []
        for cat in categories:
            if cat == "disk_image":
                from catalogue_app.config import DISK_IMAGE_EXT
                placeholders = ",".join("?" for _ in DISK_IMAGE_EXT)
                cat_subclauses.append(f"LOWER(f.ext) IN ({placeholders})")
                args.extend(list(DISK_IMAGE_EXT))
            elif cat == "logiciel":
                from catalogue_app.config import LOGICIEL_EXT
                placeholders = ",".join("?" for _ in LOGICIEL_EXT)
                cat_subclauses.append(f"(f.category = 'logiciel' OR LOWER(f.ext) IN ({placeholders}))")
                args.extend(list(LOGICIEL_EXT))
            else:
                cat_subclauses.append("f.category = ?")
                args.append(cat)
        if cat_subclauses:
            clauses.append(f"({' OR '.join(cat_subclauses)})")

    if not clauses:
        return "", []
    return " AND ".join(clauses), args


def duplicate_groups(con, min_size_mb=10, min_copies=2, limit_groups=2000, selected_vols=None, categories=None, extensions=None, strict_name=True):
    min_bytes = int(float(min_size_mb) * 1024 * 1024)
    
    if strict_name:
        query = ["SELECT f.quick_hash, f.name_norm, COUNT(*) n, MAX(f.size) size, COUNT(DISTINCT f.volume_id) n_vol",
                 "FROM files f WHERE f.quick_hash <> '' AND f.quick_hash IS NOT NULL AND f.size >= ?"]
    else:
        query = ["SELECT f.quick_hash, COUNT(*) n, MAX(f.size) size, COUNT(DISTINCT f.volume_id) n_vol",
                 "FROM files f WHERE f.quick_hash <> '' AND f.quick_hash IS NOT NULL AND f.size >= ?"]
                 
    args = [min_bytes]
    if selected_vols:
        placeholders = ",".join("?" for _ in selected_vols)
        query.append(f"AND f.volume_id IN ({placeholders})")
        args.extend(selected_vols)

    cat_clause, cat_args = build_cat_ext_filter(categories, extensions)
    if cat_clause:
        query.append(f"AND {cat_clause}")
        args.extend(cat_args)

    if strict_name:
        query.append("GROUP BY f.quick_hash, f.name_norm HAVING n >= ?")
    else:
        query.append("GROUP BY f.quick_hash HAVING n >= ?")
        
    args.extend([min_copies])
    rows = con.execute(" ".join(query), args).fetchall()
    
    # Sort in Python to avoid SQLite TEMP B-TREE freeze on complex GROUP BY
    rows = [dict(r) for r in rows]
    rows.sort(key=lambda r: (r["n"] - 1) * r["size"], reverse=True)
    return rows[:limit_groups]


def group_copies(con, quick_hash_value, selected_vols=None, categories=None, extensions=None):
    query = ["SELECT f.*, v.name AS volume_name, v.priority AS volume_priority",
             "FROM files f JOIN volumes v ON v.id = f.volume_id WHERE f.quick_hash = ?"]
    args = [quick_hash_value]
    if selected_vols:
        placeholders = ",".join("?" for _ in selected_vols)
        query.append(f"AND f.volume_id IN ({placeholders})")
        args.extend(selected_vols)

    cat_clause, cat_args = build_cat_ext_filter(categories, extensions)
    if cat_clause:
        query.append(f"AND {cat_clause}")
        args.extend(cat_args)

    query.append("ORDER BY v.priority DESC, v.name, f.rel_path")
    return con.execute(" ".join(query), args).fetchall()


def plan_deduplication(con, keep=2, min_size_mb=50, limit_groups=2000, selected_vols=None, categories=None, extensions=None, strict_name=True):
    """
    Construit le plan de réduction par fichier avec filtres de disques, catégories et extensions.
    Optimisé par requêtes SQL groupées par lots (chunking).
    """
    groups = duplicate_groups(con, min_size_mb, min_copies=2, limit_groups=limit_groups,
                              selected_vols=selected_vols, categories=categories, extensions=extensions, strict_name=strict_name)
    if not groups:
        return []

    if strict_name:
        hash_map = {(g["quick_hash"], g["name_norm"]): g for g in groups}
        target_hashes = list({g["quick_hash"] for g in groups}) # Unique hashes
    else:
        hash_map = {g["quick_hash"]: g for g in groups}
        target_hashes = list(hash_map.keys())

    copies_by_hash = defaultdict(list)
    cat_clause, cat_args = build_cat_ext_filter(categories, extensions)

    CHUNK_SIZE = 500
    for i in range(0, len(target_hashes), CHUNK_SIZE):
        chunk = target_hashes[i:i + CHUNK_SIZE]
        placeholders = ",".join("?" for _ in chunk)
        query = [
            "SELECT f.*, v.name AS volume_name, v.priority AS volume_priority",
            f"FROM files f JOIN volumes v ON v.id = f.volume_id WHERE f.quick_hash IN ({placeholders})"
        ]
        args = list(chunk)
        if selected_vols:
            placeholders_vol = ",".join("?" for _ in selected_vols)
            query.append(f"AND f.volume_id IN ({placeholders_vol})")
            args.extend(selected_vols)
        if cat_clause:
            query.append(f"AND {cat_clause}")
            args.extend(cat_args)

        for row in con.execute(" ".join(query), args).fetchall():
            row_dict = dict(row)
            if strict_name:
                copies_by_hash[(row_dict["quick_hash"], row_dict["name_norm"])].append(row_dict)
            else:
                copies_by_hash[row_dict["quick_hash"]].append(row_dict)

    plan = []
    for key, g in hash_map.items():
        copies = copies_by_hash.get(key, [])
        if len(copies) < 2:
            continue

        by_vol = defaultdict(list)
        for c in copies:
            by_vol[c["volume_name"]].append(c)

        keep_rows, drop_rows = [], []
        best_per_vol = []
        for vol, rows in by_vol.items():
            rows = sorted(rows, key=lambda r: (r["rel_path"].count(os.sep)
                                               + r["rel_path"].count("/"), len(r["rel_path"])))
            best_per_vol.append(rows[0])
            drop_rows.extend(rows[1:])          # règle 1 : copies internes redondantes

        best_per_vol.sort(key=lambda r: (-(r["volume_priority"] or 0),
                                         r["rel_path"].count(os.sep) + r["rel_path"].count("/"),
                                         r["volume_name"]))
        keep_rows = best_per_vol[:keep]
        drop_rows.extend(best_per_vol[keep:])   # règles 2 et 3

        if drop_rows:
            cat = copies[0]["category"] or "" if copies else ""
            ext = copies[0]["ext"] or "" if copies else ""
            plan.append({
                "type": "file",
                "hash": key[0] if strict_name else key, "name": copies[0]["name"], "size": g["size"],
                "category": cat, "ext": ext,
                "copies": g["n"], "volumes": g["n_vol"],
                "keep": keep_rows, "drop": drop_rows,
                "reclaim": sum(r["size"] or 0 for r in drop_rows),
            })
    plan.sort(key=lambda p: p["reclaim"], reverse=True)
    return plan


def plan_folder_deduplication(con, keep=1, min_size_mb=20, min_files=2, limit_groups=1000, selected_vols=None, categories=None, extensions=None):
    """
    Détecte les dossiers entiers en doublon (dossiers jumeaux ou miroirs).
    Deux dossiers sont considérés comme doublons s'ils partagent le même contenu
    (mêmes fichiers avec mêmes tailles et hashes).
    """
    import hashlib
    min_bytes = int(float(min_size_mb) * 1024 * 1024)
    query = [
        "SELECT f.volume_id, v.name AS volume_name, v.priority AS volume_priority,",
        "f.folder, COUNT(*) AS file_count, SUM(f.size) AS total_size",
        "FROM files f",
        "JOIN volumes v ON v.id = f.volume_id",
        "WHERE f.folder <> '' AND f.size > 0"
    ]
    args = []

    if selected_vols:
        placeholders = ",".join("?" for _ in selected_vols)
        query.append(f"AND f.volume_id IN ({placeholders})")
        args.extend(selected_vols)

    cat_clause, cat_args = build_cat_ext_filter(categories, extensions)
    if cat_clause:
        query.append(f"AND {cat_clause}")
        args.extend(cat_args)

    query.append("GROUP BY f.volume_id, f.folder")
    query.append("HAVING COUNT(*) >= ? AND SUM(f.size) >= ?")
    args.extend([min_files, min_bytes])

    rows = con.execute(" ".join(query), args).fetchall()
    if not rows:
        return []

    # Regrouper les dossiers candidats par (file_count, total_size)
    by_signature = defaultdict(list)
    for r in rows:
        by_signature[(r["file_count"], r["total_size"])].append(dict(r))

    candidate_groups = [group for group in by_signature.values() if len(group) > 1]
    candidate_groups = candidate_groups[:limit_groups]
    if not candidate_groups:
        return []

    # Extraire la liste de tous les couples (volume_id, folder) pour requêter par lots
    all_cand_folders = []
    for grp in candidate_groups:
        for folder_info in grp:
            all_cand_folders.append((folder_info["volume_id"], folder_info["folder"]))

    folder_files_map = defaultdict(list)
    CHUNK_SIZE = 150
    for i in range(0, len(all_cand_folders), CHUNK_SIZE):
        chunk = all_cand_folders[i:i + CHUNK_SIZE]
        pair_clauses = ["(volume_id=? AND folder=?)" for _ in chunk]
        sql = f"SELECT volume_id, folder, name_norm, size, quick_hash FROM files WHERE {' OR '.join(pair_clauses)}"
        params = []
        for v_id, f_path in chunk:
            params.extend([v_id, f_path])
        for f_row in con.execute(sql, params).fetchall():
            folder_files_map[(f_row["volume_id"], f_row["folder"])].append(f_row)

    plan = []
    for grp in candidate_groups:
        by_fingerprint = defaultdict(list)
        for folder_info in grp:
            vol_id = folder_info["volume_id"]
            f_path = folder_info["folder"]
            f_rows = folder_files_map.get((vol_id, f_path), [])
            f_rows.sort(key=lambda fr: fr["name_norm"])
            fp_str = "".join(f"{fr['name_norm']}:{fr['size']}:{fr['quick_hash']}" for fr in f_rows)
            fp_hash = hashlib.md5(fp_str.encode("utf-8", "ignore")).hexdigest()
            folder_info["fingerprint"] = fp_hash
            folder_info["folder_name"] = os.path.basename(f_path) or f_path
            folder_info["rel_path"] = f_path
            folder_info["name"] = folder_info["folder_name"]
            folder_info["size"] = folder_info["total_size"]
            by_fingerprint[fp_hash].append(folder_info)

        for fp_hash, matched_folders in by_fingerprint.items():
            if len(matched_folders) < 2:
                continue

            matched_folders.sort(
                key=lambda f: (
                    -(f["volume_priority"] or 0),
                    f["folder"].count(os.sep) + f["folder"].count("/"),
                    f["volume_name"]
                )
            )

            keep_folders = matched_folders[:keep]
            drop_folders = matched_folders[keep:]

            if drop_folders:
                display_name = matched_folders[0]["folder_name"]
                rep_folder = matched_folders[0]
                plan.append({
                    "type": "folder",
                    "hash": fp_hash,
                    "name": display_name,
                    "folder_name": display_name,
                    "folder_path": rep_folder["folder"],
                    "size": rep_folder["total_size"],
                    "file_count": rep_folder["file_count"],
                    "copies": len(matched_folders),
                    "volumes": len(set(f["volume_name"] for f in matched_folders)),
                    "keep": keep_folders,
                    "drop": drop_folders,
                    "reclaim": sum(f["total_size"] or 0 for f in drop_folders),
                })

    plan.sort(key=lambda p: p["reclaim"], reverse=True)
    return plan


def plan_by_volume(plan):
    """Récapitulatif : combien chaque disque libérerait si le plan était appliqué."""
    agg = defaultdict(lambda: {"files": 0, "size": 0})
    for grp in plan:
        is_folder = grp.get("type") == "folder"
        for r in grp["drop"]:
            vol = r["volume_name"]
            a = agg[vol]
            if is_folder:
                cnt = r["file_count"] if "file_count" in r.keys() else 1
                sz = r["total_size"] if "total_size" in r.keys() else (r["size"] if "size" in r.keys() else 0)
                a["files"] += cnt
                a["size"] += sz
            else:
                a["files"] += 1
                sz = r["size"] if "size" in r.keys() else 0
                a["size"] += sz
    return sorted(((k, v["files"], v["size"]) for k, v in agg.items()),
                  key=lambda x: x[2], reverse=True)


def verify_group(con, grp):
    """Vérifie par empreinte complète que les copies encore accessibles sont identiques.
    Retourne (statut, message). Les disques non branchés sont signalés."""
    is_folder = grp.get("type") == "folder"
    digests, missing = {}, []
    online = online_map(con)
    for r in grp["keep"] + grp["drop"]:
        path = full_path_of(con, r, online)
        if not os.path.exists(path):
            missing.append(r["volume_name"])
            continue
        if is_folder and os.path.isdir(path):
            import hashlib
            f_hashes = []
            for root, _, files in os.walk(path):
                for fn in sorted(files):
                    if fn in SKIP_FILES or fn.startswith("._"):
                        continue
                    fp = os.path.join(root, fn)
                    try:
                        sz = os.path.getsize(fp)
                        h = quick_hash(fp, sz)
                        rel = os.path.relpath(fp, path)
                        f_hashes.append(f"{rel}:{sz}:{h}")
                    except Exception:
                        pass
            dig_str = hashlib.md5("".join(f_hashes).encode("utf-8")).hexdigest()
            digests[f'{r["volume_name"]} : {r.get("folder", path)}'] = dig_str
        elif os.path.isfile(path):
            digests[f'{r["volume_name"]} : {r.get("rel_path", path)}'] = full_hash(path)
    if not digests:
        return "inconnu", "Aucune copie accessible : branchez au moins deux disques."
    uniq = set(digests.values())
    if len(digests) < 2:
        return "partiel", ("Une seule copie accessible. Disques absents : "
                           + ", ".join(sorted(set(missing))))
    if len(uniq) == 1:
        item_label = "dossiers" if is_folder else "copies"
        msg = f"{len(digests)} {item_label} vérifiés : strictement identiques."
        if missing:
            msg += " Non vérifiés (disques absents) : " + ", ".join(sorted(set(missing)))
        return "identique", msg
    return "different", ("ATTENTION : les contenus diffèrent malgré une structure similaire. "
                         "Ne supprimez rien dans ce groupe.")


# ---------------------------------------------------------------------------
# Exports
# ---------------------------------------------------------------------------

def export_rows(rows, path, con=None, with_tags=False):
    cols = ["volume_name", "rel_path", "name", "ext", "category", "size", "duration",
            "camera", "lens", "width", "height", "fps", "codec", "shot_date", "app", "quick_hash"]
    head = ["Disque", "Chemin", "Nom", "Extension", "Catégorie", "Taille (octets)",
            "Durée (s)", "Caméra", "Objectif", "Largeur", "Hauteur", "IPS", "Codec",
            "Date de prise", "Logiciel", "Empreinte"]
    if with_tags:
        head.append("Étiquettes")
    tagmap = {}
    if with_tags and con is not None:
        tagmap = tags_for_files(con, [r["id"] for r in rows])
    with open(path, "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.writer(fh, delimiter=";")
        w.writerow(head)
        for r in rows:
            line = [r[c] if c in r.keys() else "" for c in cols]
            if with_tags:
                line.append(", ".join(tagmap.get(r["id"], [])))
            w.writerow(line)
    return path


def export_plan(plan, path):
    with open(path, "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.writer(fh, delimiter=";")
        w.writerow(["Type", "Action", "Disque", "Chemin / Dossier", "Nom", "Taille (octets)",
                    "Taille lisible", "Copies au total", "Disques concernés", "Empreinte"])
        for g in plan:
            t = "Dossier" if g.get("type") == "folder" else "Fichier"
            for action_label, items in [("CONSERVER", g["keep"]), ("RETIRER", g["drop"])]:
                for item in items:
                    r = dict(item) if not isinstance(item, dict) else item
                    p = r.get("folder") or r.get("rel_path", "")
                    nm = r.get("folder_name") or r.get("name", "")
                    sz = r.get("total_size") if "total_size" in r else r.get("size", 0)
                    vol_name = r.get("volume_name", "?")
                    w.writerow([t, action_label, vol_name, p, nm,
                                sz, human_size(sz), g["copies"], g["volumes"], g.get("hash", "")])
    return path


def reveal(path):
    if not os.path.exists(path):
        return False
    try:
        if sys.platform == "darwin":
            subprocess.Popen(["open", "-R", path])
        elif os.name == "nt":
            subprocess.Popen(["explorer", "/select,", os.path.normpath(path)])
        else:
            subprocess.Popen(["xdg-open", os.path.dirname(path)])
        return True
    except Exception:
        return False


def full_path_of(con, row, online=None):
    """Chemin complet, résolu sur le point de montage actuel si le disque est branché."""
    rel = ""
    try:
        rel = row["rel_path"]
    except Exception:
        try:
            rel = row["folder"]
        except Exception:
            rel = ""
    if online and row["volume_id"] in online and online[row["volume_id"]]:
        return os.path.join(online[row["volume_id"]], rel)
    vol = con.execute("SELECT * FROM volumes WHERE id=?", (row["volume_id"],)).fetchone()
    if vol is None:
        return rel
    base = volume_online_path(con, vol) or vol["last_path"] or ""
    return os.path.join(base, rel)


# ---------------------------------------------------------------------------
# Recherches sauvegardées et collections intelligentes
# ---------------------------------------------------------------------------

def save_search_query(con, name, query_dict, is_smart_collection=0):
    """Sauvegarde les paramètres d'une recherche."""
    q_json = json.dumps(query_dict, ensure_ascii=False)
    con.execute("""
        INSERT INTO saved_searches (name, query_json, is_smart_collection)
        VALUES (?, ?, ?)
        ON CONFLICT(name) DO UPDATE SET query_json=excluded.query_json, is_smart_collection=excluded.is_smart_collection
    """, (name, q_json, is_smart_collection))
    con.commit()


def get_saved_searches(con):
    """Récupère la liste de toutes les recherches sauvegardées."""
    try:
        rows = con.execute("SELECT id, name, query_json, created_at, is_smart_collection FROM saved_searches ORDER BY name ASC").fetchall()
        result = []
        for r in rows:
            try:
                q = json.loads(r["query_json"])
            except Exception:
                q = {}
            result.append({
                "id": r["id"],
                "name": r["name"],
                "query": q,
                "created_at": r["created_at"],
                "is_smart_collection": bool(r["is_smart_collection"])
            })
        return result
    except Exception:
        return []


def delete_saved_search(con, name_or_id):
    """Supprime une recherche sauvegardée par son nom ou son ID."""
    if isinstance(name_or_id, int):
        con.execute("DELETE FROM saved_searches WHERE id=?", (name_or_id,))
    else:
        con.execute("DELETE FROM saved_searches WHERE name=?", (name_or_id,))
    con.commit()

