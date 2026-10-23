"""
Serveur Web & API REST Local Sécurisé (FastAPI + Web App Responsive).
Permet de consulter et rechercher dans le catalogue depuis un smartphone, une tablette
ou n'importe quel ordinateur connecté sur le réseau local (Wi-Fi / Ethernet) avec authentification par Code PIN.
"""

import os
import socket
import secrets
import threading
import sqlite3
import uvicorn
from fastapi import FastAPI, Query, HTTPException, Request, Response, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from .config import DB_PATH, APP_NAME, APP_VERSION
from .utils import human_size, human_count, normalize
from .queries import stats, search_files

app = FastAPI(
    title="RNS.AI API",
    description="API REST & Interface Web pour explorer votre catalogue de disques",
    version=APP_VERSION
)

import os
_assets_path = os.path.join(os.path.dirname(__file__), "assets")
app.mount("/assets", StaticFiles(directory=_assets_path), name="assets")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Variable de sécurité du PIN (par défaut 6 chiffres aléatoires par session ou personnalisable)
CURRENT_PIN = secrets.token_hex(3).upper() # Ex: 'A4F1B2' ou 6 chiffres

def get_db():
    con = sqlite3.connect(DB_PATH, check_same_thread=False)
    con.row_factory = sqlite3.Row
    return con

def get_local_ip():
    """Détecte l'adresse IP locale du Mac pour le partage réseau."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def check_auth(request: Request, pin: str = Query(None)):
    """Vérifie l'authentification par cookie, en-tête ou query parameter."""
    auth_pin = pin or request.cookies.get("auth_pin") or request.headers.get("X-Access-PIN")
    if not auth_pin or auth_pin.strip().upper() != CURRENT_PIN.strip().upper():
        raise HTTPException(status_code=401, detail="Authentification requise. Code PIN manquant ou invalide.")
    return True

@app.post("/api/verify_pin")
async def verify_pin(request: Request, response: Response):
    data = await request.json()
    entered_pin = str(data.get("pin", "")).strip().upper()
    if entered_pin == CURRENT_PIN.strip().upper():
        response.set_cookie(key="auth_pin", value=CURRENT_PIN, max_age=86400 * 30, httponly=False)
        return {"status": "ok", "authenticated": True}
    return JSONResponse(status_code=401, content={"status": "error", "message": "Code PIN incorrect."})

@app.get("/api/stats")
def api_stats(_: bool = Depends(check_auth)):
    con = get_db()
    try:
        v_info, f_info, _ = stats(con)
        
        # Répartition par catégories
        cat_rows = con.execute("SELECT category, COUNT(*) cnt, SUM(size) sz FROM files GROUP BY category").fetchall()
        categories = [{
            "category": r["category"] or "autre",
            "count": r["cnt"],
            "size": r["sz"] or 0,
            "human_size": human_size(r["sz"] or 0)
        } for r in cat_rows]

        # Top 10 disques
        vol_rows = con.execute("SELECT name, file_count, total_size FROM volumes ORDER BY total_size DESC LIMIT 10").fetchall()
        volumes = [{
            "name": r["name"],
            "files": r["file_count"],
            "size": r["total_size"],
            "human_size": human_size(r["total_size"] or 0)
        } for r in vol_rows]

        return {
            "volumes_count": v_info["n"] if v_info else 0,
            "files_count": f_info["n"] if f_info else 0,
            "total_size": f_info["s"] if f_info else 0,
            "files_human_size": human_size(f_info["s"] if f_info else 0),
            "categories": categories,
            "top_volumes": volumes
        }
    except Exception as e:
        import traceback
        error_msg = traceback.format_exc()
        raise HTTPException(status_code=500, detail=error_msg)
    finally:
        con.close()


@app.get("/api/search")
def api_search(
    q: str = Query("", description="Terme de recherche"),
    category: str = Query("toutes", description="Filtrer par catégorie"),
    volume: str = Query(None, description="Filtrer par disque"),
    limit: int = Query(100, ge=1, le=500),
    _: bool = Depends(check_auth)
):
    con = get_db()
    try:
        vols = [volume] if volume else None
        rows = search_files(con, text=q, category=category, volume_ids=vols)
        
        results = []
        for r in rows[:limit]:
            results.append({
                "id": r["id"],
                "name": r["name"],
                "rel_path": r["rel_path"],
                "folder": r["folder"],
                "size": r["size"] or 0,
                "human_size": human_size(r["size"] or 0),
                "category": r["category"] or "autre",
                "ext": r["ext"] or "",
                "volume_name": r["volume_name"] or "",
                "camera": r["camera"] or "",
                "codec": r["codec"] or "",
                "duration": r["duration"] or 0
            })
            
        return {
            "query": q,
            "total": len(rows),
            "returned": len(results),
            "results": results
        }
    except Exception as e:
        import traceback
        error_msg = traceback.format_exc()
        raise HTTPException(status_code=500, detail=error_msg)
    finally:
        con.close()


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0">
  <title>Repertoir Neuro Scan.AI (RNS.AI) — Accès Sécurisé</title>
  <style>
    :root {
      --bg: #0f172a; --card-bg: #1e293b; --card-border: #334155;
      --accent: #38bdf8; --accent-glow: rgba(56, 189, 248, 0.2);
      --text: #f8fafc; --text-muted: #94a3b8;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
    body { background: var(--bg); color: var(--text); padding-bottom: 60px; -webkit-tap-highlight-color: transparent; }
    
    header {
      background: rgba(30, 41, 59, 0.85); backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px);
      border-bottom: 1px solid var(--card-border); padding: 14px 20px;
      position: sticky; top: 0; z-index: 50; display: flex; align-items: center; justify-content: space-between;
    }
    .logo { font-weight: 800; font-size: 1.15rem; color: #fff; display: flex; align-items: center; gap: 8px; }
    .badge-ip { background: rgba(56, 189, 248, 0.15); color: var(--accent); padding: 4px 10px; border-radius: 20px; font-size: 0.75rem; font-weight: 600; border: 1px solid rgba(56, 189, 248, 0.3); }

    .container { max-width: 900px; margin: 0 auto; padding: 16px; }

    /* Modal PIN */
    #auth-overlay {
      position: fixed; inset: 0; background: rgba(15, 23, 42, 0.95); backdrop-filter: blur(8px);
      z-index: 100; display: flex; align-items: center; justify-content: center; padding: 20px;
    }
    .auth-card {
      background: var(--card-bg); border: 1px solid var(--card-border); border-radius: 20px;
      padding: 30px; width: 100%; max-width: 380px; text-align: center; box-shadow: 0 10px 40px rgba(0,0,0,0.5);
    }
    .auth-card h2 { font-size: 1.4rem; margin-bottom: 10px; }
    .auth-card p { font-size: 0.85rem; color: var(--text-muted); margin-bottom: 24px; line-height: 1.4; }
    .pin-input {
      width: 100%; font-size: 1.6rem; letter-spacing: 6px; text-align: center; text-transform: uppercase;
      background: rgba(15, 23, 42, 0.8); border: 2px solid var(--accent); border-radius: 12px;
      color: #fff; padding: 12px; margin-bottom: 20px; outline: none; font-weight: 700;
    }
    .btn-pin {
      width: 100%; background: var(--accent); color: #0f172a; border: none; border-radius: 12px;
      padding: 14px; font-size: 1rem; font-weight: 700; cursor: pointer;
    }
    .pin-error { color: #f87171; font-size: 0.85rem; margin-top: 12px; display: none; }

    /* Stats Grid */
    .stats-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-bottom: 20px; }
    .stat-card {
      background: var(--card-bg); border: 1px solid var(--card-border); border-radius: 14px;
      padding: 14px; text-align: center;
    }
    .stat-num { font-size: 1.3rem; font-weight: 800; color: var(--accent); }
    .stat-label { font-size: 0.75rem; color: var(--text-muted); margin-top: 2px; }
    
    /* Search Box */
    .search-box {
      background: var(--card-bg); border: 1px solid var(--card-border); border-radius: 16px;
      padding: 16px; margin-bottom: 20px; display: flex; flex-direction: column; gap: 12px;
      box-shadow: 0 4px 24px -1px rgba(0,0,0,0.3);
    }
    .input-row { display: flex; gap: 10px; }
    .search-input {
      flex: 1; background: rgba(15, 23, 42, 0.6); border: 1px solid var(--card-border);
      border-radius: 10px; padding: 12px 16px; color: var(--text); font-size: 1rem; outline: none;
    }
    .search-input:focus { border-color: var(--accent); box-shadow: 0 0 0 3px var(--accent-glow); }
    .btn-search {
      background: var(--accent); color: #0f172a; border: none; border-radius: 10px;
      padding: 0 20px; font-weight: 700; cursor: pointer; transition: opacity 0.2s;
    }
    .btn-search:hover { opacity: 0.9; }
    
    /* Filters */
    .filter-pills { display: flex; gap: 8px; overflow-x: auto; padding-bottom: 4px; }
    .pill {
      background: rgba(255,255,255,0.05); border: 1px solid var(--card-border); color: var(--text-muted);
      border-radius: 20px; padding: 6px 14px; font-size: 0.8rem; cursor: pointer; white-space: nowrap;
      transition: all 0.2s;
    }
    .pill.active { background: var(--accent); color: #0f172a; font-weight: 600; border-color: var(--accent); }
    
    /* Results */
    .results-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; font-size: 0.85rem; color: var(--text-muted); }
    .file-list { display: flex; flex-direction: column; gap: 8px; }
    .file-item {
      background: var(--card-bg); border: 1px solid var(--card-border); border-radius: 12px;
      padding: 12px 16px; display: flex; align-items: center; justify-content: space-between; gap: 12px;
    }
    .file-main { overflow: hidden; }
    .file-name { font-weight: 600; font-size: 0.95rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .file-sub { font-size: 0.75rem; color: var(--text-muted); margin-top: 3px; display: flex; gap: 10px; align-items: center; }
    .badge-vol { background: rgba(255,255,255,0.1); padding: 2px 6px; border-radius: 6px; }
    .file-meta { text-align: right; white-space: nowrap; }
    .file-size { font-weight: 700; font-size: 0.9rem; }
    .file-cat { font-size: 0.7rem; color: var(--accent); text-transform: uppercase; margin-top: 2px; }
  </style>
</head>
<body>
  <div id="auth-overlay">
    <div class="auth-card">
      <div style="font-size: 2.5rem; margin-bottom: 12px;">🔒</div>
      <h2>Accès Sécurisé</h2>
      <p>Entrez le code PIN affiché sur l'application de votre Mac pour accéder au catalogue.</p>
      <input type="text" id="pin-field" class="pin-input" placeholder="CODE PIN" maxlength="8" autofocus>
      <button class="btn-pin" onclick="submitPin()">Déverrouiller</button>
      <div id="pin-err" class="pin-error">Code PIN invalide. Vérifiez l'écran de votre Mac.</div>
    </div>
  </div>

  <header>
    <div class="logo">
      <img src="/assets/logo_dark.png" alt="RNS.AI" style="height: 36px; border-radius: 6px;">
      <span>Repertoir Neuro Scan.AI</span>
    </div>
    <span class="badge-ip" id="badge-ip">Réseau Local Sécurisé 🔒</span>
  </header>

  <div class="container">
    <div class="stats-grid" id="stats-grid">
      <div class="stat-card"><div class="stat-num" id="stat-vols">--</div><div class="stat-label">Disques</div></div>
      <div class="stat-card"><div class="stat-num" id="stat-files">--</div><div class="stat-label">Fichiers</div></div>
      <div class="stat-card"><div class="stat-num" id="stat-size">--</div><div class="stat-label">Stockage Total</div></div>
    </div>

    <div class="search-box">
      <div class="input-row">
        <input type="text" id="input-q" class="search-input" placeholder="Rechercher un fichier, dossier, rush..." autofocus>
        <button class="btn-search" onclick="doSearch()">Chercher</button>
      </div>
      <div class="filter-pills" id="pills-cat">
        <div class="pill active" onclick="setCategory(this, 'toutes')">Toutes</div>
        <div class="pill" onclick="setCategory(this, 'video')">🎥 Vidéos</div>
        <div class="pill" onclick="setCategory(this, 'image')">📷 Photos</div>
        <div class="pill" onclick="setCategory(this, 'audio')">🎵 Audios</div>
        <div class="pill" onclick="setCategory(this, 'projet')">🎬 Projets</div>
        <div class="pill" onclick="setCategory(this, 'logiciel')">💻 Logiciels</div>
        <div class="pill" onclick="setCategory(this, 'document')">📄 Documents</div>
        <div class="pill" onclick="setCategory(this, 'archive')">📦 Archives</div>
      </div>
    </div>

    <div class="results-header">
      <span id="results-count">Entrez un terme pour lancer la recherche</span>
      <span id="results-limit">Top 100</span>
    </div>

    <div class="file-list" id="file-list"></div>
  </div>

  <script>
    let currentCategory = 'toutes';
    
    // Auto-login si ?pin= est présent dans l'URL
    const urlParams = new URLSearchParams(window.location.search);
    const urlPin = urlParams.get('pin');
    if (urlPin) {
      document.getElementById('pin-field').value = urlPin;
      submitPin();
    }

    async function submitPin() {
      const pin = document.getElementById('pin-field').value.trim().toUpperCase();
      const err = document.getElementById('pin-err');
      err.style.display = 'none';

      try {
        const res = await fetch('/api/verify_pin', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ pin: pin })
        });
        if (res.ok) {
          document.getElementById('auth-overlay').style.display = 'none';
          loadStats();
          doSearch();
        } else {
          err.style.display = 'block';
        }
      } catch(e) {
        err.style.display = 'block';
      }
    }

    document.getElementById('pin-field').addEventListener('keyup', (e) => {
      if (e.key === 'Enter') submitPin();
    });

    async function loadStats() {
      try {
        const res = await fetch('/api/stats');
        if (res.status === 401) {
          document.getElementById('auth-overlay').style.display = 'flex';
          return;
        }
        const data = await res.json();
        if (data.detail) {
            console.error("Stats API Error:", data.detail);
            return;
        }
        document.getElementById('stat-vols').textContent = data.volumes_count;
        document.getElementById('stat-files').textContent = Number(data.files_count).toLocaleString();
        document.getElementById('stat-size').textContent = data.files_human_size;
      } catch(e) { console.error(e); }
    }

    function setCategory(el, cat) {
      document.querySelectorAll('#pills-cat .pill').forEach(p => p.classList.remove('active'));
      el.classList.add('active');
      currentCategory = cat;
      doSearch();
    }

    async function doSearch() {
      const q = document.getElementById('input-q').value.trim();
      const list = document.getElementById('file-list');
      const countLbl = document.getElementById('results-count');
      
      countLbl.textContent = 'Recherche en cours...';
      try {
        const url = `/api/search?q=${encodeURIComponent(q)}&category=${currentCategory}`;
        const res = await fetch(url);
        if (res.status === 401) {
          document.getElementById('auth-overlay').style.display = 'flex';
          return;
        }
        const data = await res.json();
        
        if (data.detail) {
            countLbl.textContent = 'Erreur API';
            list.innerHTML = `<div style="color: red; padding: 10px; white-space: pre-wrap;">${data.detail}</div>`;
            return;
        }

        countLbl.textContent = `${data.total} résultats trouvés`;
        list.innerHTML = '';
        
        if (data.results.length === 0) {
          list.innerHTML = '<div style="text-align:center; padding:30px; color:var(--text-muted)">Aucun fichier trouvé.</div>';
          return;
        }

        data.results.forEach(f => {
          const div = document.createElement('div');
          div.className = 'file-item';
          div.innerHTML = `
            <div class="file-main">
              <div class="file-name" title="${f.name}">${f.name}</div>
              <div class="file-sub">
                <span class="badge-vol">💾 ${f.volume_name}</span>
                <span>${f.rel_path}</span>
              </div>
            </div>
            <div class="file-meta">
              <div class="file-size">${f.human_size}</div>
              <div class="file-cat">${f.category}</div>
            </div>
          `;
          list.appendChild(div);
        });
      } catch(e) {
        countLbl.textContent = 'Erreur lors de la recherche';
        console.error(e);
      }
    }

    document.getElementById('input-q').addEventListener('keyup', (e) => {
      if (e.key === 'Enter') doSearch();
    });

    // Tentative initiale
    loadStats();
  </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
def home():
    return HTML_TEMPLATE


class WebServerManager:
    """Gestionnaire de cycle de vie sécurisé pour lancer et arrêter le serveur web depuis Tkinter."""
    def __init__(self, host="0.0.0.0", port=8000):
        self.host = host
        self.port = port
        self.server = None
        self.thread = None
        self.is_running = False

    def get_pin(self):
        global CURRENT_PIN
        return CURRENT_PIN

    def regenerate_pin(self):
        global CURRENT_PIN
        CURRENT_PIN = secrets.token_hex(3).upper()
        return CURRENT_PIN

    def start(self):
        if self.is_running:
            return
        self.is_running = True
        config = uvicorn.Config(app=app, host=self.host, port=self.port, log_level="warning")
        self.server = uvicorn.Server(config)
        self.thread = threading.Thread(target=self.server.run, daemon=True)
        self.thread.start()

    def stop(self):
        if not self.is_running or not self.server:
            return
        self.server.should_exit = True
        self.is_running = False

    def get_urls(self):
        local_ip = get_local_ip()
        pin = self.get_pin()
        return {
            "local": f"http://localhost:{self.port}",
            "local_authenticated": f"http://localhost:{self.port}/?pin={pin}",
            "network": f"http://{local_ip}:{self.port}",
            "network_authenticated": f"http://{local_ip}:{self.port}/?pin={pin}",
            "pin": pin
        }

server_manager = WebServerManager()
