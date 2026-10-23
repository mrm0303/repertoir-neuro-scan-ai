import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
import os
import shutil
import base64
import requests
import xml.etree.ElementTree as ET
HEADERS = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7 AppleWebKit/537.36) Safari/537.36'}
from datetime import datetime
import json
from catalogue_app.config import DB_PATH, APP_DIR

def _load_default_nas():
    servers_file = os.path.join(APP_DIR, "servers.json")
    if os.path.exists(servers_file):
        try:
            with open(servers_file, "r", encoding="utf-8") as fh:
                items = json.load(fh)
            for it in items:
                if it.get("host", "").startswith("https://"):
                    return it.get("host", ""), it.get("user", "admin"), it.get("password", "")
            if items:
                return items[0].get("host", ""), items[0].get("user", "admin"), items[0].get("password", "")
        except Exception:
            pass
    return "", "admin", ""

# Configuration du NAS (chargée depuis ~/CatalogueDisques/servers.json)
NAS_HOST, NAS_USER, NAS_PASS = _load_default_nas()

def backup_database_to_nas(remote_folder="/Public/Backups"):
    """
    Sauvegarde la base de données locale (catalogue.db) sur le NAS QNAP
    en utilisant l'API REST officielle File Station.
    """
    try:
        # 1. Obtenir un SID (Session ID)
        pwd_b64 = base64.b64encode(NAS_PASS.encode()).decode()
        login_url = f"{NAS_HOST}/cgi-bin/authLogin.cgi?user={NAS_USER}&pwd={pwd_b64}"
        resp = requests.get(login_url, headers=HEADERS, verify=False, timeout=10)
        
        if resp.status_code != 200:
            return False, f"Erreur serveur NAS ({resp.status_code})"
            
        root = ET.fromstring(resp.text)
        auth_passed = root.findtext("authPassed")
        
        if auth_passed != "1":
            return False, "Authentification NAS échouée (identifiants incorrects)."
            
        sid = root.findtext("authSid")
        if not sid:
            return False, "Session NAS (SID) non reçue."
            
        # 2. Créer le dossier Backups s'il n'existe pas (ignore silencieusement si déjà existant)
        create_url = f"{NAS_HOST}/cgi-bin/filemanager/utilRequest.cgi"
        requests.get(create_url, headers=HEADERS, params={
            "func": "createdir",
            "dest_path": "/Public",
            "dest_folder": "Backups",
            "sid": sid
        }, verify=False, timeout=10)
        
        # 3. Préparer le fichier de backup local
        backup_name = f"catalogue_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        local_temp_copy = f"/tmp/{backup_name}"
        shutil.copy2(DB_PATH, local_temp_copy)
        
        # 4. Uploader le fichier
        upload_url = f"{NAS_HOST}/cgi-bin/filemanager/utilRequest.cgi"
        with open(local_temp_copy, "rb") as f:
            files = {"file": (backup_name, f)}
            data = {
                "func": "upload",
                "dest_path": remote_folder,
                "sid": sid
            }
            up_resp = requests.post(upload_url, headers=HEADERS, data=data, files=files, verify=False, timeout=60)
            
        # Nettoyage
        if os.path.exists(local_temp_copy):
            os.remove(local_temp_copy)
            
        if up_resp.status_code == 200 and '"success": "true"' in up_resp.text:
            return True, f"Sauvegarde réussie : {backup_name}"
        else:
            return False, f"Erreur lors de l'upload : {up_resp.text}"
            
    except Exception as e:
        return False, f"Exception lors de la sauvegarde: {str(e)}"
