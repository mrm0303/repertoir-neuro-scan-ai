import concurrent.futures
import os, time, json, threading
from datetime import datetime
from .config import *
from .utils import *
from .db import *

def generate_html_snapshot(con, vol_id, vol_name, out_path, stats=None):
    rows = con.execute("SELECT rel_path, name, size, mtime, category, ext FROM files WHERE volume_id = ?", (vol_id,)).fetchall()
    tree = {"_is_dir": True, "_children": {}, "name": vol_name}
    for r in rows:
        parts = r["rel_path"].replace('\\', '/').split('/')
        curr = tree
        for part in parts[:-1]:
            if part not in curr["_children"]:
                curr["_children"][part] = {"_is_dir": True, "_children": {}, "name": part}
            curr = curr["_children"][part]
        curr["_children"][parts[-1]] = {
            "_is_dir": False,
            "name": r["name"],
            "size": r["size"],
            "mtime": r["mtime"],
            "category": r["category"],
            "ext": r["ext"]
        }
    def compute_dir_stats(node):
        if not node["_is_dir"]: return node["size"] or 0, node["mtime"] or 0
        total_size = 0
        latest_mtime = 0
        for k, v in node["_children"].items():
            sz, mt = compute_dir_stats(v)
            total_size += sz
            if mt and mt > latest_mtime: latest_mtime = mt
        node["size"] = total_size
        node["mtime"] = latest_mtime
        return total_size, latest_mtime
    compute_dir_stats(tree)
    def render_node(node, level=0):
        mtime_str = dt.datetime.fromtimestamp(node["mtime"]).strftime("%d %b %Y à %H:%M") if node.get("mtime") else "--"
        size_str = human_size_local(node.get("size"))
        if node["_is_dir"]:
            kind_str = "Dossier"
            icon = "📁"
            children_html = "".join(render_node(c, level + 1) for c in sorted(node["_children"].values(), key=lambda x: (not x["_is_dir"], x["name"].lower())))
            row = f'''
            <div class="row dir-row" onclick="toggleDir(this)">
                <div class="cell name" style="padding-left: {level * 20 + 5}px;">
                    <span class="chevron">▼</span> <span class="icon">{icon}</span> {node["name"]}
                </div>
                <div class="cell date">{mtime_str}</div>
                <div class="cell size">{size_str}</div>
                <div class="cell kind">{kind_str}</div>
            </div>
            <div class="children">{children_html}</div>
            '''
            return row
        else:
            cat = node.get("category", "")
            ext = str(node.get("ext", "")).upper()
            kind_str = f"{cat.capitalize()} {ext}" if ext else "Fichier"
            icon = "📄"
            if cat == "video": icon = "🎞️"
            elif cat == "image": icon = "🖼️"
            elif cat == "audio": icon = "🎵"
            elif cat == "projet": icon = "🎬"
            return f'''
            <div class="row file-row">
                <div class="cell name" style="padding-left: {level * 20 + 25}px;">
                    <span class="icon">{icon}</span> {node["name"]}
                </div>
                <div class="cell date">{mtime_str}</div>
                <div class="cell size">{size_str}</div>
                <div class="cell kind">{kind_str}</div>
            </div>
            '''
    stats_html = ""
    if stats:
        n = stats.get("n_files", 0)
        reused = stats.get("reused", 0)
        sys_skip = stats.get("system_skipped", 0)
        err = stats.get("errors", 0)
        new_f = n - reused
        stats_html = f'''
        <div style="background: #e3f2fd; padding: 10px 15px; margin-bottom: 10px; border-radius: 6px; font-size: 13px;">
            <strong>Rapport d'analyse :</strong> {n} fichiers au total.<br>
            • Nouvelles données (nouveaux ou modifiés) : <b>{new_f}</b> fichiers.<br>
            • Données inchangées (identiques) : <b>{reused}</b> fichiers.<br>
            • Erreurs de lecture : <b>{err}</b>.<br>
            • Dossiers système ignorés : <b>{sys_skip}</b> (non analysés pour protéger le système).
        </div>
        '''

    html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Snapshot : {vol_name}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; font-size: 13px; color: #333; margin: 0; padding: 20px; background: #f5f5f7; }}
        .window {{ background: #fff; border-radius: 10px; box-shadow: 0 10px 30px rgba(0,0,0,0.15); overflow: hidden; border: 1px solid #d1d1d1; max-width: 1200px; margin: 0 auto; }}
        .header {{ background: #f0f0f0; border-bottom: 1px solid #d1d1d1; padding: 10px 20px; font-weight: 600; text-align: center; color: #444; border-radius: 10px 10px 0 0; display: flex; justify-content: space-between; align-items: center;}}
        .header .dots {{ display: flex; gap: 8px; }}
        .header .dot {{ width: 12px; height: 12px; border-radius: 50%; }}
        .header .dot.red {{ background: #ff5f56; }}
        .header .dot.yellow {{ background: #ffbd2e; }}
        .header .dot.green {{ background: #27c93f; }}
        .table-header {{ display: flex; border-bottom: 1px solid #e0e0e0; background: #fafafa; font-weight: bold; color: #888; font-size: 12px; }}
        .row {{ display: flex; border-bottom: 1px solid #f0f0f0; padding: 4px 0; cursor: default; }}
        .row:hover {{ background: #f0f4ff; }}
        .dir-row {{ cursor: pointer; }}
        .cell {{ padding: 2px 10px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
        .cell.name {{ flex: 5; font-weight: 500; display: flex; align-items: center; }}
        .cell.date {{ flex: 2; color: #666; }}
        .cell.size {{ flex: 1; text-align: right; color: #666; }}
        .cell.kind {{ flex: 2; color: #666; padding-left: 20px; }}
        .chevron {{ display: inline-block; width: 15px; font-size: 10px; color: #999; transition: transform 0.1s; }}
        .children.collapsed {{ display: none; }}
        .dir-row.collapsed .chevron {{ transform: rotate(-90deg); }}
        .icon {{ margin-right: 6px; font-size: 14px; }}
    </style>
</head>
<body>
    <div class="window">
        <div class="header">
            <div class="dots"><div class="dot red"></div><div class="dot yellow"></div><div class="dot green"></div></div>
            <div>{vol_name}</div>
            <div style="width: 52px;"></div>
        </div>
        {stats_html}
        <div class="table-header">
            <div class="cell name" style="padding-left: 30px;">Nom</div>
            <div class="cell date">Date de modification</div>
            <div class="cell size">Taille</div>
            <div class="cell kind">Type</div>
        </div>
        <div class="tree-container">
            {render_node(tree, 0)}
        </div>
    </div>
    <script>
        function toggleDir(el) {{
            el.classList.toggle('collapsed');
            let children = el.nextElementSibling;
            if (children && children.classList.contains('children')) {{
                children.classList.toggle('collapsed');
            }}
        }}
    </script>
</body>
</html>'''
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)


class Scanner:
    def __init__(self, con, progress=None, cancel_event=None, pause_event=None):
        self.con = con
        self.progress = progress or (lambda kind, payload: None)
        self.cancel = cancel_event or threading.Event()
        self.pause_event = pause_event or threading.Event()
        self.stats = {"system_skipped": 0, "n_files": 0, "total_size": 0, "reused": 0, "errors": 0}

    def log(self, msg):
        self.progress("log", msg)

    # -- pré-comptage : permet d'afficher un pourcentage et un temps restant --
    def precount(self, root, skip_system=True):
        walk_root = os.path.abspath(root)
        if os.name == "nt" and not walk_root.startswith("\\\\?\\"):
            walk_root = "\\\\?\\" + walk_root
        n = 0
        try:
            root_dev = os.stat(walk_root).st_dev
        except OSError:
            root_dev = None
        seen_dirs = set()
        for dirpath, dirnames, filenames in os.walk(walk_root, onerror=lambda e: None):
            while self.pause_event.is_set():
                if self.cancel.is_set(): break
                time.sleep(0.2)
            if self.cancel.is_set():
                break
            prune_dirs(dirpath, dirnames, filenames, root_dev, skip_system, seen_dirs, walk_root, self.stats)
            n += len(filenames)
            if n % 5000 < len(filenames):
                self.progress("precount", n)
        return n

    def scan(self, root, volume_name, do_hash=True, do_meta=True,
             min_hash_size=1024, note="", do_precount=True, incremental=True,
             skip_system=True, do_thumbs=False):
        original_root = os.path.abspath(root)
        ok, resolved_root, err_kind, err_msg = check_directory_access(original_root)
        if not ok:
            raise ValueError(f"Accès impossible au dossier '{original_root}' : {err_msg}")
        walk_root = resolved_root
        if os.name == "nt" and not walk_root.startswith("\\\\?\\"):
            walk_root = "\\\\?\\" + walk_root

        t0 = time.time()
        serial = volume_serial(original_root)
        cur = self.con.cursor()
        cur.execute("SELECT id, serial FROM volumes WHERE name = ?", (volume_name,))
        row = cur.fetchone()
        
        # Prévenir l'écrasement si deux disques PHYSIQUEMENT DIFFÉRENTS ont le même nom
        if row and row["serial"] and serial and row["serial"] != serial:
            base_name = volume_name
            counter = 2
            while row:
                volume_name = f"{base_name} ({counter})"
                cur.execute("SELECT id, serial FROM volumes WHERE name = ?", (volume_name,))
                row = cur.fetchone()
                counter += 1
            self.log(f"⚠️ Le nom '{base_name}' est déjà pris par un autre disque. Renommé en '{volume_name}'.")
            row = None # Traiter comme un nouveau disque
            
        previous = {}
        if row:
            vol_id = row["id"]
            if incremental:
                for r in self.con.execute(
                        """SELECT id, rel_path, size, mtime, quick_hash, camera, lens, duration,
                                  width, height, fps, codec, shot_date, meta
                           FROM files WHERE volume_id=?""", (vol_id,)):
                    key = unicodedata.normalize('NFC', r["rel_path"]).replace('\\', '/').lower()
                    previous[key] = r
                if previous:
                    self.log(f"Disque déjà catalogué : {human_count(len(previous))} fiches "
                             "réutilisables si les fichiers n'ont pas changé.")
            cur.execute("UPDATE volumes SET serial=?, last_path=?, "
                        "note=COALESCE(NULLIF(?,''), note) WHERE id=?",
                        (serial, original_root, note, vol_id))
        else:
            cur.execute("INSERT INTO volumes (name, serial, last_path, note) VALUES (?,?,?,?)",
                        (volume_name, serial, original_root, note))
            vol_id = cur.lastrowid
        # Frontière entre l'ancien inventaire et le nouveau : l'ancien n'est retiré
        # qu'une fois le nouveau écrit. Le catalogue reste donc interrogeable pendant
        # toute l'analyse, et une interruption ou une coupure ne détruit rien.
        generation_mark = self.con.execute(
            "SELECT COALESCE(MAX(id),0) m FROM files").fetchone()["m"]
        self.con.commit()

        total_expected = 0
        if do_precount:
            self.log("Lecture de l'arborescence…")
            total_expected = self.precount(original_root, skip_system)
            self.log(f"{human_count(total_expected)} fichiers repérés. Analyse en cours…")

        self.progress("start", {"total": total_expected, "t0": t0})
        tag_cache = TagCache(self.con)
        batch, media_batch = [], []
        n_files = total_size = reused = skipped_links = 0
        last_tick = 0.0
        try:
            root_dev = os.stat(walk_root).st_dev
        except OSError:
            root_dev = None
        seen_dirs, seen_files = set(), set()
        seen_keys = set()
        deleted_old_ids = []

        for dirpath, dirnames, filenames in os.walk(walk_root, onerror=lambda e: None):
            while self.pause_event.is_set():
                if self.cancel.is_set(): break
                time.sleep(0.2)
            if self.cancel.is_set():
                break
            prune_dirs(dirpath, dirnames, filenames, root_dev, skip_system, seen_dirs, walk_root, self.stats)
            for fname in filenames:
                while self.pause_event.is_set():
                    if self.cancel.is_set(): break
                    time.sleep(0.2)
                if self.cancel.is_set():
                    break
                if fname in SKIP_FILES:
                    continue
                full = os.path.join(dirpath, fname)
                try:
                    st = os.stat(full, follow_symlinks=False)
                    is_dir = os.path.isdir(full)
                    if not os.path.isfile(full) and not is_dir:
                        continue
                    if is_dir:
                        ext = os.path.splitext(fname)[1].lstrip(".").lower()
                        from catalogue_app.config import BUNDLE_EXT
                        if ext not in BUNDLE_EXT:
                            continue
                except OSError:
                    continue
                # Un même fichier atteint par deux chemins (lien physique)
                # ne doit être compté qu'une fois. On vérifie st_nlink pour
                # éviter de filtrer par erreur sur des inodes constants (NTFS/FAT).
                if getattr(st, "st_ino", 0) and getattr(st, "st_nlink", 1) > 1:
                    inode_key = (st.st_dev, st.st_ino)
                    if inode_key in seen_files:
                        skipped_links += 1
                        continue
                    seen_files.add(inode_key)

                try:
                    ext = os.path.splitext(fname)[1].lstrip(".").lower()
                    cat = classify(ext)
                    size = st.st_size
                    if is_dir:
                        # Compute true size of the bundle
                        try:
                            for dp, dn, fn in os.walk(full):
                                for f in fn:
                                    size += os.path.getsize(os.path.join(dp, f))
                        except: pass
                    rel = os.path.relpath(full, walk_root)
                    key = unicodedata.normalize('NFC', rel).replace('\\', '/').lower()
                    old = previous.get(key)
                    same = bool(old and old["size"] == size
                                and abs((old["mtime"] or 0) - st.st_mtime) < 2)
                    seen_keys.add(key)
                    
                    if same:
                        reused += 1
                        n_files += 1
                        total_size += size
                        # Skip if quick_hash isn't missing
                        if do_hash and not old["quick_hash"] and size >= min_hash_size:
                            rec = {
                                "volume_id": vol_id, "rel_path": rel, "folder": os.path.dirname(rel),
                                "name": fname, "name_lower": fname.lower(),
                                "name_norm": normalize(fname), "path_norm": normalize(rel),
                                "ext": ext, "category": cat, "size": size, "mtime": st.st_mtime,
                                "quick_hash": quick_hash(full, size), "app": PROJECT_EXT.get(ext),
                                "camera": old.get("camera"), "lens": old.get("lens"), "duration": old.get("duration"), "width": old.get("width"),
                                "height": old.get("height"), "fps": old.get("fps"), "codec": old.get("codec"), "shot_date": old.get("shot_date"),
                                "meta": old.get("meta"), "_full": full,
                            }
                            deleted_old_ids.append(old["id"])
                            batch.append(rec)
                        continue
                        
                    rec = {
                        "volume_id": vol_id, "rel_path": rel, "folder": os.path.dirname(rel),
                        "name": fname, "name_lower": fname.lower(),
                        "name_norm": normalize(fname), "path_norm": normalize(rel),
                        "ext": ext, "category": cat, "size": size, "mtime": st.st_mtime,
                        "quick_hash": "", "app": PROJECT_EXT.get(ext),
                        "camera": None, "lens": None, "duration": None, "width": None,
                        "height": None, "fps": None, "codec": None, "shot_date": None,
                        "meta": None, "_full": full,
                    }
    
                    if do_hash and size >= min_hash_size:
                        rec["quick_hash"] = quick_hash(full, size)
                    if do_meta and cat in MEDIA_CATEGORIES:
                        media_batch.append(rec)
                    
                    if old:
                        deleted_old_ids.append(old["id"])

                    batch.append(rec)
                    n_files += 1
                    total_size += size
    
                    if len(media_batch) >= 40:
                        self._enrich(media_batch, do_thumbs)
                        media_batch = []
                except Exception as e:
                    self.stats["errors"] += 1
                    self.log(f"Erreur inattendue sur {fname}: {e}")
                if len(batch) >= 400:
                    if media_batch:
                        self._enrich(media_batch, do_thumbs)
                        media_batch = []
                    self._flush(batch, tag_cache)
                    batch = []

                now = time.time()
                if now - last_tick > 0.4:
                    last_tick = now
                    self.progress("tick", {
                        "n": n_files, "size": total_size, "total": total_expected,
                        "elapsed": now - t0, "reused": reused,
                        "current": os.path.basename(dirpath),
                    })

        if media_batch:
            self._enrich(media_batch, do_thumbs)
        if batch:
            self._flush(batch, tag_cache)

        # Retrait de l'ancienne génération, maintenant que la nouvelle est en base.
        if deleted_old_ids:
            for i in range(0, len(deleted_old_ids), 900):
                chunk = deleted_old_ids[i:i+900]
                cur.execute(f"DELETE FROM files WHERE id IN ({','.join('?'*len(chunk))})", chunk)
                
        if not self.cancel.is_set():
            missing_ids = [old["id"] for k, old in previous.items() if k not in seen_keys]
            if missing_ids:
                for i in range(0, len(missing_ids), 900):
                    chunk = missing_ids[i:i+900]
                    cur.execute(f"DELETE FROM files WHERE id IN ({','.join('?'*len(chunk))})", chunk)
            kept_n, kept_s = n_files, total_size
        else:
            agg = self.con.execute(
                "SELECT COUNT(*) n, COALESCE(SUM(size),0) s FROM files WHERE volume_id=?",
                (vol_id,)).fetchone()
            kept_n, kept_s = agg["n"], agg["s"]
        cur.execute("UPDATE volumes SET scanned_at=?, file_count=?, total_size=? WHERE id=?",
                    (datetime.now().isoformat(timespec="seconds"), kept_n, kept_s, vol_id))
        self.con.commit()
        elapsed = time.time() - t0
        state = "interrompue" if self.cancel.is_set() else "terminée"
        self.log(f"Analyse {state} : {human_count(n_files)} fichiers, "
                 f"{human_size(total_size)}, en {human_clock(elapsed)}"
                 + (f" ({human_count(reused)} fiches réutilisées)." if reused else "."))
        if skipped_links:
            self.log(f"{human_count(skipped_links)} fichier(s) atteints par plusieurs "
                     "chemins n'ont été comptés qu'une fois (liens physiques ou "
                     "dossiers miroirs du système).")
        self.progress("tick", {"n": n_files, "size": total_size, "total": n_files,
                               "elapsed": elapsed, "reused": reused, "current": ""})

        if not self.cancel.is_set():
            snap_dir = os.path.join(APP_DIR, "Snapshots")
            os.makedirs(snap_dir, exist_ok=True)
            snap_file = os.path.join(snap_dir, f"snapshot_{volume_name}.html")
            try:
                self.stats["n_files"] = n_files
                self.stats["total_size"] = total_size
                self.stats["reused"] = reused
                generate_html_snapshot(self.con, vol_id, volume_name, snap_file, self.stats)
                self.log(f"Capture de l'arborescence (façon Finder) enregistrée dans {snap_file}")
                try:
                    from .dashboard import generate_sunburst
                    dash_file = generate_sunburst(self.con, vol_id, volume_name)
                    self.log(f"Graphique de stockage interactif disponible dans {dash_file}")
                except Exception as de:
                    self.log(f"Erreur graphique: {de}")
            except Exception as e:
                self.log(f"Erreur lors de la création du snapshot : {e}")

        return n_files, total_size, elapsed

    def _enrich(self, records, do_thumbs=False):
        paths = [r["_full"] for r in records]
        meta = exiftool_batch(paths) if EXIFTOOL else {}
        
        # Parallélisation multi-cœurs de ffprobe (ThreadPoolExecutor) pour les médias non traités par exiftool
        if FFPROBE:
            probe_candidates = [
                r for r in records 
                if meta.get(os.path.normpath(r["_full"])) is None and r["category"] in ("video", "audio")
            ]
            if probe_candidates:
                workers = min(os.cpu_count() or 4, 8)
                with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
                    future_map = {executor.submit(ffprobe_one, r["_full"]): r for r in probe_candidates}
                    for fut in concurrent.futures.as_completed(future_map):
                        rec = future_map[fut]
                        try:
                            res = fut.result()
                            if res:
                                meta[os.path.normpath(rec["_full"])] = res
                        except Exception:
                            pass

        for r in records:
            m = meta.get(os.path.normpath(r["_full"]))
            if not m:
                continue
            for key in ("camera", "lens", "duration", "width", "height", "fps", "codec", "shot_date"):
                if m.get(key) not in (None, ""):
                    r[key] = m[key]
            if m.get("extra"):
                r["meta"] = json.dumps(m["extra"], ensure_ascii=False)
                
        # AI Embedding
        if do_thumbs:
            try:
                from ai_search import HAS_AI, encode_image, serialize_vector
                if HAS_AI:
                    import subprocess
                    for r in records:
                        path = r["_full"]
                        vec = None
                        if r["category"] == "image":
                            vec = encode_image(path)
                        elif r["category"] == "video":
                            out = "/tmp/ai_thumb.jpg"
                            if os.path.exists(out): os.remove(out)
                            try:
                                subprocess.run(["ffmpeg", "-y", "-ss", "00:00:01", "-i", path, "-vframes", "1", "-q:v", "2", out], 
                                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5)
                                if os.path.exists(out):
                                    vec = encode_image(out)
                            except:
                                pass
                        
                        if vec is not None:
                            r["embedding"] = serialize_vector(vec)
            except Exception as e:
                self.log(f"Erreur AI embedding: {e}")

    def _flush(self, records, tag_cache):
        cols = ("volume_id", "rel_path", "folder", "name", "name_lower", "name_norm",
                "path_norm", "ext", "category", "size", "mtime", "quick_hash", "app",
                "camera", "lens", "duration", "width", "height", "fps", "codec",
                "shot_date", "meta")
        max_before = self.con.execute("SELECT COALESCE(MAX(id),0) m FROM files").fetchone()["m"]
        rows = []
        for r in records:
            rows.append(tuple(json.dumps(r.get(c), ensure_ascii=False)
                              if isinstance(r.get(c), (dict, list)) else r.get(c) for c in cols))
        self.con.executemany(
            f"INSERT INTO files ({','.join(cols)}) VALUES ({','.join('?' * len(cols))})", rows)

        ids = {r["rel_path"]: r["id"] for r in self.con.execute(
            "SELECT id, rel_path FROM files WHERE id > ?", (max_before,))}
        pairs = []
        for r in records:
            fid = ids.get(r["rel_path"])
            if not fid:
                continue
            for name, kind in derive_tags(r):
                pairs.append((fid, tag_cache.id_for(name, kind)))
        if pairs:
            self.con.executemany("INSERT OR IGNORE INTO file_tags VALUES (?,?)", pairs)
            
        embeddings = []
        for r in records:
            fid = ids.get(r["rel_path"])
            if not fid: continue
            if r.get("embedding"):
                embeddings.append((fid, r["embedding"]))
        if embeddings:
            self.con.executemany("INSERT OR REPLACE INTO file_embeddings (file_id, embedding) VALUES (?,?)", embeddings)
            
        self.con.commit()


# ---------------------------------------------------------------------------
# Recherche
# ---------------------------------------------------------------------------

