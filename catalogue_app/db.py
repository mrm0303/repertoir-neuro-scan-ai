import os, sqlite3, json, shutil, time, subprocess
from datetime import datetime
from glob import glob
from .config import *
from .utils import *

SCHEMA = """
CREATE TABLE IF NOT EXISTS volumes (
    id INTEGER PRIMARY KEY, name TEXT UNIQUE NOT NULL, serial TEXT,
    last_path TEXT, scanned_at TEXT, file_count INTEGER DEFAULT 0,
    total_size INTEGER DEFAULT 0, note TEXT DEFAULT '', priority INTEGER DEFAULT 0
);
CREATE TABLE IF NOT EXISTS files (
    id INTEGER PRIMARY KEY,
    volume_id INTEGER NOT NULL REFERENCES volumes(id) ON DELETE CASCADE,
    rel_path TEXT NOT NULL, folder TEXT, name TEXT, name_lower TEXT, name_norm TEXT,
    path_norm TEXT, ext TEXT, category TEXT, size INTEGER, mtime REAL,
    quick_hash TEXT, app TEXT, camera TEXT, lens TEXT, duration REAL,
    width INTEGER, height INTEGER, fps REAL, codec TEXT, shot_date TEXT, meta TEXT
);
CREATE TABLE IF NOT EXISTS file_embeddings (
        file_id INTEGER PRIMARY KEY,
        embedding BLOB
    );
    CREATE TABLE IF NOT EXISTS tags (
    id INTEGER PRIMARY KEY, name TEXT NOT NULL, kind TEXT NOT NULL DEFAULT 'auto',
    UNIQUE(name, kind)
);
CREATE TABLE IF NOT EXISTS file_tags (
    file_id INTEGER NOT NULL REFERENCES files(id) ON DELETE CASCADE,
    tag_id  INTEGER NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY (file_id, tag_id)
);
CREATE TABLE IF NOT EXISTS saved_searches (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    query_json TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    is_smart_collection INTEGER DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_files_volume ON files(volume_id);
CREATE INDEX IF NOT EXISTS idx_files_name   ON files(name_norm);
CREATE INDEX IF NOT EXISTS idx_files_hash   ON files(quick_hash);
CREATE INDEX IF NOT EXISTS idx_files_hash_size ON files(quick_hash, size);
CREATE INDEX IF NOT EXISTS idx_files_vol_folder ON files(volume_id, folder);
CREATE INDEX IF NOT EXISTS idx_files_cat    ON files(category);
CREATE INDEX IF NOT EXISTS idx_files_camera ON files(camera);
CREATE INDEX IF NOT EXISTS idx_files_size   ON files(size);
CREATE INDEX IF NOT EXISTS idx_ft_tag       ON file_tags(tag_id);
CREATE INDEX IF NOT EXISTS idx_ft_file      ON file_tags(file_id);
"""


def _columns(con, table):
    return {r["name"] for r in con.execute(f"PRAGMA table_info({table})")}



def setup_fts5(con):
    """Initialise ou met à jour la table d'indexation plein texte SQLite FTS5."""
    try:
        # Vérifier si la table FTS5 existe déjà
        has_fts = con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='files_fts'").fetchone()
        if not has_fts:
            con.execute("""
                CREATE VIRTUAL TABLE files_fts USING fts5(
                    name, folder, camera, meta,
                    content='files',
                    content_rowid='id',
                    tokenize='unicode61 remove_diacritics 2'
                );
            """)
            con.execute("""
                CREATE TRIGGER IF NOT EXISTS files_ai AFTER INSERT ON files BEGIN
                    INSERT INTO files_fts(rowid, name, folder, camera, meta) 
                    VALUES (new.id, new.name, new.folder, new.camera, new.meta);
                END;
            """)
            con.execute("""
                CREATE TRIGGER IF NOT EXISTS files_ad AFTER DELETE ON files BEGIN
                    INSERT INTO files_fts(files_fts, rowid, name, folder, camera, meta) 
                    VALUES('delete', old.id, old.name, old.folder, old.camera, old.meta);
                END;
            """)
            con.execute("""
                CREATE TRIGGER IF NOT EXISTS files_au AFTER UPDATE ON files BEGIN
                    INSERT INTO files_fts(files_fts, rowid, name, folder, camera, meta) 
                    VALUES('delete', old.id, old.name, old.folder, old.camera, old.meta);
                    INSERT INTO files_fts(rowid, name, folder, camera, meta) 
                    VALUES (new.id, new.name, new.folder, new.camera, new.meta);
                END;
            """)
            # Reconstruction initiale de l'index
            con.execute("INSERT INTO files_fts(files_fts) VALUES('rebuild');")
            con.commit()
    except Exception as e:
        print(f"Avertissement configuration FTS5: {e}")


def migrate(con):
    setup_fts5(con)
    con.execute("CREATE INDEX IF NOT EXISTS idx_files_hash_size ON files(quick_hash, size)")
    con.execute("CREATE INDEX IF NOT EXISTS idx_files_vol_folder ON files(volume_id, folder)")
    cols = _columns(con, "volumes")
    if "priority" not in cols:
        con.execute("ALTER TABLE volumes ADD COLUMN priority INTEGER DEFAULT 0")
    
    cols = _columns(con, "files")
    changed = False
    for name, decl in (("name_norm", "TEXT"), ("path_norm", "TEXT"), ("global_cat", "TEXT")):
        if name not in cols:
            con.execute(f"ALTER TABLE files ADD COLUMN {name} {decl}")
            changed = True
    con.commit()
    if changed or con.execute(
            "SELECT COUNT(*) c FROM files WHERE name_norm IS NULL").fetchone()["c"]:
        rows = con.execute(
            "SELECT id, name, rel_path FROM files WHERE name_norm IS NULL").fetchall()
        if rows:
            con.executemany(
                "UPDATE files SET name_norm=?, path_norm=? WHERE id=?",
                [(normalize(r["name"]), normalize(r["rel_path"]), r["id"]) for r in rows])
            con.commit()



def backup_database():
    import gzip
    if not os.path.exists(DB_PATH):
        return
    backup_dir = os.path.join(APP_DIR, "Backups")
    os.makedirs(backup_dir, exist_ok=True)
    
    # Ne faire qu'une seule sauvegarde automatique par jour pour éviter de saturer le disque
    today = datetime.now().strftime("%Y%m%d")
    existing_today = glob(os.path.join(backup_dir, f"catalogue_{today}_*.db.gz"))
    if existing_today:
        return
        
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = os.path.join(backup_dir, f"catalogue_{timestamp}.db.gz")
    
    try:
        # Compresser en streaming pour économiser l'espace disque (réduit 5.4Go à ~1Go)
        with open(DB_PATH, "rb") as f_in:
            with gzip.open(backup_file, "wb", compresslevel=6) as f_out:
                shutil.copyfileobj(f_in, f_out, length=1024 * 1024)
    except Exception as e:
        print(f"Erreur de sauvegarde: {e}")
        return

    # Retain last 5 backups (au lieu de 10)
    backups = sorted(glob(os.path.join(backup_dir, "catalogue_*.db.gz")))
    if len(backups) > 5:
        for old in backups[:-5]:
            try:
                os.remove(old)
            except OSError:
                pass

def connect(db_path: str = DB_PATH) -> sqlite3.Connection:
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    con = sqlite3.connect(db_path, check_same_thread=False)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    con.execute("PRAGMA journal_mode = WAL")
    con.execute("PRAGMA synchronous = NORMAL")
    con.execute("PRAGMA cache_size = -64000")
    con.execute("PRAGMA busy_timeout = 60000")  # analyses simultanees : attendre au lieu d echouer
    con.executescript(SCHEMA)
    con.commit()
    migrate(con)
    return con


# ---------------------------------------------------------------------------
# Identification des disques
# ---------------------------------------------------------------------------

def volume_serial(path: str):
    if os.name == "nt":
        try:
            import ctypes
            root = os.path.splitdrive(os.path.abspath(path))[0] + "\\"
            buf = ctypes.create_unicode_buffer(1024)
            serial = ctypes.c_ulong(0)
            if ctypes.windll.kernel32.GetVolumeInformationW(
                    ctypes.c_wchar_p(root), buf, 1024,
                    ctypes.byref(serial), None, None, None, 0):
                return f"{serial.value:08X}"
        except Exception:
            pass
    elif sys.platform == "darwin":
        try:
            # import subprocess
            # res = subprocess.run(["diskutil", "info", path], capture_output=True, text=True, timeout=2)
            # for line in res.stdout.splitlines():
            #     if "Volume UUID:" in line:
            #         return line.split(":", 1)[1].strip()
            return None # TEMPORARILY DISABLED TO PREVENT CRASH
        except Exception:
            pass
    return None


def suggest_volume_name(path: str) -> str:
    path = os.path.abspath(path)
    if os.name == "nt":
        drive = os.path.splitdrive(path)[0]
        try:
            import ctypes
            buf = ctypes.create_unicode_buffer(1024)
            ctypes.windll.kernel32.GetVolumeInformationW(
                ctypes.c_wchar_p(drive + "\\"), buf, 1024, None, None, None, None, 0)
            if buf.value:
                return f"{buf.value} ({drive})"
        except Exception:
            pass
        return drive or path
    parts = path.rstrip(os.sep).split(os.sep)
    if len(parts) >= 3 and parts[1] == "Volumes":
        return parts[2]
    if len(parts) >= 4 and parts[1] == "media":
        return parts[3]
    return os.path.basename(path.rstrip(os.sep)) or path


def list_mounted_volumes():
    vols = []
    if os.name == "nt":
        import string
        for letter in string.ascii_uppercase:
            root = f"{letter}:\\"
            if os.path.exists(root):
                vols.append(root)
    else:
        for base in ("/Volumes", "/media/" + os.environ.get("USER", ""), "/mnt"):
            if os.path.isdir(base):
                try:
                    for entry in sorted(os.listdir(base)):
                        full = os.path.join(base, entry)
                        if os.path.isdir(full) and not entry.startswith("."):
                            vols.append(full)
                except PermissionError:
                    pass
    return vols


# ---------------------------------------------------------------------------
# Empreintes
# ---------------------------------------------------------------------------

def quick_hash(path: str, size: int, chunk: int = 512 * 1024) -> str:
    import hashlib
    h = hashlib.sha1()
    h.update(str(size).encode())
    try:
        with open(path, "rb") as f:
            h.update(f.read(chunk))
            if size > chunk * 2:
                f.seek(-chunk, os.SEEK_END)
                h.update(f.read(chunk))
    except (OSError, ValueError):
        return ""
    return h.hexdigest()


def full_hash(path: str) -> str:
    """Empreinte complète — pour vérifier un groupe de doublons avant suppression."""
    import hashlib
    h = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            for block in iter(lambda: f.read(4 * 1024 * 1024), b""):
                h.update(block)
    except OSError:
        return ""
    return h.hexdigest()


# ---------------------------------------------------------------------------
# Métadonnées
# ---------------------------------------------------------------------------

EXIFTOOL = shutil.which("exiftool")
FFPROBE = shutil.which("ffprobe")

EXIF_TAGS = [
    "-Make", "-Model", "-LensModel", "-LensID", "-ISO", "-FocalLength",
    "-DateTimeOriginal", "-CreateDate", "-MediaCreateDate",
    "-Duration", "-MediaDuration", "-TrackDuration",
    "-ImageWidth", "-ImageHeight", "-VideoFrameRate", "-FrameRate",
    "-CompressorName", "-CompressorID", "-VideoCodec", "-AudioFormat",
    "-FileType", "-SampleRate", "-AudioChannels", "-ColorSpace",
]


def _first(d, *keys):
    for k in keys:
        v = d.get(k)
        if v not in (None, "", 0):
            return v
    return None


def exiftool_batch(paths, timeout=240):
    if not EXIFTOOL or not paths:
        return {}
    cmd = [EXIFTOOL, "-j", "-n", "-q", "-q", "-charset", "filename=utf8"] + EXIF_TAGS + list(paths)
    try:
        out = subprocess.run(cmd, capture_output=True, timeout=timeout,
                             stdin=subprocess.DEVNULL).stdout.decode("utf-8", "replace")
        data = json.loads(out) if out.strip() else []
    except Exception:
        return {}
    result = {}
    for item in data:
        src = item.get("SourceFile")
        if not src:
            continue
        w, h = _first(item, "ImageWidth"), _first(item, "ImageHeight")
        result[os.path.normpath(src)] = {
            "camera": " ".join(str(x) for x in [item.get("Make"), item.get("Model")] if x).strip() or None,
            "lens": _first(item, "LensModel", "LensID"),
            "duration": _first(item, "MediaDuration", "Duration", "TrackDuration"),
            "width": int(w) if isinstance(w, (int, float)) else None,
            "height": int(h) if isinstance(h, (int, float)) else None,
            "fps": _first(item, "VideoFrameRate", "FrameRate"),
            "codec": _first(item, "CompressorName", "VideoCodec", "CompressorID",
                            "AudioFormat", "FileType"),
            "shot_date": _first(item, "DateTimeOriginal", "MediaCreateDate", "CreateDate"),
            "extra": {k: v for k, v in item.items()
                      if k in ("ISO", "FocalLength", "SampleRate", "AudioChannels", "ColorSpace")},
        }
    return result


def ffprobe_one(path: str, timeout=60):
    if not FFPROBE:
        return None
    cmd = [FFPROBE, "-v", "quiet", "-print_format", "json", "-show_format", "-show_streams", path]
    try:
        out = subprocess.run(cmd, capture_output=True, timeout=timeout,
                             stdin=subprocess.DEVNULL).stdout.decode("utf-8", "replace")
        data = json.loads(out) if out.strip() else {}
    except Exception:
        return None
    if not data:
        return None
    fmt = data.get("format", {}) or {}
    tags = {k.lower(): v for k, v in (fmt.get("tags") or {}).items()}
    vs = next((s for s in data.get("streams", []) if s.get("codec_type") == "video"), None)
    as_ = next((s for s in data.get("streams", []) if s.get("codec_type") == "audio"), None)
    fps = None
    if vs and vs.get("r_frame_rate") and "/" in vs["r_frame_rate"]:
        try:
            num, den = vs["r_frame_rate"].split("/")
            fps = round(float(num) / float(den), 3) if float(den) else None
        except (ValueError, ZeroDivisionError):
            fps = None
    return {
        "camera": tags.get("com.apple.quicktime.model") or tags.get("model") or tags.get("make"),
        "lens": tags.get("com.apple.quicktime.camera.lens_model"),
        "duration": float(fmt["duration"]) if fmt.get("duration") else None,
        "width": vs.get("width") if vs else None,
        "height": vs.get("height") if vs else None,
        "fps": fps,
        "codec": (vs or as_ or {}).get("codec_name"),
        "shot_date": tags.get("creation_time"),
        "extra": {"bitrate": fmt.get("bit_rate")} if fmt.get("bit_rate") else {},
    }


def tools_status() -> str:
    parts = ["exiftool : " + ("détecté ✓" if EXIFTOOL else "absent ✗"),
             "ffprobe : " + ("détecté ✓" if FFPROBE else "absent ✗")]
    if not EXIFTOOL and not FFPROBE:
        parts.append("(aucune métadonnée caméra ne sera extraite)")
    return "   |   ".join(parts)


# ---------------------------------------------------------------------------
# Générateur d'étiquettes
# ---------------------------------------------------------------------------

TAG_KINDS = ("type", "définition", "caméra", "marque", "codec", "cadence",
             "durée", "année", "contenu", "dossier", "manuelle", "doublon")

BRANDS = [
    ("sony", "Sony"), ("canon", "Canon"), ("nikon", "Nikon"), ("panasonic", "Panasonic"),
    ("lumix", "Panasonic"), ("fujifilm", "Fujifilm"), ("blackmagic", "Blackmagic"),
    ("red ", "RED"), ("reddigital", "RED"), ("arri", "ARRI"), ("dji", "DJI"),
    ("gopro", "GoPro"), ("apple", "Apple"), ("iphone", "iPhone"), ("samsung", "Samsung"),
    ("insta360", "Insta360"), ("leica", "Leica"), ("olympus", "Olympus"), ("sigma", "Sigma"),
]

CONTENT_KEYWORDS = {
    "rush": "rushes", "rushes": "rushes", "brut": "rushes", "raw": "rushes",
    "montage": "montage", "edit": "montage", "timeline": "montage",
    "export": "export", "master": "master", "final": "master", "livraison": "livraison",
    "diffusion": "diffusion", "broadcast": "diffusion",
    "son": "son", "audio": "son", "mix": "mixage", "mixage": "mixage",
    "musique": "musique", "music": "musique", "voix": "voix-off", "voice": "voix-off",
    "ambiance": "ambiance", "bruitage": "bruitage",
    "interview": "interview", "itw": "interview", "entretien": "interview",
    "plateau": "plateau", "studio": "studio", "reportage": "reportage",
    "photo": "photos", "photos": "photos", "image": "images", "images": "images",
    "proxy": "proxy", "preview": "cache", "previews": "cache", "cache": "cache",
    "autosave": "auto-save", "auto-save": "auto-save", "backup": "sauvegarde",
    "sauvegarde": "sauvegarde", "archive": "archive", "archives": "archive",
    "graphisme": "graphisme", "generique": "générique", "titre": "titres",
    "titres": "titres", "sous-titre": "sous-titres", "subtitle": "sous-titres",
    "etalonnage": "étalonnage", "grading": "étalonnage", "color": "étalonnage",
    "drone": "drone", "gopro": "gopro", "timelapse": "timelapse",
    "doc": "documents", "admin": "administratif", "contrat": "administratif",
    "scenario": "scénario", "script": "scénario", "decoupage": "découpage",
}

GENERIC_FOLDERS = {"", "documents", "desktop", "downloads", "users", "video", "videos",
                   "movies", "images", "photos", "data", "divers", "temp", "tmp", "new folder"}


def resolution_tag(width, height):
    if not width or not height:
        return None
    long_side = max(int(width), int(height))
    if long_side >= 7000:
        return "8K"
    if long_side >= 5000:
        return "6K"
    if long_side >= 3400:
        return "4K"
    if long_side >= 2300:
        return "2.5K"
    if long_side >= 1800:
        return "HD 1080"
    if long_side >= 1200:
        return "HD 720"
    return "SD"


def cadence_tag(fps):
    try:
        f = float(fps)
    except (TypeError, ValueError):
        return None, False
    if f <= 0:
        return None, False
    for ref in (23.976, 24, 25, 29.97, 30, 48, 50, 59.94, 60, 100, 120, 180, 240):
        if abs(f - ref) < 0.6:
            label = f"{int(round(ref))}p"
            return label, ref >= 48
    return f"{f:.0f}p", f >= 48


def duration_tag(seconds):
    try:
        s = float(seconds)
    except (TypeError, ValueError):
        return None
    if s <= 0:
        return None
    if s < 30:
        return "clip court"
    if s < 300:
        return "clip moyen"
    if s < 1800:
        return "séquence longue"
    return "très long"


def codec_tag(codec, ext):
    text = normalize(f"{codec or ''} {ext or ''}")
    table = [("prores", "ProRes"), ("dnx", "DNxHD"), ("hevc", "H.265"), ("h265", "H.265"),
             ("hvc1", "H.265"), ("h264", "H.264"), ("avc", "H.264"), ("braw", "BRAW"),
             ("r3d", "REDCODE"), ("arri", "ARRIRAW"), ("mjpeg", "MJPEG"),
             ("xavc", "XAVC"), ("dv", "DV"), ("pcm", "PCM"), ("mp3", "MP3"),
             ("aac", "AAC"), ("flac", "FLAC")]
    for needle, label in table:
        if needle in text:
            return label
    return None


def derive_tags(rec):
    """Retourne une liste de couples (nom, genre) déduits d'un fichier."""
    tags = []
    cat, ext = rec.get("category"), (rec.get("ext") or "").lower()
    tags.append((cat, "type"))
    if rec.get("app"):
        tags.append((rec["app"], "type"))

    if cat in ("video", "image"):
        r = resolution_tag(rec.get("width"), rec.get("height"))
        if r:
            tags.append((r, "définition"))
        w, h = rec.get("width"), rec.get("height")
        if w and h:
            if h > w * 1.15:
                tags.append(("vertical", "définition"))
            elif abs(w - h) <= max(w, h) * 0.05:
                tags.append(("carré", "définition"))

    cam = (rec.get("camera") or "").strip()
    if cam:
        clean = re.sub(r"\s+", " ", cam)
        tags.append((clean, "caméra"))
        low = normalize(clean) + " "
        for needle, brand in BRANDS:
            if needle in low:
                tags.append((brand, "marque"))
                break

    if cat in ("video", "audio"):
        c = codec_tag(rec.get("codec"), ext)
        if c:
            tags.append((c, "codec"))
        cad, slow = cadence_tag(rec.get("fps"))
        if cad:
            tags.append((cad, "cadence"))
        if slow:
            tags.append(("ralenti", "cadence"))
        d = duration_tag(rec.get("duration"))
        if d:
            tags.append((d, "durée"))

    if ext in RAW_PHOTO_EXT or ext in RAW_VIDEO_EXT:
        tags.append(("RAW", "codec"))

    y = year_of(rec.get("shot_date"), rec.get("mtime"))
    if y:
        tags.append((y, "année"))

    parts = [p for p in (rec.get("rel_path") or "").replace("\\", "/").split("/") if p]
    seen = set()
    for part in parts[:-1]:
        np_ = normalize(part)
        for key, label in CONTENT_KEYWORDS.items():
            if key in np_ and label not in seen:
                seen.add(label)
                tags.append((label, "contenu"))
    if len(parts) >= 2 and normalize(parts[0]) not in GENERIC_FOLDERS:
        tags.append((parts[0].strip(), "dossier"))

    out, dedup = [], set()
    for name, kind in tags:
        name = (str(name) if name is not None else "").strip()
        if not name or len(name) > 60:
            continue
        key = (normalize(name), kind)
        if key not in dedup:
            dedup.add(key)
            out.append((name, kind))
    return out


class TagCache:
    def __init__(self, con):
        self.con = con
        self.cache = {}
        for r in con.execute("SELECT id, name, kind FROM tags"):
            self.cache[(normalize(r["name"]), r["kind"])] = r["id"]

    def id_for(self, name, kind):
        key = (normalize(name), kind)
        if key in self.cache:
            return self.cache[key]
        cur = self.con.execute(
            "INSERT OR IGNORE INTO tags (name, kind) VALUES (?,?)", (name, kind))
        if cur.lastrowid:
            tid = cur.lastrowid
        else:
            row = self.con.execute(
                "SELECT id FROM tags WHERE name=? AND kind=?", (name, kind)).fetchone()
            tid = row["id"]
        self.cache[key] = tid
        return tid


def tag_cloud(con, kind=None, min_count=1, vols=None):
    sql = ["""SELECT t.id, t.name, t.kind, COUNT(ft.file_id) n,
                     COALESCE(SUM(f.size),0) s
              FROM tags t
              JOIN file_tags ft ON ft.tag_id = t.id
              JOIN files f ON f.id = ft.file_id
              JOIN volumes v ON v.id = f.volume_id
              WHERE 1=1"""]
    args = []
    if vols:
        p = ",".join(["?"]*len(vols))
        sql.append(f"AND v.name IN ({p})")
        args += vols
    if kind and kind != "(tous)":
        sql.append("AND t.kind = ?")
        args.append(kind)
    sql.append("GROUP BY t.id HAVING n >= ? ORDER BY n DESC, t.name")
    args.append(min_count)
    return con.execute(" ".join(sql), args).fetchall()


def add_manual_tag(con, file_ids, name, kind="manuelle"):
    if not file_ids or not name.strip():
        return 0
    tc = TagCache(con)
    tid = tc.id_for(name.strip(), kind)
    con.executemany("INSERT OR IGNORE INTO file_tags (file_id, tag_id) VALUES (?,?)",
                    [(int(i), tid) for i in file_ids])
    con.commit()
    return len(file_ids)


def remove_tag_from(con, file_ids, tag_id):
    con.executemany("DELETE FROM file_tags WHERE file_id=? AND tag_id=?",
                    [(int(i), int(tag_id)) for i in file_ids])
    con.commit()


def tags_of(con, file_id):
    return con.execute(
        """SELECT t.name, t.kind FROM tags t JOIN file_tags ft ON ft.tag_id=t.id
           WHERE ft.file_id=? ORDER BY t.kind, t.name""", (file_id,)).fetchall()


def tags_for_files(con, file_ids):
    """Étiquettes de plusieurs fichiers en quelques requêtes au lieu d'une par fichier.
    Indispensable : une requête par ligne rendait l'affichage des résultats
    interminable au-delà de quelques centaines de fichiers."""
    out = defaultdict(list)
    ids = [int(i) for i in file_ids]
    chunk = 900
    for start in range(0, len(ids), chunk):
        part = ids[start:start + chunk]
        placeholders = ",".join("?" * len(part))
        for r in con.execute(
                f"""SELECT ft.file_id fid, t.name, t.kind FROM file_tags ft
                    JOIN tags t ON t.id = ft.tag_id
                    WHERE ft.file_id IN ({placeholders})
                    ORDER BY t.kind, t.name""", part):
            out[r["fid"]].append(r["name"])
    return out


# ---------------------------------------------------------------------------
# Disques branchés ou absents (mode « online » / « offline »)
# ---------------------------------------------------------------------------

def volume_online_path(con, vol_row, update=True):
    """Retourne le point de montage ACTUEL du disque s'il est branché, sinon None.

    La lettre de lecteur (Windows) et le point de montage (macOS) changent d'une
    session à l'autre : on ne peut pas se fier au chemin enregistré. On vérifie donc
    l'identité réelle du disque, dans cet ordre :
      1. un fichier témoin du catalogue existe-t-il à cet emplacement ?
      2. le numéro de série du volume correspond-il (Windows) ?
      3. à défaut, le nom du volume correspond-il ?
    """
    vid = vol_row["id"]
    sample = con.execute(
        "SELECT rel_path FROM files WHERE volume_id=? AND size > 0 ORDER BY id LIMIT 1",
        (vid,)).fetchone()
    candidates = []
    if vol_row["last_path"]:
        candidates.append(vol_row["last_path"])
    candidates.extend(list_mounted_volumes())

    seen = set()
    for cand in candidates:
        if not cand or cand in seen:
            continue
        seen.add(cand)
        try:
            if not os.path.isdir(cand):
                continue
        except OSError:
            continue
        ok = False
        vol_serial = vol_row["serial"] if "serial" in vol_row.keys() else None
        cand_serial = volume_serial(cand)
        
        # 1. Matching UUID (serial) is the absolute guarantee of identity
        if vol_serial and cand_serial and vol_serial == cand_serial:
            ok = True
        # 2. Fallback: Check for a specific known file on the disk
        elif sample and os.path.exists(os.path.join(cand, sample["rel_path"])):
            ok = True
        # 3. Fallback: Just rely on the mount name
        elif not sample and normalize(suggest_volume_name(cand)) == normalize(vol_row["name"]):
            ok = True
            
        if ok:
            if update and cand != vol_row["last_path"]:
                con.execute("UPDATE volumes SET last_path=? WHERE id=?", (cand, vid))
                con.commit()
            return cand
    return None


def online_map(con):
    """{id du disque: chemin actuel ou None} — l'état branché/absent de tout le parc.
    Optimisé pour être quasi-instantané même avec des millions de fichiers et des dizaines de disques.
    """
    vols = con.execute("SELECT id, name, last_path, serial FROM volumes").fetchall()
    mounted = list_mounted_volumes()
    mounted_set = set(mounted)
    
    # Carte des noms de disques actuellement branchés
    mounted_by_name = {}
    for p in mounted:
        norm_name = normalize(suggest_volume_name(p))
        if norm_name not in mounted_by_name:
            mounted_by_name[norm_name] = p
            
    res = {}
    for r in vols:
        vid = r["id"]
        last_p = r["last_path"]
        vname_norm = normalize(r["name"])
        
        # 1. Vérification directe O(1) si le chemin habituel est toujours monté
        if last_p and last_p in mounted_set:
            res[vid] = last_p
            continue
            
        # 2. Vérification rapide O(1) par nom de volume monté
        if vname_norm in mounted_by_name:
            cand = mounted_by_name[vname_norm]
            res[vid] = cand
            # Mettre à jour en tâche de fond si le chemin a changé
            if cand != last_p:
                try:
                    con.execute("UPDATE volumes SET last_path=? WHERE id=?", (cand, vid))
                    con.commit()
                except Exception:
                    pass
            continue
            
        res[vid] = None
        
    return res


# ---------------------------------------------------------------------------
# Maintenance du catalogue
# ---------------------------------------------------------------------------

def repair_catalog(con):
    """Répare un catalogue abîmé : fiches en double pour un même chemin, étiquettes
    orphelines, compteurs de disques erronés. Retourne un rapport chiffré."""
    before = con.execute("SELECT COUNT(*) n, COALESCE(SUM(size),0) s FROM files").fetchone()
    con.execute("""DELETE FROM files WHERE id NOT IN
                   (SELECT MAX(id) FROM files GROUP BY volume_id, rel_path)""")
    con.execute("DELETE FROM file_tags WHERE file_id NOT IN (SELECT id FROM files)")
    con.execute("DELETE FROM file_tags WHERE tag_id NOT IN (SELECT id FROM tags)")
    con.execute("""UPDATE volumes SET
                   file_count = (SELECT COUNT(*) FROM files WHERE volume_id = volumes.id),
                   total_size = (SELECT COALESCE(SUM(size),0) FROM files WHERE volume_id = volumes.id)""")
    con.commit()
    after = con.execute("SELECT COUNT(*) n, COALESCE(SUM(size),0) s FROM files").fetchone()
    try:
        con.execute("VACUUM")
    except sqlite3.Error:
        pass
    return {"removed": before["n"] - after["n"],
            "size_removed": before["s"] - after["s"],
            "files": after["n"], "size": after["s"]}


def retag_all(con, progress=None, mark_duplicates=True):
    """Recalcule toutes les étiquettes automatiques (les manuelles sont conservées)."""
    con.execute("""DELETE FROM file_tags WHERE tag_id IN
                   (SELECT id FROM tags WHERE kind <> 'manuelle')""")
    con.commit()
    tc = TagCache(con)
    rows = con.execute("SELECT * FROM files").fetchall()
    pairs, done = [], 0
    for r in rows:
        rec = {k: r[k] for k in r.keys()}
        for name, kind in derive_tags(rec):
            pairs.append((r["id"], tc.id_for(name, kind)))
        done += 1
        if len(pairs) >= 5000:
            con.executemany("INSERT OR IGNORE INTO file_tags VALUES (?,?)", pairs)
            pairs = []
            if progress:
                progress(done, len(rows))
    if pairs:
        con.executemany("INSERT OR IGNORE INTO file_tags VALUES (?,?)", pairs)
    con.commit()
    if mark_duplicates:
        tag_duplicates(con, tc)
    if progress:
        progress(len(rows), len(rows))
    return len(rows)


def tag_duplicates(con, tc=None):
    """Étiquette « doublon » et « doublon ×N » les fichiers présents en plusieurs exemplaires."""
    tc = tc or TagCache(con)
    base = tc.id_for("doublon", "doublon")
    con.execute("DELETE FROM file_tags WHERE tag_id IN (SELECT id FROM tags WHERE kind='doublon')")
    rows = con.execute(
        """SELECT quick_hash, COUNT(*) n FROM files
           WHERE quick_hash IS NOT NULL AND quick_hash <> ''
           GROUP BY quick_hash HAVING n > 1""").fetchall()
    pairs = []
    for r in rows:
        bucket = "doublon ×2-3" if r["n"] <= 3 else ("doublon ×4-5" if r["n"] <= 5 else "doublon ×6+")
        bid = tc.id_for(bucket, "doublon")
        for f in con.execute("SELECT id FROM files WHERE quick_hash=?", (r["quick_hash"],)):
            pairs.append((f["id"], base))
            pairs.append((f["id"], bid))
    if pairs:
        con.executemany("INSERT OR IGNORE INTO file_tags VALUES (?,?)", pairs)
    con.commit()
    return len(rows)


# ---------------------------------------------------------------------------
# Moteur d'analyse
# ---------------------------------------------------------------------------


import json
import datetime as dt

def human_size_local(n):
    if not n: return "--"
    try: n = float(n)
    except: return "--"
    if n < 1024: return f"{int(n)} octets"
    for unit in ("Ko", "Mo", "Go", "To"):
        n /= 1024.0
        if n < 1024: return f"{n:,.1f} {unit}".replace(",", " ")
    return ""

