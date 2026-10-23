import os
import sys
import json
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

from catalogue_app.ui.tabs.base_tab import BaseTab
from catalogue_app.ui.components import MultiSelectMenu
from catalogue_app.config import *
from catalogue_app.utils import *
from catalogue_app.db import *
from catalogue_app.queries import *


class DashboardTab(BaseTab):
    def _build_ui(self):
        f = self
        
        # Top Banner
        self.dash_banner = ttk.Label(f, text="Chargement des statistiques...", font=("TkDefaultFont", 18, "bold"), anchor="center")
        self.dash_banner.pack(fill="x", pady=10)
        
        # Visualisations PanedWindow
        self.dash_paned = ttk.Panedwindow(f, orient="horizontal")
        self.dash_paned.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Left: Treemap
        try:
            from catalogue_app.treemap import TreemapFrame
            self.dash_treemap = TreemapFrame(self.dash_paned, self.app.con, volume_ids=[])
            self.dash_paned.add(self.dash_treemap, weight=3)
        except Exception as e:
            pass
            
        # Right: Matplotlib Analytics (Evolution & Word Cloud)
        right_frame = ttk.Frame(self.dash_paned)
        self.dash_paned.add(right_frame, weight=1)
        try:
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
            from matplotlib.figure import Figure
            self.fig = Figure(figsize=(4, 6), dpi=100)
            self.fig.subplots_adjust(bottom=0.1, hspace=0.3)
            self.canvas = FigureCanvasTkAgg(self.fig, master=right_frame)
            self.canvas.get_tk_widget().pack(fill="both", expand=True)
        except Exception as e:
            pass
        
        # Actions Rapides
        act_frame = ttk.LabelFrame(f, text=" Actions Rapides ", padding=20)
        act_frame.pack(fill="x", padx=20, pady=10)
        
        ttk.Button(act_frame, text="🔍 Lancer un Scan", command=lambda: (self.app.nb.select(self.app.tab_stockage_main), self.app.nb_stockage.select(self.app.tab_scan))).pack(side="left", padx=10)
        ttk.Button(act_frame, text="👯 Chercher des Doublons", command=lambda: (self.app.nb.select(self.app.tab_ia_main), self.app.nb_ia.select(self.app.tab_dup))).pack(side="left", padx=10)
        ttk.Button(act_frame, text="📅 Calendrier de Tournage", command=self.app._show_shooting_timeline).pack(side="left", padx=10)
        
        self.btn_enrich = ttk.Button(act_frame, text="🌙 Lancer l'Auto-étiquetage IA", command=self._toggle_ai_enricher)
        self.btn_enrich.pack(side="left", padx=10)
        
        ttk.Button(act_frame, text="📖 Guide d'Utilisation", command=self.app.open_user_guide).pack(side="left", padx=10)
        
        # IA Analyst Frame
        ai_frame = ttk.LabelFrame(f, text=" Agent Analyste IA ", padding=10)
        ai_frame.pack(fill="x", padx=20, pady=5)
        
        self.txt_analyst = tk.Text(ai_frame, height=4, wrap="word", bg="#1e1e2e", fg="#a6e3a1", font=("TkDefaultFont", 11, "italic"))
        self.txt_analyst.pack(fill="x", expand=True, side="left", padx=(0,10))
        self.txt_analyst.insert("1.0", "Cliquez sur 'Générer un Insight' pour que l'agent analyse vos données...")
        self.txt_analyst.config(state="disabled")
        
        def get_insight():
            self.btn_insight.config(text="Analyse en cours...", state="disabled")
            self.update_idletasks()

            def _update_txt(t):
                import re as re_mod, json
                match = re_mod.search(r'```action\s*(.*?)\s*```', t, re_mod.DOTALL)
                action_data = None
                if match:
                    try:
                        action_data = json.loads(match.group(1))
                        t = t.replace(match.group(0), "\n[Action Détectée : Proposition de Rapport]")
                    except: pass

                self.txt_analyst.config(state="normal")
                self.txt_analyst.delete("1.0", "end")
                self.txt_analyst.insert("1.0", t)
                self.txt_analyst.config(state="disabled")

                if action_data and action_data.get("command") == "EXPORT_AUDIT_REPORT":
                    title = action_data.get("title", "Bilan_Stockage")
                    if messagebox.askyesno("Agent Analyste", "L'agent propose d'exporter un Rapport d'Audit Complet sur votre stockage en Markdown.\n\nExporter le rapport ?"):
                        p = filedialog.asksaveasfilename(
                            defaultextension=".md",
                            initialfile=f"{title}.md",
                            filetypes=[("Document Markdown", "*.md"), ("Fichier Texte", "*.txt")]
                        )
                        if p:
                            try:
                                from catalogue_app.queries import stats
                                v, fl, by_cat = stats(self.app.con)
                                with open(p, "w", encoding="utf-8") as fh:
                                    fh.write(f"# 📊 Rapport d'Audit & Santé du Stockage\n\n")
                                    fh.write(f"- Date d'évaluation : {time.strftime('%Y-%m-%d %H:%M')}\n")
                                    fh.write(f"- Disques catalogués : {v['n'] if v else 0}\n")
                                    fh.write(f"- Fichiers totaux : {human_count(fl['n'] if fl else 0)}\n")
                                    fh.write(f"- Volume total : {human_size(fl['s'] if fl else 0)}\n\n")
                                    fh.write("### 🗂️ Répartition par catégorie :\n")
                                    for c in by_cat:
                                        fh.write(f"- **{c['category']}** : {human_count(c['n'])} fichiers ({human_size(c['s'])})\n")
                                    fh.write(f"\n### 🤖 Analyse & Recommandations de l'Agent :\n\n{t}\n")
                                if messagebox.askyesno("Succès", "Rapport d'audit enregistré !\n\nL'afficher dans le Finder ?"):
                                    subprocess.Popen(["open", "-R", p])
                            except Exception as err:
                                messagebox.showerror("Erreur", f"Échec de l'export : {err}")

            def worker():
                local_con = None
                try:
                    import sqlite3
                    from catalogue_app.config import DB_PATH
                    from catalogue_app.agents import AnalystAgent
                    local_con = sqlite3.connect(DB_PATH)
                    local_con.row_factory = sqlite3.Row
                    agent = AnalystAgent(local_con)
                    resp = agent.ask_insight()
                    self.after(0, lambda r=resp: _update_txt(r))
                except Exception as e:
                    err_msg = str(e)
                    self.after(0, lambda err=err_msg: _update_txt(f"Erreur Agent: {err}"))
                finally:
                    if local_con is not None:
                        try:
                            local_con.close()
                        except Exception:
                            pass
                    self.after(0, lambda: self.btn_insight.config(text="🤖 Générer un Insight", state="normal"))

            import threading
            threading.Thread(target=worker, daemon=True).start()
            
        self.btn_insight = ttk.Button(ai_frame, text="🤖 Générer un Insight", command=get_insight)
        self.btn_insight.pack(side="right")
        
        self.lbl_enrich_status = ttk.Label(act_frame, text="IA en pause", foreground="gray")
        self.lbl_enrich_status.pack(side="left", padx=10)
        
        ttk.Label(act_frame, text="🗺️ Treemap Disques:").pack(side="left", padx=(10, 2))
        self.cmb_dashtree = MultiSelectMenu(act_frame, text="(tous)")
        self.cmb_dashtree.command = self._update_dashtree
        self.cmb_dashtree.pack(side="left")
        self.btn_web = ttk.Button(act_frame, text="🌐 Lancer Accès Web & Mobile", command=self._toggle_web_server)
        self.btn_web.pack(side="left", padx=10)
        self.btn_update = ttk.Button(act_frame, text="🔄 Mise à jour", command=lambda: self.app.check_and_prompt_update(interactive=True))
        self.btn_update.pack(side="left", padx=6)
        
        # Statistiques Cards
        self.cards_frame = ttk.Frame(f)
        self.cards_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        self.card_video = ttk.Button(self.cards_frame, text="🎬 Vidéos\n0 fichier\n0 B", command=lambda: self._quick_filter("Vidéo"))
        self.card_video.pack(side="left", fill="both", expand=True, padx=5)
        
        self.card_audio = ttk.Button(self.cards_frame, text="🎵 Audios\n0 fichier\n0 B", command=lambda: self._quick_filter("Audio"))
        self.card_audio.pack(side="left", fill="both", expand=True, padx=5)
        
        self.card_photo = ttk.Button(self.cards_frame, text="📷 Photos\n0 fichier\n0 B", command=lambda: self._quick_filter("Photo"))
        self.card_photo.pack(side="left", fill="both", expand=True, padx=5)
        
        self.card_project = ttk.Button(self.cards_frame, text="🎨 Projets\n0 fichier\n0 B", command=lambda: self._quick_filter("Projet"))
        self.card_project.pack(side="left", fill="both", expand=True, padx=5)
        
        self.card_software = ttk.Button(self.cards_frame, text="💾 Logiciels\n0 fichier\n0 B", command=lambda: self._quick_filter("Logiciel"))
        self.card_software.pack(side="left", fill="both", expand=True, padx=5)
        
        self.card_other = ttk.Button(self.cards_frame, text="📄 Autres\n0 fichier\n0 B", command=lambda: self._quick_filter("Autre"))
        self.card_other.pack(side="left", fill="both", expand=True, padx=5)
        
    def _update_dashtree(self):
        if hasattr(self, "dash_treemap"):
            self.dash_treemap.set_volumes(self.cmb_dashtree.get_selected())

    def _toggle_web_server(self):
        import webbrowser
        import subprocess
        from catalogue_app.web_server import server_manager
        if not server_manager.is_running:
            server_manager.start()
            self.btn_web.config(text="🌐 Accès Web : ACTIF (Arrêter)")
            urls = server_manager.get_urls()
            pin = urls.get("pin", "")
            msg = (
                f"🔒 Le serveur Web & Mobile Sécurisé est ACTIF ! 🚀\n\n"
                f"🔑 CODE PIN DE SÉCURITÉ : {pin}\n\n"
                f"• Accès Smartphone / Tablette (même Wi-Fi) :\n"
                f"  {urls['network']}\n\n"
                f"• Lien direct sécurisé (avec PIN pré-rempli) :\n"
                f"  {urls['network_authenticated']}\n\n"
                f"Personne sur votre réseau ne peut accéder au catalogue sans ce code PIN.\n\n"
                f"Souhaitez-vous ouvrir l'interface sur votre Mac ?"
            )
            ans = messagebox.askyesno(APP_NAME, msg)
            if ans:
                webbrowser.open(urls["local_authenticated"])
        else:
            server_manager.stop()
            self.btn_web.config(text="🌐 Lancer Accès Web & Mobile")
            messagebox.showinfo(APP_NAME, "Le serveur Web a été arrêté.")

    def _quick_filter(self, category):
        self.app.nb.select(self.app.tab_search)
        if hasattr(self.app, "search_tab") and hasattr(self.app.search_tab, "cmb_cat"):
            self.app.search_tab.cmb_cat.set("toutes")
            if category == "Vidéo":
                self.app.search_tab.cmb_cat.set("video")
            elif category == "Audio":
                self.app.search_tab.cmb_cat.set("audio")
            elif category == "Photo":
                self.app.search_tab.cmb_cat.set("image")
            elif category == "Projet":
                self.app.search_tab.cmb_cat.set("projet")
            elif category == "Logiciel":
                self.app.search_tab.cmb_cat.set("logiciel")
        self.app._do_search()

    def _toggle_ai_enricher(self):
        if not hasattr(self, "ai_enricher"):
            from catalogue_app.ai_enricher import AIEnricher
            from catalogue_app.db import connect
            
            def progress_cb(msg, cur, tot):
                def _update(m=msg):
                    try:
                        if hasattr(self, "lbl_enrich_status") and self.lbl_enrich_status.winfo_exists():
                            self.lbl_enrich_status.config(text=m)
                    except Exception:
                        pass
                self.after(0, _update)
                    
            self.ai_enricher = AIEnricher(connect, progress_cb)
            
        if getattr(self.ai_enricher, "is_running", False):
            self.ai_enricher.stop()
            self.btn_enrich.config(text="🌙 Lancer l'Auto-étiquetage IA")
            if hasattr(self, "lbl_enrich_status") and self.lbl_enrich_status.winfo_exists():
                self.lbl_enrich_status.config(text="IA en pause")
        else:
            if hasattr(self, "lbl_enrich_status") and self.lbl_enrich_status.winfo_exists():
                self.lbl_enrich_status.config(text="Démarrage de l'analyse...")
            self.ai_enricher.start()
            self.btn_enrich.config(text="⏹ Arrêter l'Auto-étiquetage IA")

    def refresh(self):
        if getattr(self, "_refreshing_dash", False):
            return
        self._refreshing_dash = True

        def _bg():
            local_con = None
            try:
                local_con = connect()
                v, fl, by_cat = stats(local_con)
                v_count = v["n"] if v else 0
                f_count = fl["n"] if fl else 0
                f_size = fl["s"] if fl else 0

                cat_map = {
                    "video": "Vidéo", "image": "Photo", "audio": "Audio",
                    "projet": "Projet", "logiciel": "Logiciel", "archive": "Archive",
                    "document": "Doc", "3d": "3D", "code": "Code", "autre": "Autre"
                }
                data = {}
                for r in by_cat:
                    cname = cat_map.get(r["category"], "Autre")
                    if cname not in data:
                        data[cname] = [0, 0]
                    data[cname][0] += (r["n"] or 0)
                    data[cname][1] += (r["s"] or 0)

                years = local_con.execute(
                    "SELECT strftime('%Y', datetime(mtime, 'unixepoch')) as yr, sum(size) as sz "
                    "FROM files WHERE mtime > 0 GROUP BY yr ORDER BY yr"
                ).fetchall()
                cur_year = datetime.now().year
                years = [{"yr": y["yr"], "sz": y["sz"]} for y in years if y["yr"] and 2000 <= int(y["yr"]) <= cur_year]

                top_tags = local_con.execute(
                    "SELECT t.name, COUNT(ft.file_id) as cnt "
                    "FROM tags t JOIN file_tags ft ON t.id = ft.tag_id "
                    "WHERE t.name LIKE 'ia:%' OR t.kind='ia' "
                    "GROUP BY t.id ORDER BY cnt DESC LIMIT 8"
                ).fetchall()
                top_tags = [{"name": t["name"], "cnt": t["cnt"]} for t in top_tags]

                self.after(0, lambda: self._apply_refresh_ui(v_count, f_count, f_size, data, years, top_tags))
            except Exception as e:
                print("Error in dashboard bg:", e)
                self._refreshing_dash = False
            finally:
                if local_con is not None:
                    try:
                        local_con.close()
                    except Exception:
                        pass

        threading.Thread(target=_bg, daemon=True).start()

    def _apply_refresh_ui(self, v_count, f_count, f_size, data, years, top_tags):
        try:
            if not self.winfo_exists():
                return
            self.dash_banner.config(text=f"Total Catalogue : {v_count} Disques — {human_count(f_count)} Fichiers — {human_size(f_size)}")

            v_vid = data.get("Vidéo", (0, 0))
            self.card_video.config(text=f"🎬 Vidéos\n{human_count(v_vid[0])} fichiers\n{human_size(v_vid[1])}")

            v_aud = data.get("Audio", (0, 0))
            self.card_audio.config(text=f"🎵 Audios\n{human_count(v_aud[0])} fichiers\n{human_size(v_aud[1])}")

            v_pho = data.get("Photo", (0, 0))
            self.card_photo.config(text=f"📷 Photos\n{human_count(v_pho[0])} fichiers\n{human_size(v_pho[1])}")

            v_prj = data.get("Projet", (0, 0))
            self.card_project.config(text=f"🎨 Projets\n{human_count(v_prj[0])} fichiers\n{human_size(v_prj[1])}")

            v_sof = data.get("Logiciel", (0, 0))
            self.card_software.config(text=f"💾 Logiciels\n{human_count(v_sof[0])} fichiers\n{human_size(v_sof[1])}")

            v_oth_cnt = sum(v[0] for k, v in data.items() if k not in ("Vidéo", "Audio", "Photo", "Projet", "Logiciel"))
            v_oth_sz = sum(v[1] for k, v in data.items() if k not in ("Vidéo", "Audio", "Photo", "Projet", "Logiciel"))
            self.card_other.config(text=f"📄 Autres\n{human_count(v_oth_cnt)} fichiers\n{human_size(v_oth_sz)}")

            if hasattr(self, "fig") and hasattr(self, "canvas"):
                try:
                    self.fig.clear()
                    self.fig.patch.set_facecolor('#1e1e2e')

                    # 1. Évolution du Stockage (par année de modification)
                    ax1 = self.fig.add_subplot(211)
                    ax1.set_facecolor('#1e1e2e')
                    if years:
                        x = [y["yr"] for y in years]
                        y = [(y["sz"] or 0) / (1024**3) for y in years]  # en Go
                        ax1.bar(x, y, color='#38bdf8', edgecolor='#0284c7', linewidth=0.8, alpha=0.9)
                        ax1.set_title("Évolution du stockage (Go / Année)", color='#f8fafc', pad=10, fontdict={'fontsize': 10, 'fontweight': 'bold'})
                        ax1.tick_params(axis='x', colors='#94a3b8', rotation=45, labelsize=8)
                        ax1.tick_params(axis='y', colors='#94a3b8', labelsize=8)
                        ax1.grid(True, linestyle=':', alpha=0.2, color='#ffffff', axis='y')

                        ax1.spines['top'].set_visible(False)
                        ax1.spines['right'].set_visible(False)
                        ax1.spines['left'].set_visible(False)
                        ax1.spines['bottom'].set_color('#334155')
                    else:
                        ax1.axis('off')
                        ax1.text(0.5, 0.5, "Données temporelles insuffisantes", ha='center', va='center', color='#64748b', fontsize=10)

                    # 2. Classement des Top Mots-Clés IA (Horizontal Bar Ranking)
                    ax2 = self.fig.add_subplot(212)
                    ax2.set_facecolor('#1e1e2e')
                    ax2.set_title("Top Mots-Clés IA (Fichiers indexés)", color='#f8fafc', pad=10, fontdict={'fontsize': 10, 'fontweight': 'bold'})

                    if top_tags:
                        tag_names = [t["name"].replace("ia:", "").capitalize() for t in reversed(top_tags)]
                        tag_counts = [t["cnt"] for t in reversed(top_tags)]

                        bars2 = ax2.barh(tag_names, tag_counts, color='#a855f7', edgecolor='#7e22ce', linewidth=0.8, alpha=0.85)
                        ax2.tick_params(axis='x', colors='#94a3b8', labelsize=8)
                        ax2.tick_params(axis='y', colors='#e2e8f0', labelsize=8.5)
                        ax2.grid(True, linestyle=':', alpha=0.2, color='#ffffff', axis='x')

                        for bar in bars2:
                            w = bar.get_width()
                            ax2.text(w + (max(tag_counts)*0.02), bar.get_y() + bar.get_height()/2, f"{int(w)}",
                                     va='center', ha='left', color='#cbd5e1', fontsize=8, fontweight='bold')

                        ax2.spines['top'].set_visible(False)
                        ax2.spines['right'].set_visible(False)
                        ax2.spines['left'].set_visible(False)
                        ax2.spines['bottom'].set_color('#334155')
                    else:
                        ax2.axis('off')
                        ax2.text(0.5, 0.5, "Aucun mot-clé IA généré", ha="center", va="center", color="#64748b", fontsize=10)

                    self.fig.tight_layout()
                    self.canvas.draw()
                except Exception as e:
                    print("Error drawing analytics:", e)
        except Exception as e:
            print("Error in dashboard UI:", e)
        finally:
            self._refreshing_dash = False
