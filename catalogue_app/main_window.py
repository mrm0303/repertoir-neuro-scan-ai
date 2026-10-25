import sys
import os
import time
import queue
import threading
import re
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

import ttkbootstrap as tb
try:
    from tkinterdnd2 import TkinterDnD, DND_FILES
    HAS_DND = True
except ImportError:
    HAS_DND = False

from catalogue_app.db import connect, backup_database, online_map, tools_status
from catalogue_app.config import APP_NAME
from catalogue_app.utils import normalize, human_count, human_size, human_clock

# UI Tabs Imports
from catalogue_app.ui.tabs.dashboard_tab import DashboardTab
from catalogue_app.ui.tabs.scanner_tab import ScannerTab
from catalogue_app.ui.tabs.servers_tab import ServersTab
from catalogue_app.ui.tabs.dit_tab import DitTab
from catalogue_app.ui.tabs.search_tab import SearchTab
from catalogue_app.ui.tabs.chat_tab import ChatTab
from catalogue_app.ui.tabs.rename_tab import RenameTab
from catalogue_app.ui.tabs.sync_tab import SyncTab
from catalogue_app.ui.tabs.tags_tab import TagsTab
from catalogue_app.ui.tabs.duplicates_tab import DuplicatesTab
from catalogue_app.ui.tabs.projects_tab import ProjectsTab
from catalogue_app.ui.tabs.settings_tab import SettingsTab

if HAS_DND:
    class AppBase(tb.Window, TkinterDnD.DnDWrapper):
        pass
else:
    class AppBase(tb.Window):
        pass

class CatalogueApp(AppBase):
    def __init__(self, con):
        super().__init__(themename="darkly")
        if HAS_DND:
            self.TkdndVersion = TkinterDnD._require(self)
        
        self.con = con
        self.title(f"{APP_NAME} V6 — Post-Production Manager (Refactored)")
        self.geometry("1400x900")
        
        # Core State Variables
        self.msgq = queue.Queue()
        self.cancel_event = threading.Event()
        self.ai_cache = None
        self.online = {}
        self.dup_selected_vols = None
        self.jobs, self.job_seq, self.queue_running = {}, 0, False
        self.search_rows, self.proj_rows, self.plan = [], [], []
        self.basket_items = {}
        
        # Configuration Variables
        self.var_hash = tk.BooleanVar(value=True)
        self.var_meta = tk.BooleanVar(value=True)
        self.var_pre = tk.BooleanVar(value=True)
        self.var_inc = tk.BooleanVar(value=True)
        self.var_skipsys = tk.BooleanVar(value=True)
        self.var_thumbs = tk.BooleanVar(value=True)
        self.var_theme = tk.StringVar(value="darkly")
        self.var_msg = tk.StringVar()
        
        self.style.configure("Treeview", rowheight=22)
        self.style.configure("Big.TLabel", font=("TkDefaultFont", 12, "bold"))
        
        self._build_ui()
        
        # Initial refreshes and background loop
        self._refresh_online(silent=True)
        self.refresh_volumes()
        self.refresh_dashboard()
        self.refresh_tags()
        # Vérification silencieuse des mises à jour GitHub au démarrage (après 3 secondes)
        self.after(3000, lambda: self.check_and_prompt_update(interactive=False))
        # La pompe de messages et l'horloge sont gérées uniquement par ScannerTab
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        
    def _build_ui(self):
        # Top Global Header Bar
        top_header = ttk.Frame(self)
        top_header.pack(fill="x", padx=12, pady=(6, 2))
        
        lbl_app = ttk.Label(top_header, text="🎬 Repertoir Neuro Scan.AI — V6.0 PRO", font=("TkDefaultFont", 11, "bold"))
        lbl_app.pack(side="left")
        
        btn_guide = ttk.Button(
            top_header, 
            text="📖 Guide d'Utilisation / User Manual / دليل الاستخدام", 
            command=self.open_user_guide
        )
        btn_guide.pack(side="right")

        self.nb = ttk.Notebook(self)
        self.nb.pack(fill="both", expand=True, padx=8, pady=(4, 0))
        
        # --- Main Tabs Frames ---
        self.tab_dash = ttk.Frame(self.nb)
        self.tab_stockage_main = ttk.Frame(self.nb)
        self.tab_search = ttk.Frame(self.nb)
        self.tab_ia_main = ttk.Frame(self.nb)
        self.tab_settings = ttk.Frame(self.nb)
        
        self.nb.add(self.tab_dash, text="  📊 Tableau de bord  ")
        self.nb.add(self.tab_stockage_main, text="  💽 Stockage & Analyse  ")
        self.nb.add(self.tab_search, text="  🔍 Recherche  ")
        self.nb.add(self.tab_ia_main, text="  🧠 Laboratoire IA  ")
        self.nb.add(self.tab_settings, text="  ⚙️ Paramètres  ")
        
        # --- Sub Tabs: Stockage ---
        self.nb_stockage = ttk.Notebook(self.tab_stockage_main)
        self.nb_stockage.pack(fill="both", expand=True, padx=2, pady=2)
        
        self.tab_scan = ttk.Frame(self.nb_stockage)
        self.tab_servers = ttk.Frame(self.nb_stockage)
        self.tab_dit = ttk.Frame(self.nb_stockage)
        
        self.nb_stockage.add(self.tab_scan, text=" Disques Locaux ")
        self.nb_stockage.add(self.tab_servers, text=" Serveurs Distants ")
        self.nb_stockage.add(self.tab_dit, text=" 📥 Transfert DIT ")
        
        # --- Sub Tabs: Laboratoire IA ---
        self.nb_ia = ttk.Notebook(self.tab_ia_main)
        self.nb_ia.pack(fill="both", expand=True, padx=2, pady=2)
        
        self.tab_chat = ttk.Frame(self.nb_ia)
        self.tab_rename = ttk.Frame(self.nb_ia)
        self.tab_sync = ttk.Frame(self.nb_ia)
        self.tab_tags = ttk.Frame(self.nb_ia)
        self.tab_dup = ttk.Frame(self.nb_ia)
        self.tab_proj = ttk.Frame(self.nb_ia)
        
        self.nb_ia.add(self.tab_chat, text=" Assistant IA ")
        self.nb_ia.add(self.tab_rename, text=" 🪄 Renommage de Rushes ")
        self.nb_ia.add(self.tab_sync, text=" 🎬 Sync Image & Son ")
        self.nb_ia.add(self.tab_tags, text=" Étiquettes ")
        self.nb_ia.add(self.tab_dup, text=" Doublons ")
        self.nb_ia.add(self.tab_proj, text=" Projets ")

        # Status Bar
        self.status = tk.StringVar(value=tools_status())
        ttk.Label(self, textvariable=self.status, anchor="w",
                  relief="sunken", padding=4).pack(fill="x", side="bottom")

        # --- Instantiate Tab Views ---
        self.dashboard_tab = DashboardTab(self.tab_dash, self)
        self.dashboard_tab.pack(fill="both", expand=True)
        
        self.scanner_tab = ScannerTab(self.tab_scan, self)
        self.scanner_tab.pack(fill="both", expand=True)
        
        self.servers_tab = ServersTab(self.tab_servers, self)
        self.servers_tab.pack(fill="both", expand=True)
        
        self.dit_tab = DitTab(self.tab_dit, self)
        self.dit_tab.pack(fill="both", expand=True)
        
        self.search_tab = SearchTab(self.tab_search, self)
        self.search_tab.pack(fill="both", expand=True)
        
        self.chat_tab = ChatTab(self.tab_chat, self)
        self.chat_tab.pack(fill="both", expand=True)
        
        self.rename_tab = RenameTab(self.tab_rename, self)
        self.rename_tab.pack(fill="both", expand=True)
        
        self.sync_tab = SyncTab(self.tab_sync, self)
        self.sync_tab.pack(fill="both", expand=True)
        
        self.tags_tab = TagsTab(self.tab_tags, self)
        self.tags_tab.pack(fill="both", expand=True)
        
        self.duplicates_tab = DuplicatesTab(self.tab_dup, self)
        self.duplicates_tab.pack(fill="both", expand=True)
        
        self.projects_tab = ProjectsTab(self.tab_proj, self)
        self.projects_tab.pack(fill="both", expand=True)
        
        self.settings_tab = SettingsTab(self.tab_settings, self)
        self.settings_tab.pack(fill="both", expand=True)

    # --- Helper & Controller Delegation Methods ---
    def _refresh_online(self, silent=False):
        if not silent:
            self.status.set("Détection des disques branchés…")
        try:
            self.online = online_map(self.con)
        except Exception as exc:
            self.online = {}
            if not silent:
                messagebox.showerror(APP_NAME, str(exc))
        n = sum(1 for v in self.online.values() if v)
        if not silent:
            self.refresh_volumes()
            self.status.set(f"{n} disque(s) branché(s) sur "
                            f"{len(self.online)} catalogué(s).   |   " + tools_status())

    def refresh_volumes(self):
        if hasattr(self, 'scanner_tab') and hasattr(self.scanner_tab, 'refresh_volumes'):
            self.scanner_tab.refresh_volumes()
        elif hasattr(self, 'scanner_tab') and hasattr(self.scanner_tab, 'refresh'):
            self.scanner_tab.refresh()

    def refresh_dashboard(self):
        if hasattr(self, 'dashboard_tab') and hasattr(self.dashboard_tab, 'refresh'):
            self.dashboard_tab.refresh()

    def refresh_tags(self):
        if hasattr(self, 'tags_tab') and hasattr(self.tags_tab, 'refresh'):
            self.tags_tab.refresh()

    def _do_search(self):
        if hasattr(self, 'search_tab') and hasattr(self.search_tab, '_do_search'):
            self.search_tab._do_search()

    def _make_sortable(self, tv, cols, heads):
        state = {"col": None, "desc": False}

        def sort_by(col):
            state["desc"] = not state["desc"] if state["col"] == col else False
            state["col"] = col
            items = [(tv.set(i, col), i) for i in tv.get_children("")]

            def key(pair):
                v = pair[0]
                num = re.sub(r"[^\d,.\-]", "", v).replace(",", ".").strip(".")
                try:
                    if re.search(r"\d", v) and not re.match(r"^\d{4}-\d{2}-\d{2}$", v):
                        base = float(num)
                        for unit, mult in (("Po", 2**50), ("To", 2**40), ("Go", 2**30),
                                           ("Mo", 2**20), ("Ko", 2**10)):
                            if unit in v:
                                return base * mult
                        return base
                except ValueError:
                    pass
                return normalize(v)

            try:
                items.sort(key=key, reverse=state["desc"])
            except TypeError:
                items.sort(key=lambda p: normalize(p[0]), reverse=state["desc"])
            for pos, (_, iid) in enumerate(items):
                tv.move(iid, "", pos)
            for c, h in zip(cols, heads):
                arrow = "  ▼" if (c == col and state["desc"]) else ("  ▲" if c == col else "")
                tv.heading(c, text=h + arrow)

        for c in cols:
            tv.heading(c, command=lambda cc=c: sort_by(cc))

    def _add_to_basket(self):
        if hasattr(self, 'search_tab') and hasattr(self.search_tab, '_add_to_basket'):
            self.search_tab._add_to_basket()

    def _clear_basket(self):
        if hasattr(self, 'search_tab') and hasattr(self.search_tab, '_clear_basket'):
            self.search_tab._clear_basket()

    def _generate_proxies(self):
        if hasattr(self, 'search_tab') and hasattr(self.search_tab, '_generate_proxies'):
            self.search_tab._generate_proxies()

    def _export_basket_xml(self):
        if hasattr(self, 'search_tab') and hasattr(self.search_tab, '_export_basket_xml'):
            self.search_tab._export_basket_xml()


    # ===== Façades partagées (accès inter-onglets) =====
    def _make_tree(self, parent, cols, heads, widths, selectmode="extended"):
        wrap = ttk.Frame(parent)
        wrap.pack(fill="both", expand=True, padx=8, pady=4)
        tv = ttk.Treeview(wrap, columns=cols, show="headings", selectmode=selectmode)
        for c, h, w in zip(cols, heads, widths):
            tv.heading(c, text=h)
            min_w = max(60, int(w * 0.6))
            tv.column(c, width=w, minwidth=min_w, anchor="w", stretch=True)
        vs = ttk.Scrollbar(wrap, orient="vertical", command=tv.yview)
        hs = ttk.Scrollbar(wrap, orient="horizontal", command=tv.xview)
        tv.configure(yscrollcommand=vs.set, xscrollcommand=hs.set)
        tv.grid(row=0, column=0, sticky="nsew")
        vs.grid(row=0, column=1, sticky="ns")
        hs.grid(row=1, column=0, sticky="we")
        wrap.rowconfigure(0, weight=1)
        wrap.columnconfigure(0, weight=1)
        self._make_sortable(tv, cols, heads)
        try:
            from catalogue_app.ui.components.tooltip import attach_treeview_tooltip
            attach_treeview_tooltip(tv)
        except Exception:
            pass
        return tv

    def _tab_attr(self, tab_name, attr):
        tab = getattr(self, tab_name, None)
        return getattr(tab, attr, None) if tab is not None else None

    # Widgets de l'onglet Recherche utilisés ailleurs (Étiquettes, Scanner)
    var_q = property(lambda self: self._tab_attr("search_tab", "var_q"))
    var_tagfilter = property(lambda self: self._tab_attr("search_tab", "var_tagfilter"))
    cmb_cat = property(lambda self: self._tab_attr("search_tab", "cmb_cat"))
    cmb_vol = property(lambda self: self._tab_attr("search_tab", "cmb_vol"))
    lbl_res = property(lambda self: self._tab_attr("search_tab", "lbl_res"))
    tv_basket = property(lambda self: self._tab_attr("search_tab", "tv_basket"))
    # Autres onglets
    cmb_dupvol = property(lambda self: self._tab_attr("duplicates_tab", "cmb_dupvol"))
    cmb_dashtree = property(lambda self: self._tab_attr("dashboard_tab", "cmb_dashtree"))
    dash_treemap = property(lambda self: self._tab_attr("dashboard_tab", "dash_treemap"))
    var_path = property(lambda self: self._tab_attr("scanner_tab", "var_path"))
    tv_rename = property(lambda self: self._tab_attr("rename_tab", "tv_rename"))

    def _show_results(self, rows, tagmap):
        if hasattr(self, "search_tab"):
            self.search_tab._show_results(rows, tagmap)

    def open_tag_in_search(self, tag_name):
        st = getattr(self, "search_tab", None)
        if not st:
            return
        st.var_tagfilter.set(tag_name)
        st.var_q.set("")
        try:
            st.cmb_cat.set("toutes")
        except Exception:
            pass
        st._do_search()
        self.nb.select(self.tab_search)

    def _show_shooting_timeline(self):
        from catalogue_app.shooting_timeline import ShootingTimelineDialog
        ShootingTimelineDialog(self, self.con)

    def check_and_prompt_update(self, interactive=True):
        """Vérifie sur GitHub s'il y a une mise à jour et propose de l'installer en 1 clic."""
        from catalogue_app.updater import check_for_updates, apply_update, restart_application
        if interactive:
            self.status.set("🔄 Vérification des mises à jour sur GitHub en cours...")

        def _bg():
            res = check_for_updates()
            def _on_ui():
                st = res.get("status")
                if st == "update_available":
                    n = res.get("behind_count", 1)
                    changelog = res.get("changelog", "")
                    self.status.set(f"🎉 {n} mise(s) à jour disponible(s) sur GitHub ! Cliquez sur « 🔄 Mise à jour » pour l'installer.")
                    btn_dash = self._tab_attr("dashboard_tab", "btn_update")
                    if btn_dash:
                        btn_dash.config(text=f"🔄 Mise à jour ({n}) !")
                    if interactive:
                        msg = (
                            f"🎉 {n} nouvelle(s) mise(s) à jour disponible(s) sur GitHub !\n\n"
                            f"Nouveautés / Corrections :\n{changelog}\n\n"
                            f"🔒 Votre base de données personnelle (catalogue.db) ne sera PAS modifiée.\n\n"
                            f"Voulez-vous télécharger et installer cette mise à jour maintenant ?"
                        )
                        if messagebox.askyesno(f"{APP_NAME} — Mise à jour", msg):
                            self._run_update_install()
                elif st == "up_to_date":
                    if interactive:
                        self.status.set(res.get("message", "Application à jour."))
                        messagebox.showinfo(f"{APP_NAME} — Mise à jour", res.get("message", "Votre application est à jour !"))
                elif st == "no_repo":
                    if interactive:
                        self.nb.select(self.tab_settings)
                        messagebox.showinfo(
                            f"{APP_NAME} — Mise à jour GitHub",
                            "Aucun dépôt GitHub n'est encore renseigné.\n\n"
                            "Entrez l'adresse de votre dépôt GitHub dans l'onglet « ⚙️ Paramètres » > « Mises à jour & GitHub »."
                        )
                else:
                    if interactive:
                        messagebox.showwarning(f"{APP_NAME} — Mise à jour", res.get("message", "Erreur de vérification."))
            self.after(0, _on_ui)

        threading.Thread(target=_bg, daemon=True).start()

    def _run_update_install(self):
        from catalogue_app.updater import apply_update, restart_application
        self.status.set("⏳ Téléchargement et installation de la mise à jour depuis GitHub...")

        def _bg():
            ok, msg = apply_update(progress_cb=lambda m: self.after(0, lambda: self.status.set(f"⏳ {m}")))
            def _done():
                if ok:
                    self.status.set("✅ Mise à jour installée avec succès !")
                    if messagebox.askyesno(f"{APP_NAME} — Mise à jour terminée", msg):
                        restart_application()
                else:
                    self.status.set("⚠️ Échec de la mise à jour.")
                    messagebox.showerror(f"{APP_NAME} — Erreur de mise à jour", msg)
            self.after(0, _done)

        threading.Thread(target=_bg, daemon=True).start()

    def _toggle_web_server(self):
        import webbrowser
        from catalogue_app.web_server import server_manager
        btn = self._tab_attr("settings_tab", "btn_web") or self._tab_attr("dashboard_tab", "btn_web")
        if not server_manager.is_running:
            server_manager.start()
            if btn: btn.config(text="🌐 Accès Web : ACTIF (Arrêter)")
            urls = server_manager.get_urls()
            msg = (f"🔒 Serveur Web & Mobile ACTIF\n\n🔑 CODE PIN : {urls.get('pin','')}\n\n"
                   f"• Réseau : {urls['network']}\n• Lien direct : {urls['network_authenticated']}\n\n"
                   f"Ouvrir l'interface sur ce Mac ?")
            if messagebox.askyesno(APP_NAME, msg):
                webbrowser.open(urls["local_authenticated"])
        else:
            server_manager.stop()
            if btn: btn.config(text="🌐 Lancer Accès Web & Mobile")
            messagebox.showinfo(APP_NAME, "Le serveur Web a été arrêté.")

    def open_user_guide(self):
        """Ouvre le guide d'utilisation interactif trilingue dans le navigateur web par défaut."""
        import webbrowser
        base_dir = os.path.dirname(os.path.abspath(__file__))
        guide_html = os.path.join(base_dir, "manuel.html")
        if not os.path.exists(guide_html):
            guide_html = os.path.join(base_dir, "docs", "guide_complet.html")
        if os.path.exists(guide_html):
            webbrowser.open(f"file://{os.path.abspath(guide_html)}")
        else:
            messagebox.showinfo(APP_NAME, "Le fichier de guide n'a pas été trouvé.")

    def open_markdown_guide(self):
        """Ouvre le guide Markdown avec le lecteur par défaut du système."""
        import subprocess
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        guide_md = os.path.join(base_dir, "GUIDE_UTILISATION_TRILINGUE.md")
        if os.path.exists(guide_md):
            if sys.platform == "darwin":
                subprocess.call(["open", guide_md])
            elif os.name == "nt":
                os.startfile(guide_md)
            else:
                subprocess.call(["xdg-open", guide_md])
        else:
            messagebox.showinfo(APP_NAME, "Le fichier GUIDE_UTILISATION_TRILINGUE.md n'a pas été trouvé.")

    def _on_close(self):
        import subprocess, signal
        enr = getattr(self, "ai_enricher", None) or self._tab_attr("dashboard_tab", "ai_enricher")
        if enr is not None and getattr(enr, "is_running", False):
            try: enr.stop()
            except Exception: pass
        self.queue_running = False
        self.cancel_event.set()
        for j in self.jobs.values():
            if "cancel" in j: j["cancel"].set()
        dit_job = self._tab_attr("dit_tab", "dit_job")
        if dit_job is not None and hasattr(dit_job, "stop"):
            try: dit_job.stop()
            except Exception: pass
        try:
            from catalogue_app.web_server import server_manager
            if server_manager.is_running: server_manager.stop()
        except Exception:
            pass
        try:
            out = subprocess.check_output(["pgrep", "-f", "repertoir_vision_frame"], text=True).strip()
            for pid in out.split("\n"):
                if pid: os.kill(int(pid), signal.SIGTERM)
        except Exception:
            pass
        try:
            if sys.platform == "darwin":
                subprocess.run(["pkill", "-f", "qlmanage"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass
        try:
            self.con.commit()
        except Exception:
            pass
        self.destroy()

def main():
    args = sys.argv[1:]
    if args and args[0] in ("--scan", "-s"):
        from catalogue_app.scanner import Scanner, suggest_volume_name
        con = connect()
        root = args[1] if len(args) > 1 else "."
        name = args[2] if len(args) > 2 else suggest_volume_name(root)
        def prog(kind, payload):
            if kind == "log":
                print(payload, flush=True)
            elif kind == "tick" and payload.get("total"):
                pct = payload["n"] * 100.0 / payload["total"]
                rate = payload["n"] / payload["elapsed"] if payload["elapsed"] else 0
                remain = (payload["total"] - payload["n"]) / rate if rate else 0
                print(f"\r{pct:5.1f} %  écoulé {human_clock(payload['elapsed'])}  restant ≈ {human_clock(remain)}   ", end="", flush=True)
        Scanner(con, progress=prog).scan(root, name)
        print()
        return
    if args and args[0] == "--retag":
        from catalogue_app.db import retag_all
        con = connect()
        print("Recalcul des étiquettes…")
        print(f"{retag_all(con)} fichiers traités.")
        return
    backup_database()
    con = connect()
    app = CatalogueApp(con)
    app.mainloop()

if __name__ == "__main__":
    main()
