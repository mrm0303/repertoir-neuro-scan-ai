import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
import requests
import base64
import xml.etree.ElementTree as ET

class RemoteServer:
    def __init__(self, name, host, user, password, server_type):
        self.name = name
        self.host = host
        self.user = user
        self.password = password
        self.server_type = server_type 

    def list_disks(self):
        raise NotImplementedError

class QNAPServer(RemoteServer):
    def list_disks(self):
        try:
            pwd_b64 = base64.b64encode(self.password.encode()).decode()
            login_url = f"{self.host}/cgi-bin/authLogin.cgi?user={self.user}&pwd={pwd_b64}"
            r = requests.get(login_url, verify=False, timeout=10)
            
            if r.status_code != 200:
                return [{"name": f"Erreur serveur ({r.status_code})", "type": "error"}]
                
            root = ET.fromstring(r.text)
            auth_sid = root.findtext("authSid")
            
            if not auth_sid:
                return [{"name": "Erreur d'authentification (mot de passe ?)", "type": "error"}]
                
            fs_url = f"{self.host}/cgi-bin/filemanager/utilRequest.cgi"
            r2 = requests.get(fs_url, params={'func': 'get_tree', 'node': 'share_root', 'sid': auth_sid}, verify=False, timeout=10)
            
            # Simple mock parsing for now
            return [
                {"name": "Public", "type": "Dossier Partagé"},
                {"name": "Multimedia", "type": "Dossier Partagé"},
                {"name": "Backups", "type": "Dossier Partagé"},
                {"name": "Web", "type": "Dossier Partagé"}
            ]
        except requests.exceptions.Timeout:
            return [{"name": f"Timeout : Le NAS ({self.host}) ne répond pas.", "type": "error"}]
        except Exception as e:
            return [{"name": f"Erreur: {str(e)}", "type": "error"}]

def get_configured_servers():
    import os, json
    from catalogue_app.config import APP_DIR
    servers_file = os.path.join(APP_DIR, "servers.json")
    if os.path.exists(servers_file):
        try:
            with open(servers_file, "r", encoding="utf-8") as fh:
                items = json.load(fh)
            return [
                QNAPServer(
                    it.get("name", "NAS"),
                    it.get("host", ""),
                    it.get("user", "admin"),
                    it.get("password", ""),
                    it.get("server_type", "QNAP")
                )
                for it in items if it.get("host")
            ]
        except Exception:
            pass
    return []
