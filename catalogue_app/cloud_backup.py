import os
import sys
import glob
import json
import gzip
import shutil
import sqlite3
from datetime import datetime
from .config import APP_DIR, DB_PATH

SETTINGS_PATH = os.path.join(APP_DIR, "settings.json")

def load_settings() -> dict:
    if os.path.exists(SETTINGS_PATH):
        try:
            with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_settings(data: dict):
    os.makedirs(APP_DIR, exist_ok=True)
    try:
        current = load_settings()
        current.update(data)
        with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
            json.dump(current, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Erreur sauvegarde settings: {e}")

def detect_google_drive_folder() -> str:
    """Tente de détecter automatiquement le dossier Google Drive de l'utilisateur."""
    # 1. Vérification dans ~/Library/CloudStorage (macOS FileProvider standard)
    cloud_storage = os.path.expanduser("~/Library/CloudStorage")
    if os.path.isdir(cloud_storage):
        matches = sorted(glob.glob(os.path.join(cloud_storage, "GoogleDrive-*")))
        # 1. Privilégier d'abord le dossier actif sans suffixe de date
        clean_matches = [m for m in matches if "(" not in os.path.basename(m)]
        search_list = clean_matches + [m for m in matches if "(" in os.path.basename(m)]
        for m in search_list:
            for sub in ["Mon Drive", "My Drive", ""]:
                p = os.path.join(m, sub) if sub else m
                try:
                    if os.path.exists(p):
                        return p
                except Exception:
                    pass

    # 2. Vérification dans /Volumes
    for vol in ["/Volumes/GoogleDrive/Mon Drive", "/Volumes/GoogleDrive/My Drive", "/Volumes/GoogleDrive"]:
        if os.path.exists(vol):
            return vol

    # 3. Dossier utilisateur standard
    user_drive = os.path.expanduser("~/Google Drive")
    if os.path.exists(user_drive):
        return user_drive

    return ""

def get_cloud_backup_dir() -> str:
    settings = load_settings()
    custom_dir = settings.get("google_drive_dir")
    if custom_dir and os.path.isdir(custom_dir):
        return custom_dir

    auto_dir = detect_google_drive_folder()
    if auto_dir:
        backup_sub = os.path.join(auto_dir, "CatalogueDisques_Backups")
        return backup_sub
    return ""

def set_cloud_backup_dir(path: str):
    save_settings({"google_drive_dir": path})

def perform_cloud_backup(target_dir: str, progress_cb=None, keep_count: int = 5) -> str:
    """
    Sauvegarde la base de données vers le dossier cible (Google Drive),
    en la compressant au format .db.gz pour réduire le volume de 70-80%.
    """
    if not progress_cb:
        progress_cb = lambda msg: None

    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"La base de données principale n'existe pas : {DB_PATH}")

    os.makedirs(target_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    temp_sqlite = os.path.join(APP_DIR, f"temp_backup_{timestamp}.db")
    target_gz = os.path.join(target_dir, f"catalogue_{timestamp}.db.gz")

    progress_cb("Instanciation de la sauvegarde SQLite sécurisée (sans verrou)...")
    try:
        # Copie via l'API backup de SQLite pour ne jamais bloquer la base en lecture/écriture
        src_con = sqlite3.connect(DB_PATH)
        dst_con = sqlite3.connect(temp_sqlite)
        with dst_con:
            src_con.backup(dst_con, pages=500)
        src_con.close()
        dst_con.close()

        raw_size = os.path.getsize(temp_sqlite)
        progress_cb(f"Compression gzip vers Google Drive ({raw_size // (1024*1024)} Mo d'origine)...")

        # Compression streamée par blocs de 1 Mo pour ne pas surcharger la RAM
        with open(temp_sqlite, "rb") as f_in:
            with gzip.open(target_gz, "wb", compresslevel=6) as f_out:
                shutil.copyfileobj(f_in, f_out, length=1024 * 1024)

        gz_size = os.path.getsize(target_gz)
        progress_cb(f"Fichier compressé créé : {gz_size // (1024*1024)} Mo (gain important d'espace).")

        # Nettoyage des anciennes sauvegardes sur Google Drive (garder les N dernières)
        existing = sorted(glob.glob(os.path.join(target_dir, "catalogue_*.db.gz")))
        if len(existing) > keep_count:
            for old_file in existing[:-keep_count]:
                try:
                    os.remove(old_file)
                except OSError:
                    pass

        progress_cb("Sauvegarde Google Drive terminée avec succès !")
        return target_gz
    finally:
        if os.path.exists(temp_sqlite):
            try:
                os.remove(temp_sqlite)
            except OSError:
                pass

import socket

def get_computer_name():
    return socket.gethostname().replace(" ", "_")

def sync_with_cloud(progress_cb=None):
    if not progress_cb:
        progress_cb = lambda msg: None
        
    target_dir = get_cloud_backup_dir()
    if not target_dir:
        raise ValueError("Aucun dossier Google Drive détecté.")
        
    os.makedirs(target_dir, exist_ok=True)
    my_name = get_computer_name()
    
    # 1. PUSH : Sauvegarder la base locale actuelle
    progress_cb("Étape 1/2 : Sauvegarde locale vers le Cloud...")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    temp_sqlite = os.path.join(APP_DIR, f"temp_sync_{timestamp}.db")
    target_gz = os.path.join(target_dir, f"catalogue_{my_name}_{timestamp}.db.gz")
    
    try:
        src_con = sqlite3.connect(DB_PATH)
        dst_con = sqlite3.connect(temp_sqlite)
        with dst_con:
            src_con.backup(dst_con, pages=500)
        src_con.close()
        dst_con.close()
        
        with open(temp_sqlite, "rb") as f_in:
            with gzip.open(target_gz, "wb", compresslevel=6) as f_out:
                shutil.copyfileobj(f_in, f_out, length=1024 * 1024)
                
        # Clean up old backups of THIS computer
        existing_mine = sorted(glob.glob(os.path.join(target_dir, f"catalogue_{my_name}_*.db.gz")))
        if len(existing_mine) > 3:
            for old_file in existing_mine[:-3]:
                try: os.remove(old_file)
                except OSError: pass
    finally:
        if os.path.exists(temp_sqlite):
            try: os.remove(temp_sqlite)
            except OSError: pass
            
    # 2. PULL : Récupérer les bases des AUTRES ordinateurs
    progress_cb("Étape 2/2 : Vérification des mises à jour des autres ordinateurs...")
    all_files = glob.glob(os.path.join(target_dir, "catalogue_*.db.gz"))
    
    # Grouper par nom d'ordinateur
    from collections import defaultdict
    others_latest = {}
    
    for fpath in all_files:
        base = os.path.basename(fpath)
        if base == os.path.basename(target_gz):
            continue # Ignorer notre propre sauvegarde immédiate
            
        # Format: catalogue_{computer}_{timestamp}.db.gz
        parts = base.replace("catalogue_", "").replace(".db.gz", "").rsplit("_", 2)
        if len(parts) == 3:
            comp, date, time = parts
        else:
            comp = "Unknown"
            
        if comp == my_name:
            continue
            
        if comp not in others_latest or fpath > others_latest[comp]:
            others_latest[comp] = fpath
            
    if not others_latest:
        progress_cb("Aucune base d'un autre ordinateur trouvée sur le Cloud. Vous êtes à jour !")
        return
        
    from .sync import merge_databases
    
    for comp, gz_path in others_latest.items():
        progress_cb(f"Fusion des données provenant de '{comp}'...")
        temp_extract = os.path.join(APP_DIR, f"temp_pull_{comp}.db")
        try:
            with gzip.open(gz_path, "rb") as f_in:
                with open(temp_extract, "wb") as f_out:
                    shutil.copyfileobj(f_in, f_out, length=1024 * 1024)
            merge_databases(DB_PATH, temp_extract, progress_cb=progress_cb)
        except Exception as e:
            progress_cb(f"Erreur lors de la fusion de {comp}: {e}")
        finally:
            if os.path.exists(temp_extract):
                try: os.remove(temp_extract)
                except OSError: pass
                
    progress_cb("Synchronisation terminée avec succès !")
