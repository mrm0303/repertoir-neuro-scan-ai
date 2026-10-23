import os
import json
import base64
import urllib.request
import threading
import time
import subprocess
import sqlite3
from io import BytesIO

# Try to load PIL for image resizing (don't explode LLM RAM)
try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

from catalogue_app.ai_chat import load_ai_config

class AIEnricher:
    def __init__(self, db_conn_factory, progress_callback=None):
        self.db_conn_factory = db_conn_factory
        self.progress_callback = progress_callback
        self.is_running = False
        self.thread = None

    def start(self):
        if self.is_running:
            return
        self.is_running = True
        self.thread = threading.Thread(target=self._worker, daemon=True)
        self.thread.start()

    def stop(self):
        self.is_running = False

    def _worker(self):
        con = self.db_conn_factory()
        
        while self.is_running:
            cfg = load_ai_config()
            if not cfg.get("url"):
                if self.progress_callback: self.progress_callback("Erreur: URL LM Studio non configurée.", 0, 0)
                time.sleep(2)
                continue
                
            # Find a file to process (video or image) that doesn't have an AI tag yet
            # We look for files on connected volumes (using a quick hack: we assume volumes with a known last_path that exists are connected)
            # Actually, to be safe, let's just query files and check if they exist on disk.
            query = """
                SELECT f.id, f.rel_path, v.last_path, f.category
                FROM files f 
                JOIN volumes v ON f.volume_id = v.id
                WHERE (f.category = 'video' OR f.category = 'image')
                AND f.id NOT IN (
                    SELECT ft.file_id FROM file_tags ft JOIN tags t ON t.id = ft.tag_id WHERE t.name LIKE 'ia:%'
                )
                ORDER BY f.mtime DESC
                LIMIT 50
            """
            try:
                rows = con.execute(query).fetchall()
            except Exception as e:
                print("DB Query Error:", e)
                time.sleep(5)
                continue
                
            if not rows:
                if self.progress_callback: self.progress_callback("Aucun nouveau fichier à analyser.", 0, 0)
                time.sleep(10)
                continue
                
            processed_any = False
            for row in rows:
                if not self.is_running:
                    break
                    
                fid = row["id"]
                rel_path = row["rel_path"]
                last_path = row["last_path"]
                cat = row["category"]
                
                # Reconstruct full path
                if not last_path: continue
                full_path = os.path.join(last_path, rel_path)
                
                if not os.path.exists(full_path):
                    # Disk not connected or file moved, skip for now
                    continue
                    
                processed_any = True
                if self.progress_callback: 
                    self.progress_callback(f"Analyse IA en cours : {os.path.basename(rel_path)}", 0, 0)
                    
                # A. Encodage Vecteur (Recherche Sémantique Locale)
                try:
                    import catalogue_app.ai_search as ai_search
                    if ai_search.HAS_AI:
                        vec = ai_search.encode_image(full_path)
                        if vec is not None:
                            con.execute("INSERT OR REPLACE INTO file_embeddings (file_id, embedding) VALUES (?, ?)", (fid, ai_search.serialize_vector(vec)))
                            con.commit()
                except Exception as e:
                    print("Erreur embedding local:", e)

                
                # 1. Extract Image Frame
                b64_img = self._extract_base64_frame(full_path, cat)
                if not b64_img:
                    # Mark as failed to avoid infinite loop
                    self._mark_failed(con, fid)
                    continue
                    
                # 2. Call LM Studio Vision API
                tags_text, err_msg = self._call_vision_api(b64_img, cfg)
                if not tags_text:
                    self._mark_failed(con, fid)
                    if self.progress_callback and err_msg:
                        self.progress_callback(f"Erreur API: {err_msg}", 0, 0)
                    continue
                    
                # 3. Parse tags and save
                tags = [t.strip().lower() for t in tags_text.replace('#', '').replace('.', '').split(',') if t.strip()]
                for t in tags[:5]: # Take max 5 tags
                    clean_tag = f"ia:{t}"
                    try:
                        # Ensure tag exists in tags table
                        con.execute("INSERT OR IGNORE INTO tags (name, kind) VALUES (?, 'auto')", (clean_tag,))
                        tag_id = con.execute("SELECT id FROM tags WHERE name = ?", (clean_tag,)).fetchone()["id"]
                        # Link tag to file
                        con.execute("INSERT OR IGNORE INTO file_tags (file_id, tag_id) VALUES (?, ?)", (fid, tag_id))
                    except Exception as ins_err:
                        print("Tag Insert Error:", ins_err)
                con.commit()
                
            if not processed_any:
                if self.progress_callback: self.progress_callback("En attente de disques branchés...", 0, 0)
                time.sleep(5)
                
        if self.progress_callback:
            self.progress_callback("Enrichissement arrêté.", 0, 0)
        con.close()

    def _mark_failed(self, con, fid):
        try:
            con.execute("INSERT OR IGNORE INTO tags (name, kind) VALUES ('ia:echec_analyse', 'auto')")
            tag_id = con.execute("SELECT id FROM tags WHERE name = 'ia:echec_analyse'").fetchone()["id"]
            con.execute("INSERT OR IGNORE INTO file_tags (file_id, tag_id) VALUES (?, ?)", (fid, tag_id))
            con.commit()
        except:
            pass

    def _extract_base64_frame(self, path, category):
        img_path = path
        temp_file = "/tmp/repertoir_ai_frame.jpg"
        
        if category == "video":
            # Extract frame at 1 second
            cmd = [
                "ffmpeg", "-y", "-ss", "00:00:01", "-i", path, 
                "-vframes", "1", "-q:v", "5", "-vf", "scale=512:-1", temp_file
            ]
            try:
                subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10)
                if os.path.exists(temp_file):
                    img_path = temp_file
                else:
                    return None
            except:
                return None
                
        # Resize and read as base64
        if not HAS_PIL:
            return None
            
        try:
            with Image.open(img_path) as img:
                img = img.convert("RGB")
                img.thumbnail((512, 512)) # Small size for LLM to process fast
                buffered = BytesIO()
                img.save(buffered, format="JPEG", quality=80)
                return base64.b64encode(buffered.getvalue()).decode('utf-8')
        except:
            return None
        finally:
            if img_path == temp_file and os.path.exists(temp_file):
                os.remove(temp_file)

    def _call_vision_api(self, b64_img, cfg):
        # Force a generic local model name to avoid crashing if user set gemma in text config
        cfg = cfg.copy()
        cfg["model"] = "local-model"

        url = cfg.get("url", "http://localhost:1234/v1/chat/completions")
        # Ensure standard openai endpoint if they passed the custom one for text
        if url.endswith("/api/v1/chat"):
            url = url.replace("/api/v1/chat", "/v1/chat/completions")
            
        payload = {
            "model": cfg.get("model", "local-model"),
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Décris ce que tu vois de manière extrêmement concise. Donne UNIQUEMENT 3 à 5 mots-clés pertinents, séparés par des virgules, sans aucune phrase."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{b64_img}"
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 30,
            "temperature": 0.2
        }
        
        headers = {"Content-Type": "application/json"}
        if cfg.get("api_key"):
            headers["Authorization"] = f"Bearer {cfg['api_key']}"
            
        req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                res = json.loads(response.read().decode("utf-8"))
                return res["choices"][0]["message"]["content"].strip(), ""
        except Exception as e:
            err = str(e)
            from catalogue_app.logger import log
            log.warning(f"Vision API: {err}")
            if "HTTP Error 400" in err or "does not support vision" in err.lower():
                return None, "Le modèle actuel ne supporte pas les images (Vision)."
            return None, "Serveur IA injoignable ou erreur."

