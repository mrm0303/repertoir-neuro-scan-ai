from .settings_manager import get_category_extensions
import os, re, unicodedata, shutil, subprocess, json, sys, sqlite3, time
from datetime import datetime
from .config import *

def is_system_path(path: str, root: str = "") -> bool:
    """Le chemin appartient-il à une zone système à ne pas inventorier ?"""
    try:
        p = os.path.abspath(path).replace("\\", "/").lower()
    except (OSError, ValueError):
        return False
    if os.name == "nt":
        _, rest = os.path.splitdrive(p)
        parts = [x for x in rest.split("/") if x]
        if parts and parts[0] in SYSTEM_FIRST_PARTS_NT:
            return True
        return "/appdata/local/temp" in p or "/appdata/local/packages" in p
    for prefix in SYSTEM_PREFIXES_POSIX:
        if p == prefix or p.startswith(prefix + "/"):
            return True
    return False


def prune_dirs(dirpath, dirnames, filenames, root_dev, skip_system, seen_dirs, scan_root, stats=None):
    keep = []
    
    # Détecter si on analyse le disque système (boot drive) pour limiter la vérification des inodes.
    # Les pilotes NTFS / exFAT externes sur macOS/Linux retournent souvent des inodes constants (ex: 2)
    # ce qui entraînait le saut (skip) de tous les dossiers.
    try:
        boot_dev = os.stat("/").st_dev
        is_boot = (root_dev == boot_dev)
    except OSError:
        is_boot = False

    for d in dirnames:
        if d in SKIP_DIRS:
            continue
        full = os.path.join(dirpath, d)
        
        ext = os.path.splitext(d)[1].lstrip(".").lower()
        if ext in BUNDLE_EXT:
            filenames.append(d)
            continue
            
        if skip_system and is_system_path(full, root=scan_root):
            if stats is not None:
                stats["system_skipped"] += 1
            continue
        try:
            if os.path.islink(full):
                continue
            st = os.lstat(full)
        except OSError:
            continue
            
        # On ne traverse pas les points de montage (ex: depuis / vers /Volumes)
        if root_dev is not None and getattr(st, "st_dev", root_dev) != root_dev:
            continue
            
        # La déduplication par Inode n'est requise que sur le disque principal (protection Firmlinks APFS).
        # Sur les disques externes, elle est désactivée pour contrer les bugs d'inodes constants des drivers NTFS/FAT.
        if getattr(st, "st_ino", 0) and is_boot:
            key = (st.st_dev, st.st_ino)
            if key in seen_dirs:
                continue
            seen_dirs.add(key)
            
        keep.append(d)
    dirnames[:] = keep


def classify(ext: str) -> str:
    ext = ext.lower()
    cats = get_category_extensions()
    if ext in cats["projet"]:
        return "projet"
    if ext in cats["video"]:
        return "video"
    if ext in cats["image"]:
        return "image"
    if ext in cats["audio"]:
        return "audio"
    if ext in cats["document"]:
        return "document"
    if ext in cats["archive"]: return "archive"
    if ext in cats["logiciel"]: return "logiciel"
    if ext in cats["3d"]: return "3d"
    if ext in cats["code"]: return "code"
    return "autre"


# ---------------------------------------------------------------------------
# Normalisation du texte (accents latins + variantes arabes)
# ---------------------------------------------------------------------------

_ARABIC_MAP = str.maketrans({
    "أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا",
    "ى": "ي", "ئ": "ي", "ؤ": "و", "ة": "ه",
    "ـ": "",
})
_ARABIC_DIACRITICS = re.compile(r"[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]")


def normalize(text: str) -> str:
    """Minuscules, sans accents latins ni diacritiques arabes, alif/hamza unifiés."""
    if not text:
        return ""
    t = text.lower().translate(_ARABIC_MAP)
    t = _ARABIC_DIACRITICS.sub("", t)
    t = unicodedata.normalize("NFD", t)
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    return unicodedata.normalize("NFC", t)


# ---------------------------------------------------------------------------
# Affichage
# ---------------------------------------------------------------------------

def human_size(n) -> str:
    try:
        n = float(n or 0)
    except (TypeError, ValueError):
        return ""
    if n < 1024:
        return f"{int(n)} o"
    for unit in ("Ko", "Mo", "Go", "To", "Po"):
        n /= 1024.0
        if n < 1024 or unit == "Po":
            return f"{n:,.1f} {unit}".replace(",", " ")
    return ""


def human_duration(seconds) -> str:
    try:
        s = float(seconds)
    except (TypeError, ValueError):
        return ""
    if s <= 0:
        return ""
    h, rem = divmod(int(round(s)), 3600)
    m, sec = divmod(rem, 60)
    return f"{h}:{m:02d}:{sec:02d}" if h else f"{m}:{sec:02d}"


def human_clock(seconds) -> str:
    """Chronomètre lisible : 45 s / 12 min 30 s / 2 h 14 min."""
    try:
        s = int(round(float(seconds)))
    except (TypeError, ValueError):
        return "—"
    if s < 60:
        return f"{s} s"
    if s < 3600:
        return f"{s // 60} min {s % 60:02d} s"
    return f"{s // 3600} h {(s % 3600) // 60:02d} min"


def human_count(n) -> str:
    try:
        return f"{int(n):,}".replace(",", " ")
    except (TypeError, ValueError):
        return "0"


def fmt_date(ts) -> str:
    try:
        return datetime.fromtimestamp(float(ts)).strftime("%Y-%m-%d")
    except (TypeError, ValueError, OSError, OverflowError):
        return ""


def year_of(shot_date, mtime):
    if shot_date:
        m = re.search(r"(19|20)\d{2}", str(shot_date))
        if m:
            return m.group(0)
    try:
        return datetime.fromtimestamp(float(mtime)).strftime("%Y")
    except (TypeError, ValueError, OSError, OverflowError):
        return None


def fmt_fps(fps) -> str:
    """Formatte le débit d'images en nombre arrondi ou chaîne lisible sans crash."""
    if fps is None or fps == "":
        return ""
    try:
        val = float(fps)
        if val.is_integer():
            return str(int(val))
        return f"{val:.2f}".rstrip("0").rstrip(".")
    except (ValueError, TypeError):
        return str(fps)


def move_to_trash(path: str) -> tuple[bool, str]:
    """Déplace un fichier vers la Corbeille de manière native et sécurisée (macOS, Windows, Linux)."""
    if not os.path.exists(path):
        return False, "Fichier introuvable sur le disque."
    try:
        if sys.platform == "darwin":
            # Corbeille native macOS via AppleScript Finder
            escaped_path = path.replace('\\', '\\\\').replace('"', '\\"')
            cmd = ["osascript", "-e", f'tell application "Finder" to delete POSIX file "{escaped_path}"']
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if res.returncode == 0:
                return True, "Fichier déplacé dans la Corbeille macOS avec succès."
            user_trash = os.path.expanduser("~/.Trash")
            if os.path.isdir(user_trash):
                dest = os.path.join(user_trash, os.path.basename(path))
                if os.path.exists(dest):
                    base, ext = os.path.splitext(dest)
                    dest = f"{base}_{int(time.time())}{ext}"
                shutil.move(path, dest)
                return True, "Fichier déplacé dans ~/.Trash avec succès."
        elif os.name == "nt":
            # Corbeille native Windows via PowerShell
            clean_win = path.replace("'", "''")
            ps_cmd = f"Add-Type -AssemblyName Microsoft.VisualBasic; [Microsoft.VisualBasic.FileIO.FileSystem]::DeleteFile('{clean_win}', 'OnlyErrorDialogs', 'SendToRecycleBin')"
            res = subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], capture_output=True, text=True, timeout=10)
            if res.returncode == 0:
                return True, "Fichier déplacé dans la Corbeille Windows avec succès."
        elif sys.platform.startswith("linux"):
            # Corbeille Linux standard (GIO / trash-cli)
            try:
                res = subprocess.run(["gio", "trash", path], capture_output=True, text=True, timeout=10)
                if res.returncode == 0:
                    return True, "Fichier déplacé dans la Corbeille Linux avec succès."
            except Exception:
                pass

        # Fallback suppression directe si la corbeille système est inaccessible
        os.remove(path)
        return True, "Fichier supprimé (Corbeille indisponible)."
    except Exception as e:
        return False, f"Erreur lors du déplacement vers la corbeille : {e}"


def quick_preview(paths):
    """Aperçu rapide multiplateforme : QuickLook sur macOS, visionneuse système sur Windows & Linux."""
    if not paths:
        return
    if isinstance(paths, str):
        paths = [paths]
    clean_paths = [p for p in paths if os.path.exists(p)]
    if not clean_paths:
        return
    try:
        if sys.platform == "darwin":
            subprocess.Popen(["qlmanage", "-p"] + clean_paths)
        elif os.name == "nt":
            for p in clean_paths[:4]:
                os.startfile(os.path.normpath(p))
        else:
            for p in clean_paths[:4]:
                subprocess.Popen(["xdg-open", p])
    except Exception:
        pass


def check_directory_access(path: str) -> tuple[bool, str, str, str]:
    """
    Vérifie la validité et l'accessibilité réelle d'un dossier ou volume (macOS, Windows, Linux).
    Gère spécifiquement :
    - Les volumes Mac OS Étendu (HFS+) avec propriétaire / autorisations POSIX activées
    - Les protections macOS TCC (Accès complet au disque / Volumes amovibles)
    - La normalisation Unicode (NFC / NFD) propre aux systèmes de fichiers Mac
    - Les points de montage décalés (/Volumes/Nom 1) ou les disques débranchés / en veille

    Retourne : (ok: bool, resolved_path: str, error_kind: str, error_message: str)
      error_kind : "" | "empty" | "not_a_dir" | "permission_hfs" | "permission_tcc" | "permission_denied" | "not_found" | "os_error"
    """
    import stat
    raw = (path or "").strip().strip("'\"")
    if not raw:
        return False, "", "empty", "Veuillez sélectionner un disque ou un dossier à analyser."

    # Normalisation et résolution des chemins
    candidates = [raw]
    if sys.platform == "darwin":
        nfd_p = unicodedata.normalize('NFD', raw)
        nfc_p = unicodedata.normalize('NFC', raw)
        if nfd_p not in candidates: candidates.append(nfd_p)
        if nfc_p not in candidates: candidates.append(nfc_p)

    resolved = None
    exists = False
    is_dir = False
    perm_err = None
    os_err = None

    for c in candidates:
        try:
            st = os.stat(c)
            exists = True
            is_dir = stat.S_ISDIR(st.st_mode)
            resolved = c
            break
        except PermissionError as pe:
            exists = True
            is_dir = True  # Considéré comme dossier si présent dans /Volumes
            perm_err = pe
            resolved = c
            break
        except FileNotFoundError:
            if os.path.lexists(c):
                exists = True
                resolved = c
                try:
                    lst = os.lstat(c)
                    is_dir = stat.S_ISDIR(lst.st_mode)
                except Exception:
                    is_dir = True
                break
        except OSError as oe:
            os_err = oe
            if os.path.lexists(c):
                exists = True
                resolved = c
                is_dir = True
                break

    if resolved is None:
        resolved = raw

    # 1. Dossier introuvable
    if not exists:
        if sys.platform == "darwin" and resolved.startswith("/Volumes/"):
            # Vérifier si le disque a été monté sous un nom incrémenté (ex: /Volumes/NOM 1)
            base_vol = resolved.rstrip("/")
            alt_candidates = [f"{base_vol} {i}" for i in range(1, 5)]
            for alt in alt_candidates:
                if os.path.lexists(alt):
                    return (
                        False, alt, "not_found",
                        f"Le disque « {os.path.basename(resolved)} » a été monté par macOS sous le chemin « {alt} ».\n\n"
                        f"Veuillez sélectionner ce chemin mis à jour."
                    )
        return (
            False, resolved, "not_found",
            f"Le dossier ou disque « {resolved} » est introuvable.\n\n"
            f"Assurez-vous que le périphérique est bien branché et visible dans le Finder."
        )

    # 2. C'est un fichier simple, pas un dossier
    if not is_dir:
        return (
            False, resolved, "not_a_dir",
            f"« {resolved} » est un fichier et non un dossier.\n\n"
            f"Veuillez choisir un dossier ou un disque."
        )

    # 3. Test de lecture réelle si stat n'a pas déjà levé de permission
    if not perm_err and not os_err:
        try:
            with os.scandir(resolved) as it:
                next(it, None)
        except PermissionError as pe:
            perm_err = pe
        except OSError as oe:
            os_err = oe

    # 4. Traitement des erreurs de permissions (HFS+, TCC macOS, ou POSIX)
    if perm_err:
        errno_val = getattr(perm_err, "errno", None)
        vol_name = os.path.basename(resolved.rstrip("/"))
        is_macos_vol = sys.platform == "darwin" and (resolved.startswith("/Volumes/") or resolved.startswith("/Volumes"))

        # macOS TCC : Errno 1 (Operation not permitted)
        if errno_val == 1 or "Operation not permitted" in str(perm_err):
            return (
                False, resolved, "permission_tcc",
                f"macOS bloque l'accès au disque « {vol_name} » (Protection de confidentialité Système).\n\n"
                f"💡 Pour débloquer l'accès :\n"
                f"1. Ouvrez « Réglages Système » > « Confidentialité et sécurité ».\n"
                f"2. Allez dans « Fichiers et dossiers » (ou « Accès complet au disque »).\n"
                f"3. Activez l'accès aux « Volumes amovibles » pour Repertoir (ou Python / Terminal)."
            )

        # macOS HFS+ (Mac OS Étendu) : Errno 13 (Permission denied) ou volume sous /Volumes
        if is_macos_vol:
            return (
                False, resolved, "permission_hfs",
                f"Le disque « {vol_name} » (formaté en Mac OS Étendu / HFS+) restreint l'accès à son contenu pour votre session utilisateur ({perm_err}).\n\n"
                f"Ce format conserve strictement les autorisations d'origine du Mac.\n\n"
                f"💡 Solution officielle Apple (1 clic) :\n"
                f"1. Ouvrez la fenêtre « Lire les informations » du disque dans le Finder (Cmd + I).\n"
                f"2. En bas de la fenêtre, déverrouillez le cadenas 🔒 avec votre mot de passe.\n"
                f"3. Cochez la case : « Ignorer les autorisations de ce volume » ☑️.\n\n"
                f"Souhaitez-vous ouvrir la fenêtre « Lire les informations » du disque dans le Finder dès maintenant ?"
            )

        return (
            False, resolved, "permission_denied",
            f"Accès refusé au dossier « {resolved} » ({perm_err}).\n\n"
            f"Vérifiez que votre compte utilisateur dispose des droits de lecture sur ce dossier."
        )

    # 5. Erreur I/O ou disque en veille
    if os_err:
        return (
            False, resolved, "os_error",
            f"Erreur d'accès matériel ou disque indisponible ({os_err}).\n\n"
            f"Si c'est un disque dur mécanique, il est peut-être en veille ou le câble a été déconnecté."
        )

    return True, resolved, "", ""


def prompt_directory_access_fix(parent, path: str, error_kind: str, error_message: str):
    """
    Affiche une boîte de dialogue explicative et propose une action directe
    (ouvrir Finder Get Info pour HFS+, ouvrir Réglages Système pour TCC).
    """
    import tkinter.messagebox as mb
    from .config import APP_NAME

    if error_kind == "permission_hfs":
        res = mb.askyesno(
            f"{APP_NAME} — Accès disque HFS+",
            error_message,
            icon="warning",
            parent=parent
        )
        if res:
            try:
                # Ouvre directement la fenêtre "Lire les informations" du Finder pour ce volume
                script = f'tell application "Finder" to open information window of (POSIX file "{path}" as alias)'
                subprocess.Popen(["osascript", "-e", script])
            except Exception as e:
                mb.showerror(APP_NAME, f"Impossible d'ouvrir le Finder : {e}", parent=parent)
        return

    if error_kind == "permission_tcc":
        res = mb.askyesno(
            f"{APP_NAME} — Confidentialité macOS",
            error_message + "\n\nSouhaitez-vous ouvrir les Réglages Système dès maintenant ?",
            icon="warning",
            parent=parent
        )
        if res:
            try:
                subprocess.Popen(["open", "x-apple.systempreferences:com.apple.preference.security?Privacy_AllFiles"])
            except Exception:
                pass
        return

    mb.showerror(APP_NAME, error_message, parent=parent)


