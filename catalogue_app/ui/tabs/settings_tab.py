import os
import sys
import subprocess
import threading
import tkinter as tk
from tkinter import ttk, messagebox

from catalogue_app.ui.tabs.base_tab import BaseTab
from catalogue_app import settings_manager
from catalogue_app.settings_manager import (
    SETTINGS_FILE, save_settings, load_settings, get_global_categories
)
from catalogue_app.config import APP_NAME, DB_PATH
from catalogue_app.utils import human_size
from catalogue_app.db import tools_status
from catalogue_app.web_server import server_manager, get_local_ip
from catalogue_app.ai_chat import save_ai_config, load_ai_config


class SettingsTab(BaseTab):
    def __init__(self, parent, app, **kwargs):
        super().__init__(parent, app, **kwargs)

    def _build_ui(self):
        # Create a Canvas and a Scrollbar
        canvas = tk.Canvas(self, borderwidth=0, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

        def _on_canvas_configure(event):
            # Expand the inner frame to match the canvas width
            canvas.itemconfig(canvas_window, width=event.width)

        canvas.bind("<Configure>", _on_canvas_configure)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Mousewheel scrolling (macOS & Windows)
        def _on_mousewheel(event):
            # Only scroll if the cursor is within the SettingsTab
            x, y = self.winfo_pointerxy()
            widget_under_cursor = self.winfo_containing(x, y)
            if widget_under_cursor and str(self) in str(widget_under_cursor):
                canvas.yview_scroll(int(-1 * event.delta), "units")

        self.bind_all("<MouseWheel>", _on_mousewheel, add="+")

        f = scrollable_frame


        # Categories Settings Frame
        cat_frame = ttk.LabelFrame(f, text=" Apparence et Configuration ", padding=20)
        cat_frame.pack(fill="x", padx=20, pady=10)

        # --- Thème Chooser ---
        ttk.Label(cat_frame, text="Thème de l'application :").grid(row=0, column=0, sticky="w", pady=5)
        themes = ["cosmo", "flatly", "darkly", "cyborg", "superhero", "solar", "vapor", "pulse", "morph", "journal", "litera", "united", "minty"]
        if hasattr(self.app, "var_theme"):
            self.var_theme = self.app.var_theme
        else:
            self.var_theme = tk.StringVar(value="darkly")
        cmb_theme = ttk.Combobox(cat_frame, textvariable=self.var_theme, values=themes, state="readonly", width=20)
        cmb_theme.grid(row=0, column=1, sticky="w", pady=5, padx=10)
        cmb_theme.bind("<<ComboboxSelected>>", self.on_theme_change)

        # --- Map Style Chooser ---
        self.var_mapstyle = tk.StringVar(value="sunburst")
        ttk.Label(cat_frame, text="Style de la carte visuelle (Stockage) :").grid(row=1, column=0, sticky="w", pady=5)
        cmb_map = ttk.Combobox(cat_frame, textvariable=self.var_mapstyle, values=["treemap", "sunburst", "arbre"], state="readonly", width=20)
        cmb_map.grid(row=1, column=1, sticky="w", pady=5, padx=10)
        cmb_map.bind("<<ComboboxSelected>>", self.on_map_change)

        ttk.Label(cat_frame, text="Catégories et extensions globales:").grid(row=2, column=0, sticky="w", pady=(15, 5))
        ttk.Button(cat_frame, text="Éditer le fichier de configuration (JSON)", command=self.open_categories_editor).grid(row=3, column=0, sticky="w", pady=5)

        # --- Agent Skills / Prompts Editor ---
        skills_frame = ttk.LabelFrame(f, text=" 🧠 Personnalité des Agents IA (Skills) ", padding=20)
        skills_frame.pack(fill="x", padx=20, pady=10)

        ttk.Label(skills_frame, text="Sélectionnez un agent et éditez ses instructions / sa personnalité directement ici.",
                  wraplength=600).grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 10))

        self.agent_skill_files = {
            "🔍 Agent Archiviste (Recherche)": "skills_search_assistant.md",
            "📊 Agent Analyste (Dashboard)": "skills_dashboard_analyst.md",
            "🏷️ Agent Documentaliste (Tags)": "skills_tag_expert.md",
            "🧹 Agent Nettoyeur (Doublons)": "skills_duplicate_cleaner.md",
            "📁 Agent Chef de Projet": "skills_project_manager.md",
            "🪄 Agent Renommeur": "skills_renamer.md",
            "📥 Agent DIT (Ingestion)": "skills_dit_ingest.md",
        }
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.agents_dir = os.path.join(base_dir, "agents")
        if not os.path.isdir(self.agents_dir):
            self.agents_dir = os.path.join(os.path.dirname(__file__), "catalogue_app", "agents")

        ttk.Label(skills_frame, text="Agent :").grid(row=1, column=0, sticky="w", pady=5)
        self.var_skill_agent = tk.StringVar()
        cmb_skill = ttk.Combobox(skills_frame, textvariable=self.var_skill_agent,
                                 values=list(self.agent_skill_files.keys()), state="readonly", width=40)
        cmb_skill.grid(row=1, column=1, sticky="w", pady=5)

        self.txt_skill = tk.Text(skills_frame, height=8, wrap="word",
                                 font=("Menlo", 10), bg="#1e1e2e", fg="#cdd6f4",
                                 insertbackground="#cdd6f4")
        self.txt_skill.grid(row=2, column=0, columnspan=3, sticky="nsew", pady=5)
        skills_frame.grid_columnconfigure(1, weight=1)

        cmb_skill.bind("<<ComboboxSelected>>", self.load_skill)

        btn_save_skill = ttk.Button(skills_frame, text="💾 Enregistrer les Instructions", command=self.save_skill)
        btn_save_skill.grid(row=3, column=1, sticky="w", pady=5)

        ia_frame = ttk.LabelFrame(f, text=" Intelligence Artificielle (IA) ", padding=20)
        ia_frame.pack(fill="x", padx=20, pady=20)

        # Granularité
        ttk.Label(ia_frame, text="Activation de l'IA (Granulométrie) :",
                  font=("TkDefaultFont", 11, "bold")).grid(row=0, column=0, sticky="w", pady=(0, 10))
        self.var_ia_active = tk.BooleanVar(value=True)
        ttk.Checkbutton(ia_frame, text="Activer les fonctionnalités d'Intelligence Artificielle",
                        variable=self.var_ia_active).grid(row=0, column=1, sticky="w", pady=(0, 10))

        # Modèle LLM Texte
        ttk.Label(ia_frame, text="Modèle LLM Texte :").grid(row=1, column=0, sticky="w", pady=5)
        self.cmb_llm = ttk.Combobox(ia_frame, values=[
            "Automatique (Low-débit)",
            "Google",
            "Gemma",
            "Gemma 4",
            "Nomic Text Embedding",
            "Minitron",
            "Qwen"
        ], state="normal", width=40)
        self.cmb_llm.set("google/gemma-4-e4b")
        self.cmb_llm.grid(row=1, column=1, sticky="w", pady=5)

        # URL de l'API
        ttk.Label(ia_frame, text="URL de l'API (ex: http://localhost:1234/api/v1/chat):").grid(row=2, column=0, sticky="w", pady=5)
        self.var_api_url = tk.StringVar(value="http://127.0.0.1:1234/api/v1/chat")
        ttk.Entry(ia_frame, textvariable=self.var_api_url, width=42).grid(row=2, column=1, sticky="w", pady=5)

        # Intégrations MCP LM Studio 0.4.0+
        ttk.Label(ia_frame, text="Serveurs MCP LM Studio (ex: mcp/playwright):").grid(row=3, column=0, sticky="w", pady=5)
        self.var_mcp = tk.StringVar(value="")
        ttk.Entry(ia_frame, textvariable=self.var_mcp, width=42).grid(row=3, column=1, sticky="w", pady=5)

        # Info
        ttk.Label(ia_frame, text="Tapez l'ID des serveurs MCP séparés par des virgules (ex: mcp/playwright).",
                  foreground="gray").grid(row=4, column=1, sticky="w", pady=(0, 15))

        ttk.Button(ia_frame, text="Enregistrer les paramètres IA",
                   command=self.save_ai).grid(row=5, column=1, sticky="w")

        # Load current values
        try:
            cfg = load_ai_config()
            self.var_ia_active.set(cfg.get("enabled_chat", True))
            self.var_api_url.set(cfg.get("url", "http://127.0.0.1:1234/api/v1/chat"))
            self.cmb_llm.set(cfg.get("model", "google/gemma-4-e4b"))
            mcp_val = cfg.get("mcp_integrations", [])
            if isinstance(mcp_val, list):
                self.var_mcp.set(", ".join(str(x) for x in mcp_val))
            else:
                self.var_mcp.set(str(mcp_val))
        except Exception:
            pass

        # NAS Backup Frame
        nas_frame = ttk.LabelFrame(f, text=" Serveur NAS & Sauvegarde ", padding=20)
        nas_frame.pack(fill="x", padx=20, pady=10)

        ttk.Label(nas_frame, text="Sauvegardez instantanément votre catalogue (Base de données) sur le serveur QNAP.").grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))

        self.btn_nas = ttk.Button(nas_frame, text="☁️ Sauvegarder sur le NAS", command=self.trigger_backup)
        self.btn_nas.grid(row=1, column=0, sticky="w", pady=5)

        # Cadre Serveur Web & Mobile
        web_frame = ttk.LabelFrame(f, text=" Serveur Web & Accès Mobile ", padding=20)
        web_frame.pack(fill="x", padx=20, pady=10)

        urls = server_manager.get_urls()

        ttk.Label(web_frame, text=f"• Accès Local : {urls['local']}\n• Accès Réseau Wi-Fi / Mobile : {urls['network']}\n• Documentation Swagger API : {urls['local']}/docs",
                  font=("TkDefaultFont", 10)).pack(anchor="w", pady=(0, 10))

        btn_st_web = ttk.Button(web_frame, text="Démarrer / Arrêter le serveur Web", command=self.toggle_web_from_settings)
        btn_st_web.pack(side="left", padx=(0, 10))

        self.lbl_web_st = ttk.Label(web_frame, text="Serveur ACTIF 🟢" if server_manager.is_running else "Serveur ARRÊTÉ 🔴", font=("TkDefaultFont", 10, "bold"))
        self.lbl_web_st.pack(side="left")

        # Cadre Base de données & Maintenance
        db_frame = ttk.LabelFrame(f, text=" Base de Données & Maintenance ", padding=20)
        db_frame.pack(fill="x", padx=20, pady=10)

        db_size = human_size(os.path.getsize(DB_PATH)) if os.path.exists(DB_PATH) else "--"
        self.lbl_db_info = ttk.Label(db_frame, text=f"Emplacement : {DB_PATH}\nTaille du catalogue SQLite : {db_size}")
        self.lbl_db_info.pack(anchor="w", pady=(0, 10))

        ttk.Button(db_frame, text="⚡ Défragmenter et Optimiser (VACUUM)", command=self.do_vacuum).pack(side="left", padx=(0, 10))
        ttk.Button(db_frame, text="💾 Créer une Sauvegarde Immédiate", command=self.do_backup_now).pack(side="left")

        # Cadre Mises à jour GitHub (1-Clic)
        upd_frame = ttk.LabelFrame(f, text=" 🔄 Mises à Jour Automatiques (GitHub) ", padding=20)
        upd_frame.pack(fill="x", padx=20, pady=10)

        from catalogue_app.updater import get_current_version_info, set_configured_repo_url
        vinfo = get_current_version_info()
        self.lbl_ver_info = ttk.Label(
            upd_frame,
            text=f"Version installée : V{vinfo['version']}  (commit : {vinfo['commit']} — branche : {vinfo['branch']})   |   Base locale isolée : {DB_PATH}",
            font=("TkDefaultFont", 10, "bold"),
            foreground="#a6e3a1"
        )
        self.lbl_ver_info.grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 8))

        ttk.Label(upd_frame, text="Dépôt GitHub (URL) :").grid(row=1, column=0, sticky="w", pady=4)
        self.var_github_url = tk.StringVar(value=vinfo.get("repo_url", ""))
        ttk.Entry(upd_frame, textvariable=self.var_github_url, width=52).grid(row=1, column=1, sticky="w", padx=8, pady=4)

        def _save_repo():
            ok, msg = set_configured_repo_url(self.var_github_url.get().strip())
            if ok:
                messagebox.showinfo(APP_NAME, msg)
            else:
                messagebox.showerror(APP_NAME, msg)

        ttk.Button(upd_frame, text="💾 Enregistrer l'URL GitHub", command=_save_repo).grid(row=1, column=2, sticky="w", padx=4, pady=4)

        btn_upd_row = ttk.Frame(upd_frame)
        btn_upd_row.grid(row=2, column=0, columnspan=3, sticky="w", pady=(8, 0))
        ttk.Button(
            btn_upd_row,
            text="🔍 Vérifier et Installer les Mises à Jour depuis GitHub",
            command=lambda: self.app.check_and_prompt_update(interactive=True)
        ).pack(side="left", padx=(0, 10))

    def on_theme_change(self, event=None):
        theme = self.var_theme.get()
        if hasattr(self.app, "style"):
            self.app.style.theme_use(theme)
        elif hasattr(self, "style"):
            self.app.style.theme_use(theme)

    def on_map_change(self, event=None):
        treemap = getattr(self.app, "dash_treemap", None)
        if not treemap and hasattr(self.app, "tab_dash") and hasattr(self.app.tab_dash, "dash_treemap"):
            treemap = self.app.tab_dash.dash_treemap
        if treemap and hasattr(treemap, "set_view_style"):
            treemap.set_view_style(self.var_mapstyle.get())
        elif hasattr(self, "dash_treemap") and hasattr(self.app.dash_treemap, "set_view_style"):
            self.app.dash_treemap.set_view_style(self.var_mapstyle.get())

    def open_categories_editor(self):
        settings = load_settings()
        if "global_categories" not in settings:
            settings["global_categories"] = get_global_categories()
        save_settings(settings)

        if sys.platform == "darwin":
            subprocess.call(["open", SETTINGS_FILE])
        elif os.name == "nt":
            os.startfile(SETTINGS_FILE)
        else:
            subprocess.call(["xdg-open", SETTINGS_FILE])

    def load_skill(self, _e=None):
        name = self.var_skill_agent.get()
        fname = self.agent_skill_files.get(name)
        if not fname:
            return
        path = os.path.join(self.agents_dir, fname)
        self.txt_skill.delete("1.0", "end")
        try:
            with open(path, "r", encoding="utf-8") as fh:
                self.txt_skill.insert("1.0", fh.read())
        except FileNotFoundError:
            self.txt_skill.insert("1.0", f"# Compétences & Directives\n\n(Fichier non trouvé : {fname})")

    def save_skill(self):
        name = self.var_skill_agent.get()
        fname = self.agent_skill_files.get(name)
        if not fname:
            messagebox.showwarning(APP_NAME, "Sélectionnez d'abord un agent.")
            return
        path = os.path.join(self.agents_dir, fname)
        try:
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(self.txt_skill.get("1.0", "end").rstrip() + "\n")
            messagebox.showinfo(APP_NAME, f"Instructions de « {name} » enregistrées !\n\nElles prendront effet à la prochaine question posée à cet agent.")
        except Exception as e:
            messagebox.showerror(APP_NAME, f"Erreur : {e}")

    def save_ai(self):
        try:
            cfg = load_ai_config()
            cfg["enabled_chat"] = self.var_ia_active.get()
            cfg["url"] = self.var_api_url.get().strip()
            model_map = {
                "Automatique (Low-débit)": "google/gemma-4-e4b",
                "Google": "google/gemma-4-e4b",
                "Gemma": "google/gemma-4-e4b",
                "Gemma 4": "google/gemma-4-e4b",
                "Nomic Text Embedding": "nomic-ai/nomic-embed-text-v1.5",
                "Minitron": "nvidia/minitron-8b-base",
                "Qwen": "qwen/qwen-2.5-coder-3b",
            }
            chosen = self.cmb_llm.get().strip()
            # If the user typed a custom model ID, use it directly, else use the mapped value
            cfg["model"] = model_map.get(chosen, chosen)
            
            # Traiter la liste des intégrations MCP
            raw_mcp = getattr(self, "var_mcp", None)
            if raw_mcp:
                mcp_str = raw_mcp.get().strip()
                if mcp_str:
                    cfg["mcp_integrations"] = [x.strip() for x in mcp_str.split(",") if x.strip()]
                else:
                    cfg["mcp_integrations"] = []

            save_ai_config(cfg)
            messagebox.showinfo(APP_NAME, "Paramètres IA enregistrés.")
        except Exception as e:
            messagebox.showerror(APP_NAME, f"Erreur : {e}")

    def trigger_backup(self):
        self.btn_nas.config(text="⏳ Sauvegarde en cours...", state="disabled")
        self.update_idletasks()

        def worker():
            try:
                from catalogue_app.nas_backup import backup_database_to_nas
                success, msg = backup_database_to_nas()
                if success:
                    self.after(0, lambda m=msg: messagebox.showinfo("Sauvegarde NAS", m))
                else:
                    self.after(0, lambda m=msg: messagebox.showerror("Erreur NAS", m))
            except Exception as e:
                err_msg = str(e)
                self.after(0, lambda err=err_msg: messagebox.showerror("Erreur", err))
            finally:
                self.after(0, lambda: self.btn_nas.config(text="☁️ Sauvegarder sur le NAS", state="normal"))

        threading.Thread(target=worker, daemon=True).start()

    def toggle_web_from_settings(self):
        if hasattr(self.app, "_toggle_web_server"):
            self.app._toggle_web_server()
        elif hasattr(self, "_toggle_web_server"):
            self.app._toggle_web_server()
        if hasattr(self, "lbl_web_st"):
            self.lbl_web_st.config(text="Serveur ACTIF 🟢" if server_manager.is_running else "Serveur ARRÊTÉ 🔴")

    def do_vacuum(self):
        try:
            if hasattr(self.app, "status"):
                self.app.status.set("Optimisation de la base de données (VACUUM)...")
            elif hasattr(self, "status"):
                self.app.status.set("Optimisation de la base de données (VACUUM)...")
            self.update_idletasks()
            self.app.con.execute("VACUUM")
            new_size = human_size(os.path.getsize(DB_PATH)) if os.path.exists(DB_PATH) else "--"
            if hasattr(self, "lbl_db_info"):
                self.lbl_db_info.config(text=f"Emplacement : {DB_PATH}\nTaille du catalogue SQLite : {new_size}")
            messagebox.showinfo(APP_NAME, f"Base optimisée avec succès !\nNouvelle taille : {new_size}")
        except Exception as e:
            messagebox.showerror(APP_NAME, f"Erreur VACUUM : {e}")
        finally:
            if hasattr(self.app, "status"):
                self.app.status.set(tools_status())
            elif hasattr(self, "status"):
                self.app.status.set(tools_status())

    def do_backup_now(self):
        try:
            from catalogue_app.db import backup_database
            backup_database()
            messagebox.showinfo(APP_NAME, "Sauvegarde compressée créée dans le dossier Backups !")
        except Exception as e:
            messagebox.showerror(APP_NAME, f"Erreur : {e}")

    def refresh(self):
        """Rafraîchit l'état des composants des paramètres (serveur web, taille DB)."""
        try:
            if hasattr(self, "lbl_web_st"):
                self.lbl_web_st.config(text="Serveur ACTIF 🟢" if server_manager.is_running else "Serveur ARRÊTÉ 🔴")
            if hasattr(self, "lbl_db_info") and os.path.exists(DB_PATH):
                db_size = human_size(os.path.getsize(DB_PATH))
                self.lbl_db_info.config(text=f"Emplacement : {DB_PATH}\nTaille du catalogue SQLite : {db_size}")
        except Exception:
            pass
