"""
DIT (Digital Imaging Technician) Module
Copies rushes from a source (SD card, SSD) to one or multiple destinations (3-2-1 backup)
with checksum integrity verification (xxHash, MD5, SHA1) and ASC-MHL standard manifest generation.
"""
import os
import hashlib
import shutil
import threading
import time
import xml.etree.ElementTree as ET
from xml.dom import minidom
from datetime import datetime, timezone
from catalogue_app.logger import log

try:
    import xxhash
    HAS_XXHASH = True
except ImportError:
    HAS_XXHASH = False

MEDIA_EXTS = {
    ".mov", ".mp4", ".mxf", ".avi", ".mkv", ".r3d", ".braw", ".ari",
    ".arw", ".cr2", ".cr3", ".nef", ".dng", ".raw", ".raf",
    ".wav", ".aif", ".aiff", ".mp3", ".flac",
    ".xml", ".srt", ".edl", ".ale", ".csv",
}


def hash_file(path, algorithm="xxhash"):
    """Compute hash of a file. Returns hex digest string."""
    buf_size = 1024 * 1024 * 4  # 4 MB chunks

    if algorithm == "xxhash" and HAS_XXHASH:
        h = xxhash.xxh64()
    elif algorithm == "sha1":
        h = hashlib.sha1()
    else:
        h = hashlib.md5()

    with open(path, "rb") as f:
        while True:
            data = f.read(buf_size)
            if not data:
                break
            h.update(data)
    return h.hexdigest()


def check_destinations_space(dest_dirs, required_bytes):
    """
    Check if all destination paths have enough free disk space.
    Returns (bool_ok, dict_details).
    """
    details = {}
    all_ok = True
    for dest in dest_dirs:
        if not dest:
            continue
        try:
            # Check existing parent directory if dest doesn't exist yet
            check_path = dest
            while check_path and not os.path.exists(check_path):
                parent = os.path.dirname(check_path)
                if parent == check_path:
                    break
                check_path = parent
            
            usage = shutil.disk_usage(check_path)
            free = usage.free
            has_space = free >= required_bytes
            details[dest] = {
                "free_bytes": free,
                "required_bytes": required_bytes,
                "ok": has_space
            }
            if not has_space:
                all_ok = False
        except Exception as e:
            details[dest] = {"error": str(e), "ok": False}
            all_ok = False
    return all_ok, details


def generate_mhl_file(dest_dir, file_records, algorithm="md5"):
    """
    Generates an ASC-MHL (Media Hash List) XML 1.1 compliant file in the destination folder.
    """
    try:
        root = ET.Element("hashlist", version="1.1")
        
        creator = ET.SubElement(root, "creatorinfo")
        ET.SubElement(creator, "program").text = "Catalogue de Disques - DIT Engine"
        ET.SubElement(creator, "version").text = "6.0"
        ET.SubElement(creator, "creationdate").text = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        ET.SubElement(creator, "hostname").text = os.uname().nodename if hasattr(os, 'uname') else "localhost"

        for rec in file_records:
            h_elem = ET.SubElement(root, "hash")
            ET.SubElement(h_elem, "file").text = rec["rel_path"]
            ET.SubElement(h_elem, "size").text = str(rec["size"])
            ET.SubElement(h_elem, "lastmodificationdate").text = rec.get("mtime_str", "")
            
            # Hash tag based on algorithm
            algo_tag = "xxhash64" if algorithm == "xxhash" else algorithm
            hash_tag = ET.SubElement(h_elem, algo_tag)
            hash_tag.text = rec["hash"]

        xml_str = ET.tostring(root, encoding="utf-8")
        parsed = minidom.parseString(xml_str)
        pretty_xml = parsed.toprettyxml(indent="  ", encoding="utf-8")

        mhl_filename = f"MANIF_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mhl"
        mhl_path = os.path.join(dest_dir, mhl_filename)
        with open(mhl_path, "wb") as f:
            f.write(pretty_xml)
        
        log.info(f"MHL généré avec succès : {mhl_path}")
        return mhl_path
    except Exception as e:
        log.error(f"Erreur lors de la génération MHL : {e}")
        return None


class DITCopyJob:
    """
    Manages verified multi-destination media copy operations (3-2-1 backup).
    """

    def __init__(self, source_dir, dest_dirs, algorithm="xxhash",
                 create_mhl=True, progress_callback=None, finished_callback=None):
        self.source_dir = source_dir
        # Support single dest string or list of dests
        if isinstance(dest_dirs, str):
            self.dest_dirs = [dest_dirs] if dest_dirs else []
        else:
            self.dest_dirs = [d for d in dest_dirs if d]

        self.algorithm = algorithm if (algorithm == "xxhash" and HAS_XXHASH) else ("sha1" if algorithm == "sha1" else "md5")
        self.create_mhl = create_mhl
        self.progress_callback = progress_callback
        self.finished_callback = finished_callback
        self._stop = threading.Event()
        self._thread = None

    def start(self):
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()

    def _discover_files(self):
        """Find all media files in source directory."""
        files = []
        for root, dirs, filenames in os.walk(self.source_dir):
            for fn in filenames:
                ext = os.path.splitext(fn)[1].lower()
                if ext in MEDIA_EXTS:
                    full = os.path.join(root, fn)
                    rel = os.path.relpath(full, self.source_dir)
                    try:
                        sz = os.path.getsize(full)
                        mtime = os.path.getmtime(full)
                        mtime_str = datetime.fromtimestamp(mtime, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                        files.append((full, rel, sz, mtime_str))
                    except Exception:
                        continue
        return files

    def _run(self):
        report = {
            "source": self.source_dir,
            "destinations": self.dest_dirs,
            "algorithm": self.algorithm,
            "total_files": 0,
            "total_bytes": 0,
            "copied": 0,
            "verified": 0,
            "failed": [],
            "mhl_files": [],
            "elapsed": 0,
        }

        if not self.dest_dirs:
            report["failed"].append(("Configuration", "Aucun dossier de destination spécifié."))
            if self.finished_callback:
                self.finished_callback(report)
            return

        files = self._discover_files()
        report["total_files"] = len(files)
        total_bytes = sum(f[2] for f in files)
        report["total_bytes"] = total_bytes

        if not files:
            if self.finished_callback:
                self.finished_callback(report)
            return

        # Check disk space on all destinations
        space_ok, space_details = check_destinations_space(self.dest_dirs, total_bytes)
        if not space_ok:
            for d, det in space_details.items():
                if not det.get("ok"):
                    free_mb = det.get("free_bytes", 0) / (1024 * 1024)
                    req_mb = total_bytes / (1024 * 1024)
                    report["failed"].append((d, f"Espace disque insuffisant (Dispo: {free_mb:.1f} Mo, Requis: {req_mb:.1f} Mo)"))
            if self.finished_callback:
                self.finished_callback(report)
            return

        start_time = time.time()
        mhl_records = []

        for idx, (src_path, rel_path, size, mtime_str) in enumerate(files):
            if self._stop.is_set():
                break

            fn_display = os.path.basename(rel_path)

            # 1. Calculate Source Hash
            if self.progress_callback:
                self.progress_callback(
                    phase="hash_src",
                    current=idx + 1,
                    total=len(files),
                    filename=fn_display,
                    size=size,
                )

            try:
                src_hash = hash_file(src_path, self.algorithm)
            except Exception as e:
                report["failed"].append((rel_path, f"Calcul hash source échoué: {e}"))
                continue

            file_all_dests_ok = True

            # 2. Copy and Verify on Each Destination
            for d_idx, dest_dir in enumerate(self.dest_dirs):
                dst_path = os.path.join(dest_dir, rel_path)
                os.makedirs(os.path.dirname(dst_path), exist_ok=True)

                if self.progress_callback:
                    self.progress_callback(
                        phase=f"copy_d{d_idx+1}",
                        current=idx + 1,
                        total=len(files),
                        filename=f"[{d_idx+1}/{len(self.dest_dirs)}] {fn_display}",
                        size=size,
                    )

                # Copy
                try:
                    shutil.copy2(src_path, dst_path)
                except Exception as e:
                    report["failed"].append((f"{rel_path} -> {dest_dir}", f"Copie échouée: {e}"))
                    file_all_dests_ok = False
                    continue

                # Verify
                if self.progress_callback:
                    self.progress_callback(
                        phase=f"verify_d{d_idx+1}",
                        current=idx + 1,
                        total=len(files),
                        filename=f"Vérif [{d_idx+1}/{len(self.dest_dirs)}] {fn_display}",
                        size=size,
                    )

                try:
                    dst_hash = hash_file(dst_path, self.algorithm)
                    if dst_hash != src_hash:
                        report["failed"].append(
                            (f"{rel_path} -> {dest_dir}", f"INTÉGRITÉ ÉCHOUÉE: src={src_hash[:10]}… dst={dst_hash[:10]}…")
                        )
                        file_all_dests_ok = False
                except Exception as e:
                    report["failed"].append((f"{rel_path} -> {dest_dir}", f"Vérification checksum échouée: {e}"))
                    file_all_dests_ok = False

            if file_all_dests_ok:
                report["copied"] += 1
                report["verified"] += 1
                mhl_records.append({
                    "rel_path": rel_path,
                    "size": size,
                    "mtime_str": mtime_str,
                    "hash": src_hash
                })

        # 3. Generate MHL manifests for all destinations
        if self.create_mhl and mhl_records:
            for dest_dir in self.dest_dirs:
                mhl_path = generate_mhl_file(dest_dir, mhl_records, self.algorithm)
                if mhl_path:
                    report["mhl_files"].append(mhl_path)

        report["elapsed"] = time.time() - start_time

        if self.finished_callback:
            self.finished_callback(report)
