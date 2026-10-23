import os
import sqlite3
import base64
import json
import urllib.request
import subprocess
import threading
import time
from catalogue_app.ai_chat import load_ai_config
from catalogue_app.config import THUMBNAILS_DIR

def init_vision_db(con):
    con.execute('''CREATE TABLE IF NOT EXISTS ai_metadata (
                    file_id INTEGER PRIMARY KEY,
                    vision_desc TEXT,
                    analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(file_id) REFERENCES files(id) ON DELETE CASCADE
                 )''')
    con.execute('''CREATE VIRTUAL TABLE IF NOT EXISTS fts_vision USING fts5(
                    file_id UNINDEXED,
                    vision_desc
                 )''')
    
    # Triggers for FTS synchronization
    con.execute('''CREATE TRIGGER IF NOT EXISTS ai_metadata_ad AFTER DELETE ON ai_metadata BEGIN
        DELETE FROM fts_vision WHERE file_id = old.file_id;
    END;''')
    
    con.execute('''CREATE TRIGGER IF NOT EXISTS ai_metadata_au AFTER UPDATE ON ai_metadata BEGIN
        DELETE FROM fts_vision WHERE file_id = old.file_id;
        INSERT INTO fts_vision (rowid, file_id, vision_desc) VALUES (new.file_id, new.file_id, new.vision_desc);
    END;''')
    
    con.commit()

def extract_frames_as_base64(file_path, category, fid=None):
    # Returns a list of base64 strings
    try:
        if category == "video" or file_path.lower().endswith((".mp4", ".mov", ".mkv", ".mxf", ".avi", ".ts", ".webm")):
            # Determine duration
            dur_cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", file_path]
            try:
                dur_out = subprocess.check_output(dur_cmd, text=True, timeout=5).strip()
                duration = float(dur_out)
            except:
                duration = 30.0 # fallback
                
            # Smart interval sampling:
            # - Short clips (<60s): take frame every 5s (5s, 10s, 15s...)
            # - Medium clips (60s-600s): 5 frames evenly spaced
            # - Long videos / interviews (>600s): sample every 30s to 60s (up to 6 frames)
            if duration <= 60:
                timestamps = list(range(5, max(6, int(duration)), 5))[:6]
                if not timestamps:
                    timestamps = [max(1, int(duration // 2))]
            elif duration <= 600:
                num_frames = 5
                interval = duration / (num_frames + 1)
                timestamps = [int(interval * i) for i in range(1, num_frames + 1)]
            else:
                # Interview / long rush: sample key points at 30s intervals or spread across the interview
                num_frames = 6
                interval = duration / (num_frames + 1)
                timestamps = [int(interval * i) for i in range(1, num_frames + 1)]
            
            b64_list = []
            for i, timestamp in enumerate(timestamps, start=1):
                tmp_path = f"/tmp/repertoir_vision_frame_{i}.jpg"
                cmd = [
                    "ffmpeg", "-y", "-ss", str(timestamp), "-i", file_path, 
                    "-vframes", "1", 
                    "-vf", "scale=384:-1", "-q:v", "6", tmp_path
                ]
                subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10)
                
                if os.path.exists(tmp_path):
                    if i == 1 and fid:
                        import shutil
                        try:
                            shutil.copy2(tmp_path, os.path.join(THUMBNAILS_DIR, f"{fid}.jpg"))
                        except: pass
                    with open(tmp_path, "rb") as f:
                        b64_list.append(base64.b64encode(f.read()).decode("utf-8"))
                    os.remove(tmp_path)
            
            return b64_list
            
        else: # image
            tmp_path = "/tmp/repertoir_vision_frame.jpg"
            from PIL import Image
            with Image.open(file_path) as img:
                img.thumbnail((512, 512))
                img = img.convert("RGB")
                img.save(tmp_path, "JPEG", quality=80)
            if fid:
                import shutil
                try:
                    shutil.copy2(tmp_path, os.path.join(THUMBNAILS_DIR, f"{fid}.jpg"))
                except: pass
            with open(tmp_path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode("utf-8")
            os.remove(tmp_path)
            return [b64]
            
    except Exception as e:
        print(f"Frame extraction error: {e}")
        return []

def analyze_image_with_lmstudio(b64_list):
    cfg = load_ai_config()
    if not cfg.get("enabled_vision", True):
        return None

    # Replace with local LM Studio chat endpoint if needed
    url = cfg.get("url", "http://127.0.0.1:1234/v1/chat/completions")
    model = cfg.get("model", "local-model")
    api_key = cfg.get("api_key", "")
    
    # OpenAI Vision format with multiple images
    content = [{"type": "text", "text": "Voici plusieurs images extraites de la même vidéo à différents moments. Synthétise ce qu'il se passe globalement dans la vidéo (objets, personnes, environnement, couleurs, ambiance, action). N'utilise que des mots-clés ou des phrases courtes. Réponds en français."}]
    for b64 in b64_list:
        content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}})
        
    messages = [{"role": "user", "content": content}]
    
    data = {
        "model": model,
        "messages": messages,
        "temperature": 0.2,
        "max_tokens": 200
    }
    
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
        
    req = urllib.request.Request(url, data=json.dumps(data).encode("utf-8"), headers=headers)
    
    try:
        with urllib.request.urlopen(req, timeout=12) as response:
            res = json.loads(response.read().decode("utf-8"))
            if "choices" in res and len(res["choices"]) > 0:
                return res["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"Vision API error: {e}")
    return None

def test_vision_api():
    """Vérifie si le serveur IA réponds et accepte les requêtes de vision."""
    cfg = load_ai_config()
    if not cfg.get("enabled_vision", True):
        return False, "La vision IA est désactivée dans les paramètres."
    
    url = cfg.get("url", "http://127.0.0.1:1234/v1/chat/completions")
    model = cfg.get("model", "local-model")
    api_key = cfg.get("api_key", "")
    
    # 1x1 red PNG base64 pour test
    tiny_b64 = "iVBORw0KGgoAAAANSU5EUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
    content = [
        {"type": "text", "text": "Test vision. Qu'est-ce que tu vois ? Réponds brièvement."},
        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{tiny_b64}"}}
    ]
    messages = [{"role": "user", "content": content}]
    data = {"model": model, "messages": messages, "temperature": 0.1, "max_tokens": 10}
    
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
        
    req = urllib.request.Request(url, data=json.dumps(data).encode("utf-8"), headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            res = json.loads(response.read().decode("utf-8"))
            if "choices" in res and len(res["choices"]) > 0:
                return True, "OK"
            return False, "Format de réponse inattendu du serveur IA."
    except Exception as e:
        return False, f"Le serveur IA n'a pas répondu à la requête vision ({e}). Vérifiez que votre modèle IA local prend bien en charge la vision."

class VisionIndexerThread(threading.Thread):
    def __init__(self, db_path, progress_callback=None, finished_callback=None, error_callback=None):
        super().__init__(daemon=True)
        self.db_path = db_path
        self.progress_callback = progress_callback
        self.finished_callback = finished_callback
        self.error_callback = error_callback
        self._stop = threading.Event()

    def stop(self):
        self._stop.set()

    def run(self):
        con = sqlite3.connect(self.db_path)
        con.row_factory = sqlite3.Row
        init_vision_db(con)
        
        # Get un-indexed media files (must be physically present on mounted volumes)
        from catalogue_app.scanner import online_map
        online = online_map(con)
        
        query = """
            SELECT f.id, v.last_path, f.rel_path, f.category, v.id as vid
            FROM files f
            JOIN volumes v ON f.volume_id = v.id
            WHERE f.category IN ('video', 'image')
            AND f.id NOT IN (SELECT file_id FROM ai_metadata)
        """
        rows = con.execute(query).fetchall()
        
        # Filter rows where volume is mounted
        to_process = []
        for r in rows:
            mount = online.get(r["vid"])
            if mount:
                abs_path = os.path.join(mount, r["rel_path"].lstrip("/"))
                if os.path.exists(abs_path):
                    to_process.append((r["id"], abs_path, r["category"]))
                    
        total = len(to_process)
        if total == 0:
            if self.finished_callback:
                self.finished_callback(0)
            return

        count = 0
        consecutive_errors = 0
        for fid, path, cat in to_process:
            if self._stop.is_set():
                break
                
            count += 1
            if self.progress_callback:
                self.progress_callback(count, total, path)
                
            b64_list = extract_frames_as_base64(path, cat, fid=fid)
            if b64_list:
                desc = analyze_image_with_lmstudio(b64_list)
                if desc:
                    consecutive_errors = 0
                    con.execute("INSERT OR REPLACE INTO ai_metadata (file_id, vision_desc) VALUES (?, ?)", (fid, desc))
                    con.execute("INSERT OR REPLACE INTO fts_vision (rowid, file_id, vision_desc) VALUES (?, ?, ?)", (fid, fid, desc))
                    
                    # Auto-extract thematic tags immediately into file_tags
                    try:
                        import re
                        from catalogue_app.tag_engine import THEMATIC_SEEDS
                        from catalogue_app.db import add_manual_tag
                        desc_lower = desc.lower()
                        for seed in THEMATIC_SEEDS:
                            if re.search(r'\b' + re.escape(seed) + r'\b', desc_lower):
                                add_manual_tag(con, [fid], seed.capitalize(), kind="contenu")
                    except Exception as tag_err:
                        print("Erreur auto-tagging vision:", tag_err)

                    con.commit()
                else:
                    consecutive_errors += 1
                    if consecutive_errors >= 3:
                        print("Vision Indexer: 3 erreurs consécutives, arrêt de l'indexation.")
                        if self.error_callback:
                            self.error_callback("Le serveur IA ne répond pas ou ne prend pas en charge l'analyse visuelle d'images.")
                        break

            # Short sleep to not overload LM Studio
            time.sleep(0.2)

        con.close()
        if not self._stop.is_set() and consecutive_errors < 3:
            if self.finished_callback:
                self.finished_callback(count)
