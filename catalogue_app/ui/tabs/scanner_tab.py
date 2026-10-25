import os
import sys
import time
import threading
import queue
import re
import subprocess
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog

from catalogue_app.ui.tabs.base_tab import BaseTab
from catalogue_app.ui.components import MultiSelectMenu
from catalogue_app.config import APP_NAME, DB_PATH
from catalogue_app.utils import human_size, human_count, human_clock, normalize
from catalogue_app.db import (
    connect,
    list_mounted_volumes,
    suggest_volume_name,
    online_map,
    tools_status,
    repair_catalog,
    retag_all,
)
from catalogue_app.scanner import Scanner
from catalogue_app.queries import stats, export_rows, reveal


class ScannerTab(BaseTab):
    def _build_ui(self):
        f = self

        # Initialisation de l'état partagé sur self.app si non présent
        if not hasattr(self.app, "jobs"):
            self.app.jobs = {}
        if not hasattr(self.app, "job_seq"):
            self.app.job_seq = 0
        if not hasattr(self.app, "queue_running"):
            self.app.queue_running = False
        if not hasattr(self.app, "online"):
            self.app.online = {}

        top = ttk.LabelFrame(f, text="Analyser un disque", padding=10)
        top.pack(fill="x", padx=8, pady=8)

        ttk.Label(top, text="Disque monté :").grid(row=0, column=0, sticky="w")
        self.cmb_mount = ttk.Combobox(
            top, width=46, state="readonly", values=list_mounted_volumes()
        )
        self.cmb_mount.grid(row=0, column=1, sticky="w", padx=6)
        self.cmb_mount.bind("<<ComboboxSelected>>", self._on_pick_mount)
        ttk.Button(top, text="Actualiser", command=self._refresh_mounts).grid(
            row=0, column=2, padx=4
        )
        ttk.Button(top, text="Parcourir…", command=self._browse).grid(
            row=0, column=3, padx=4
        )

        ttk.Label(top, text="Dossier analysé :").grid(
            row=1, column=0, sticky="w", pady=(8, 0)
        )
        self.var_path = tk.StringVar()
        ttk.Entry(top, textvariable=self.var_path).grid(
            row=1, column=1, columnspan=3, sticky="we", padx=6, pady=(8, 0)
        )

        ttk.Label(top, text="Nom du disque :").grid(
            row=2, column=0, sticky="w", pady=(8, 0)
        )
        self.var_volname = tk.StringVar()
        ttk.Entry(top, textvariable=self.var_volname, width=36).grid(
            row=2, column=1, sticky="w", padx=6, pady=(8, 0)
        )
        ttk.Label(
            top,
            text="(étiquette physique du disque — ex. « RUSHES 04 »)",
            foreground="#666",
        ).grid(row=2, column=2, columnspan=2, sticky="w")

        ttk.Label(top, text="Note :").grid(row=3, column=0, sticky="w", pady=(8, 0))
        self.var_note = tk.StringVar()
        ttk.Entry(top, textvariable=self.var_note).grid(
            row=3, column=1, columnspan=3, sticky="we", padx=6, pady=(8, 0)
        )

        opts = ttk.Frame(top)
        opts.grid(row=4, column=0, columnspan=4, sticky="w", pady=(10, 0))
        self.var_hash = tk.BooleanVar(value=True)
        self.var_meta = tk.BooleanVar(value=True)
        self.var_pre = tk.BooleanVar(value=True)
        self.var_inc = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            opts, text="Empreintes (doublons)", variable=self.var_hash
        ).pack(side="left", padx=(0, 14))
        ttk.Checkbutton(
            opts, text="Métadonnées (caméra, durée…)", variable=self.var_meta
        ).pack(side="left", padx=(0, 14))
        ttk.Checkbutton(
            opts, text="Pré-comptage (temps restant estimé)", variable=self.var_pre
        ).pack(side="left", padx=(0, 14))
        ttk.Checkbutton(
            opts, text="Analyse incrémentale", variable=self.var_inc
        ).pack(side="left", padx=(0, 14))
        self.var_skipsys = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            opts, text="Ignorer les dossiers système", variable=self.var_skipsys
        ).pack(side="left")

        btns = ttk.Frame(top)
        btns.grid(row=5, column=0, columnspan=4, sticky="we", pady=(12, 0))
        ttk.Button(btns, text="Ajouter à la file", command=self._add_job).pack(
            side="left"
        )
        ttk.Button(
            btns, text="Supprimer de la file", command=self._remove_selected_jobs
        ).pack(side="left", padx=(6, 8))
        self.btn_start = ttk.Button(
            btns, text="Démarrer la file", command=self._start_queue
        )
        self.btn_start.pack(side="left", padx=(0, 8))
        self.btn_pause = ttk.Button(
            btns, text="Pause", command=self._toggle_pause_selected
        )
        self.btn_pause.pack(side="left", padx=(0, 8))
        ttk.Button(
            btns, text="Arrêter sélection", command=self._stop_selected
        ).pack(side="left", padx=(0, 6))
        ttk.Button(btns, text="Tout arrêter", command=self._stop_all).pack(
            side="left"
        )
        ttk.Label(btns, text="Analyses simultanées :").pack(
            side="left", padx=(18, 4)
        )
        self.var_par = tk.StringVar(value="2")
        ttk.Spinbox(btns, from_=1, to=10, width=3, textvariable=self.var_par).pack(
            side="left"
        )
        ttk.Label(
            btns,
            text="(jusqu'à 10 disques en simultané)",
            foreground="#666",
        ).pack(side="left", padx=8)
        top.columnconfigure(1, weight=1)

        # ---- file d'analyse : un chronomètre par disque ----
        timer = ttk.LabelFrame(
            f, text="File d'analyse (sélection multiple avec Shift / Cmd)", padding=6
        )
        timer.pack(fill="x", padx=8, pady=(0, 8))
        jcols = (
            "disque",
            "etat",
            "pct",
            "ecoule",
            "restant",
            "vitesse",
            "traites",
            "dossier",
        )
        jheads = (
            "Disque",
            "État",
            "%",
            "Écoulé",
            "Restant",
            "Vitesse",
            "Traités",
            "Dossier en cours",
        )
        self.tv_jobs = ttk.Treeview(
            timer, columns=jcols, show="headings", height=5, selectmode="extended"
        )
        for c, h, w in zip(jcols, jheads, (170, 110, 60, 90, 100, 140, 190, 260)):
            self.tv_jobs.heading(c, text=h)
            min_w = max(50, int(w * 0.6))
            self.tv_jobs.column(c, width=w, minwidth=min_w, anchor="w", stretch=True)
        self.tv_jobs.pack(side="left", fill="x", expand=True)
        jsb = ttk.Scrollbar(timer, orient="vertical", command=self.tv_jobs.yview)
        jsb.pack(side="right", fill="y")
        self.tv_jobs.configure(yscrollcommand=jsb.set)
        try:
            from catalogue_app.ui.components.tooltip import attach_treeview_tooltip
            attach_treeview_tooltip(self.tv_jobs)
        except Exception:
            pass
        self.tv_jobs.tag_configure("run", foreground="#64b5f6")
        self.tv_jobs.tag_configure("ok", foreground="#81c784")
        self.tv_jobs.tag_configure("wait", foreground="#9e9e9e")
        self.tv_jobs.tag_configure("pause", foreground="#ffb74d")
        self.tv_jobs.tag_configure("err", foreground="#e57373")
        self.tv_jobs.bind(
            "<<TreeviewSelect>>", lambda _e: self._update_pause_btn_label()
        )
        self._make_sortable(self.tv_jobs, jcols, jheads)

        # Menu contextuel clic droit sur la file d'analyse
        self.menu_jobs = tk.Menu(timer, tearoff=0)
        self.menu_jobs.add_command(
            label="⏸️ Pause / ▶️ Reprendre", command=self._toggle_pause_selected
        )
        self.menu_jobs.add_command(
            label="⏹️ Arrêter les sélectionnés", command=self._stop_selected
        )
        self.menu_jobs.add_command(
            label="🗑️ Supprimer de la file", command=self._remove_selected_jobs
        )
        self.menu_jobs.add_separator()
        self.menu_jobs.add_command(
            label="📂 Ouvrir le dossier source dans le Finder",
            command=self._reveal_sel_job,
        )

        if sys.platform == "darwin":
            self.tv_jobs.bind("<Button-2>", self._popup_jobs)
            self.tv_jobs.bind("<Control-Button-1>", self._popup_jobs)
        else:
            self.tv_jobs.bind("<Button-3>", self._popup_jobs)

        mid = ttk.LabelFrame(
            f,
            text="Disques catalogués (double-clic sur « Priorité » pour la modifier)",
            padding=6,
        )
        mid.pack(fill="both", expand=True, padx=8, pady=(0, 6))
        cols = (
            "nom",
            "etat",
            "priorite",
            "fichiers",
            "taille",
            "analyse",
            "chemin",
            "note",
        )
        heads = (
            "Disque",
            "État",
            "Priorité",
            "Fichiers",
            "Taille",
            "Dernière analyse",
            "Chemin actuel",
            "Note",
        )
        self.tv_vol = ttk.Treeview(mid, columns=cols, show="headings", height=8)
        for c, h, w in zip(cols, heads, (180, 90, 65, 85, 95, 140, 260, 180)):
            self.tv_vol.heading(c, text=h)
            min_w = max(50, int(w * 0.6))
            self.tv_vol.column(c, width=w, minwidth=min_w, anchor="w", stretch=True)
        self.tv_vol.pack(fill="both", expand=True, side="left")
        sb = ttk.Scrollbar(mid, orient="vertical", command=self.tv_vol.yview)
        sb.pack(side="right", fill="y")
        self.tv_vol.configure(yscrollcommand=sb.set)
        self.tv_vol.bind("<Double-1>", self._edit_priority)
        self._make_sortable(self.tv_vol, cols, heads)
        try:
            from catalogue_app.ui.components.tooltip import attach_treeview_tooltip
            attach_treeview_tooltip(self.tv_vol)
        except Exception:
            pass

        vb = ttk.Frame(f)
        vb.pack(fill="x", padx=8, pady=(0, 6))
        ttk.Button(
            vb,
            text="Détecter les disques branchés",
            command=self._refresh_online,
        ).pack(side="left", padx=(0, 6))
        ttk.Button(
            vb, text="Retirer du catalogue", command=self._delete_volume
        ).pack(side="left")
        ttk.Button(
            vb, text="Exporter tout (CSV)", command=self._export_all
        ).pack(side="left", padx=6)
        ttk.Button(
            vb, text="Recalculer les étiquettes", command=self._retag
        ).pack(side="left")
        ttk.Button(
            vb, text="Vérifier et réparer", command=self._repair
        ).pack(side="left", padx=6)
        self.lbl_stats = ttk.Label(vb, text="")
        self.lbl_stats.pack(side="right")

        vb2 = ttk.Frame(f)
        vb2.pack(fill="x", padx=8, pady=(0, 6))
        ttk.Button(
            vb2,
            text="📦 Exporter Pack Portable (.catpkg)",
            command=self._export_portable_package,
        ).pack(side="left", padx=(0, 6))
        ttk.Button(
            vb2,
            text="📥 Importer Pack (.catpkg)",
            command=self._import_portable_package,
        ).pack(side="left", padx=6)
        ttk.Button(
            vb2,
            text="🗺️ Carte Visuelle Treemap",
            command=self._open_treemap_for_selected_volume,
        ).pack(side="left", padx=6)
        ttk.Button(
            vb2,
            text="💾 Exporter Backup (HTML)",
            command=self._export_html_for_selected_volume,
        ).pack(side="left", padx=6)
        ttk.Button(
            vb2,
            text="📄 Exporter Rapport (PDF)",
            command=self._export_pdf_for_selected_volume,
        ).pack(side="left", padx=6)
        ttk.Button(
            vb2,
            text="🔄 Rescanner (Mettre à jour)",
            command=self._rescan_volume,
        ).pack(side="right", padx=6)
        ttk.Button(
            vb2,
            text="👁️ Indexer le contenu par IA",
            command=self._run_vision_indexer,
        ).pack(side="right", padx=6)

        logf = ttk.LabelFrame(f, text="Journal", padding=4)
        logf.pack(fill="both", padx=8, pady=(0, 8))
        self.txt_log = tk.Text(logf, height=8, wrap="word", state="normal")
        log_sb = ttk.Scrollbar(logf, orient="vertical", command=self.txt_log.yview)
        self.txt_log.configure(yscrollcommand=log_sb.set)
        self.txt_log.pack(side="left", fill="both", expand=True)
        log_sb.pack(side="right", fill="y")

        # Démarrer le pump et le timer si pas encore lancés
        if not getattr(self.app, "_scanner_pump_started", False):
            self.app._scanner_pump_started = True
            self.after(200, self._pump)
        if not getattr(self.app, "_scanner_tick_started", False):
            self.app._scanner_tick_started = True
            self.after(500, self._tick_clock)

        # Rafraîchir les disques
        self.after(100, self.refresh)

    def _make_sortable(self, tv, cols, heads):
        """Tri par clic sur l'en-tête, comme dans le Finder : un clic trie,
        un second inverse le sens. Le tri porte sur les valeurs affichées."""
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
                        for unit, mult in (
                            ("Po", 2**50),
                            ("To", 2**40),
                            ("Go", 2**30),
                            ("Mo", 2**20),
                            ("Ko", 2**10),
                        ):
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
                tv.heading(
                    c,
                    text=h
                    + (
                        " ▲"
                        if state["col"] == c and not state["desc"]
                        else " ▼"
                        if state["col"] == c
                        else ""
                    ),
                )

        for c in cols:
            tv.heading(c, command=lambda _c=c: sort_by(_c))

    def _reveal_sel_job(self):
        for j in self._get_selected_jobs():
            if j.get("path") and os.path.exists(j["path"]):
                reveal(j["path"])

    def _popup_jobs(self, event):
        iid = self.tv_jobs.identify_row(event.y)
        if iid:
            if iid not in self.tv_jobs.selection():
                self.tv_jobs.selection_set(iid)
            self._update_pause_btn_label()
            self.menu_jobs.post(event.x_root, event.y_root)

    def _refresh_mounts(self):
        if getattr(self, "_refreshing", False):
            return
        self._refreshing = True
        try:
            # Mettre à jour la liste déroulante des disques
            self.cmb_mount["values"] = list_mounted_volumes()
            # 1. Il détecte les disques durs branchés
            self._refresh_online(silent=False)
        finally:
            self._refreshing = False

    def _refresh_online(self, silent=False):
        """Repère quels disques catalogués sont branchés en ce moment, quelle que
        soit la lettre de lecteur ou le point de montage qui leur est attribué."""
        if not silent:
            if hasattr(self.app, "status") and hasattr(self.app.status, "set"):
                self.app.status.set("Détection des disques branchés…")
        try:
            self.app.online = online_map(self.app.con)
        except Exception as exc:
            self.app.online = {}
            if not silent:
                messagebox.showerror(APP_NAME, str(exc))
        n = sum(1 for v in self.app.online.values() if v)
        if not silent:
            self.refresh_volumes()
            if hasattr(self.app, "status") and hasattr(self.app.status, "set"):
                self.app.status.set(
                    f"{n} disque(s) branché(s) sur "
                    f"{len(self.app.online)} catalogué(s).   |   "
                    + tools_status()
                )

    def _on_pick_mount(self, _e=None):
        p = self.cmb_mount.get()
        if p:
            self.var_path.set(p)
            self.var_volname.set(suggest_volume_name(p))

    def _browse(self):
        p = filedialog.askdirectory(
            title="Choisir le disque ou le dossier à analyser"
        )
        if p:
            self.var_path.set(p)
            if not self.var_volname.get():
                self.var_volname.set(suggest_volume_name(p))

    def log(self, msg):
        self.txt_log.insert("end", f"[{datetime.now():%H:%M:%S}]  {msg}\n")
        self.txt_log.see("end")

    def _edit_priority(self, event):
        item = self.tv_vol.identify_row(event.y)
        col = self.tv_vol.identify_column(event.x)
        if not item or col != "#3":
            return
        name = self.tv_vol.item(item)["values"][0]
        val = simpledialog.askinteger(
            APP_NAME,
            f"Priorité de conservation pour « {name} »\n\n"
            "Plus le nombre est élevé, plus ce disque est privilégié\n"
            "pour conserver les copies lors du dédoublonnage.\n"
            "(0 = normal, 10 = disque de référence à préserver)",
            initialvalue=int(self.tv_vol.item(item)["values"][2] or 0),
            minvalue=-50,
            maxvalue=50,
            parent=self,
        )
        if val is None:
            return
        self.app.con.execute(
            "UPDATE volumes SET priority=? WHERE id=?", (val, int(item))
        )
        self.app.con.commit()
        self.refresh_volumes()

    # ---------- file d'analyse : plusieurs disques en parallèle ----------
    def _get_selected_jobs(self):
        selected = []
        for iid in self.tv_jobs.selection():
            if iid.startswith("j"):
                try:
                    jid = int(iid[1:])
                    if jid in self.app.jobs:
                        selected.append(self.app.jobs[jid])
                except ValueError:
                    pass
        return selected

    def _update_pause_btn_label(self):
        sel_jobs = self._get_selected_jobs()
        if not sel_jobs:
            self.btn_pause.config(text="Pause")
            return
        has_running = any(j["state"] == "en cours" for j in sel_jobs)
        has_paused = any(j["state"] == "en pause" for j in sel_jobs)
        if has_paused and not has_running:
            self.btn_pause.config(text="Reprendre")
        else:
            self.btn_pause.config(text="Pause")

    def _add_job(self, start_now=False):
        path, name = self.var_path.get().strip(), self.var_volname.get().strip()
        if not path or not os.path.isdir(path):
            messagebox.showerror(APP_NAME, "Veuillez choisir un dossier valide.")
            return
        if not name:
            messagebox.showerror(APP_NAME, "Veuillez donner un nom au disque.")
            return
        for j in self.app.jobs.values():
            if j["state"] in ("en attente", "en cours", "en pause") and (
                j["name"] == name
                or os.path.abspath(j["path"]) == os.path.abspath(path)
            ):
                messagebox.showinfo(APP_NAME, f"« {name} » est déjà dans la file.")
                return
        if not hasattr(self.app, "job_seq"):
            self.app.job_seq = 0
        self.app.job_seq += 1
        jid = self.app.job_seq
        self.app.jobs[jid] = {
            "id": jid,
            "name": name,
            "path": path,
            "note": self.var_note.get().strip(),
            "state": "en attente",
            "n": 0,
            "total": 0,
            "size": 0,
            "t0": None,
            "elapsed": 0,
            "pause_t0": None,
            "paused_duration": 0.0,
            "current": "",
            "cancel": threading.Event(),
            "pause": threading.Event(),
            "opts": {
                "do_hash": self.var_hash.get(),
                "do_meta": self.var_meta.get(),
                "do_precount": self.var_pre.get(),
                "incremental": self.var_inc.get(),
                "skip_system": self.var_skipsys.get(),
            },
        }
        self.tv_jobs.insert(
            "",
            "end",
            iid=f"j{jid}",
            tags=("wait",),
            values=(name, "en attente", "", "", "", "", "", path),
        )
        self.var_path.set("")
        self.var_volname.set("")
        self.var_note.set("")
        self.log(f"« {name} » ajouté à la file.")
        if start_now or getattr(self.app, "queue_running", False):
            self._start_queue()

    def _remove_selected_jobs(self):
        sel_jobs = self._get_selected_jobs()
        if not sel_jobs:
            messagebox.showinfo(
                APP_NAME,
                "Sélectionnez un ou plusieurs disques dans la file d'analyse à supprimer.",
            )
            return
        removed_names = []
        for j in sel_jobs:
            if j["state"] in ("en cours", "en pause"):
                j["cancel"].set()
                j["pause"].clear()
            iid = f"j{j['id']}"
            if self.tv_jobs.exists(iid):
                self.tv_jobs.delete(iid)
            self.app.jobs.pop(j["id"], None)
            removed_names.append(j["name"])
        if removed_names:
            self.log(
                f"🗑️ Supprimé(s) de la file d'analyse : {', '.join(removed_names)}"
            )
        self._update_pause_btn_label()
        if getattr(self.app, "queue_running", False):
            self._schedule_jobs()

    def _start_queue(self):
        self.app.queue_running = True
        self._schedule_jobs()

    def _schedule_jobs(self):
        """Démarre autant d'analyses que la limite le permet (jusqu'à 10 disques en parallèle).
        Chaque analyse a son propre thread indépendant."""
        if not getattr(self.app, "queue_running", False):
            return
        try:
            limit = max(1, min(10, int(self.var_par.get())))
        except ValueError:
            limit = 2
        running = [j for j in self.app.jobs.values() if j["state"] == "en cours"]
        if len(running) >= limit:
            return
        for j in sorted(self.app.jobs.values(), key=lambda x: x["id"]):
            if len(running) >= limit:
                break
            if j["state"] != "en attente":
                continue
            self._launch_job(j)
            running.append(j)

    def _launch_job(self, job):
        job["state"] = "en cours"
        job["t0"] = time.time()
        job["pause_t0"] = None
        job["paused_duration"] = 0.0
        job["cancel"].clear()
        job["pause"].clear()
        self._update_job_row(job)
        jid = job["id"]

        def worker():
            wcon = None
            try:
                wcon = connect()
                sc = Scanner(
                    wcon,
                    progress=lambda k, p: self.app.msgq.put((k, (jid, p))),
                    cancel_event=job["cancel"],
                    pause_event=job["pause"],
                )
                sc.scan(job["path"], job["name"], note=job["note"], **job["opts"])
            except Exception as exc:
                self.app.msgq.put(("job_error", (jid, str(exc))))
            finally:
                if wcon is not None:
                    try:
                        wcon.close()
                    except Exception:
                        pass
                self.app.msgq.put(("job_done", (jid, None)))

        threading.Thread(target=worker, daemon=True).start()

    def _toggle_pause_selected(self):
        sel_jobs = self._get_selected_jobs()
        if not sel_jobs:
            active_jobs = [
                j
                for j in self.app.jobs.values()
                if j["state"] in ("en cours", "en pause")
            ]
            if len(active_jobs) == 1:
                sel_jobs = active_jobs
            else:
                messagebox.showinfo(
                    APP_NAME,
                    "Sélectionnez un ou plusieurs disques dans la file d'analyse pour mettre en pause ou reprendre.",
                )
                return

        has_running = any(j["state"] == "en cours" for j in sel_jobs)
        if has_running:
            paused_names = []
            for j in sel_jobs:
                if j["state"] == "en cours":
                    j["pause"].set()
                    j["state"] = "en pause"
                    j["pause_t0"] = time.time()
                    self._update_job_row(j)
                    paused_names.append(j["name"])
            if paused_names:
                self.log(f"⏸️ Mise en pause de : {', '.join(paused_names)}")
        else:
            resumed_names = []
            for j in sel_jobs:
                if j["state"] == "en pause":
                    if j.get("pause_t0"):
                        j["paused_duration"] = j.get(
                            "paused_duration", 0.0
                        ) + (time.time() - j["pause_t0"])
                        j["pause_t0"] = None
                    j["pause"].clear()
                    j["state"] = "en cours"
                    self._update_job_row(j)
                    resumed_names.append(j["name"])
            if resumed_names:
                self.log(f"▶️ Reprise de l'analyse : {', '.join(resumed_names)}")

        self._update_pause_btn_label()

    def _stop_selected(self):
        sel_jobs = self._get_selected_jobs()
        if not sel_jobs:
            messagebox.showinfo(
                APP_NAME,
                "Sélectionnez un ou plusieurs disques dans la file d'analyse à arrêter.",
            )
            return
        stopped_names = []
        for j in sel_jobs:
            if j["state"] in ("en cours", "en pause"):
                j["cancel"].set()
                j["pause"].clear()
                j["state"] = "interrompu"
                self._update_job_row(j)
                stopped_names.append(j["name"])
            elif j["state"] == "en attente":
                j["state"] = "annulé"
                self._update_job_row(j)
                stopped_names.append(j["name"])
        if stopped_names:
            self.log(
                f"⏹️ Arrêt demandé pour : {', '.join(stopped_names)} (données partielles conservées)"
            )
        self._update_pause_btn_label()
        if getattr(self.app, "queue_running", False):
            self._schedule_jobs()

    def _stop_all(self):
        self.app.queue_running = False
        stopped = 0
        for j in list(self.app.jobs.values()):
            if j["state"] in ("en cours", "en pause"):
                j["cancel"].set()
                j["pause"].clear()
                j["state"] = "interrompu"
                self._update_job_row(j)
                stopped += 1
            elif j["state"] == "en attente":
                j["state"] = "annulé"
                self._update_job_row(j)
                stopped += 1
        if stopped:
            self.log(
                "Arrêt de tous les scans — la partie déjà analysée est conservée."
            )
        self._update_pause_btn_label()

    def _update_job_row(self, job):
        iid = f'j{job["id"]}'
        if not self.tv_jobs.exists(iid):
            return
        n, total = job["n"], job["total"]
        elapsed = job["elapsed"]
        rate = n / elapsed if elapsed > 0 else 0
        mbs = (job["size"] / elapsed / (1024 * 1024)) if elapsed > 0 else 0
        pct = f"{min(100.0, n * 100.0 / total):.0f} %" if total and n else ""
        remain = ""
        if total and n and rate > 0 and job["state"] == "en cours":
            left = max(0.0, (total - n) / rate)
            remain = human_clock(left) + datetime.fromtimestamp(
                time.time() + left
            ).strftime("  (fin ~%H:%M)")
        elif job["state"] == "en pause":
            remain = "⏸️ suspendu"
        tag = {
            "en cours": "run",
            "en pause": "pause",
            "terminé": "ok",
            "en attente": "wait",
            "annulé": "wait",
            "interrompu": "wait",
            "erreur": "err",
        }.get(job["state"], "wait")
        self.tv_jobs.item(
            iid,
            tags=(tag,),
            values=(
                job["name"],
                job["state"],
                pct,
                human_clock(elapsed) if job["t0"] else "",
                remain,
                f"{rate:.0f} f/s · {mbs:.0f} Mo/s" if rate else "",
                (
                    f"{human_count(n)}"
                    + (f" / {human_count(total)}" if total else "")
                    + f' · {human_size(job["size"])}'
                )
                if n
                else "",
                job["current"] or job["path"],
            ),
        )

    def _tick_clock(self):
        """Les chronomètres avancent en continu pour les jobs en cours."""
        for j in getattr(self.app, "jobs", {}).values():
            if j["state"] == "en cours" and j["t0"]:
                paused_d = j.get("paused_duration", 0.0)
                j["elapsed"] = max(0.0, time.time() - j["t0"] - paused_d)
                self._update_job_row(j)
        self.after(500, self._tick_clock)

    def _pump(self):
        try:
            while True:
                kind, payload = self.app.msgq.get_nowait()
                if kind == "log":
                    jid, msg = (
                        payload if isinstance(payload, tuple) else (None, payload)
                    )
                    job = getattr(self.app, "jobs", {}).get(jid)
                    self.log((f'[{job["name"]}] ' if job else "") + str(msg))
                elif kind == "precount":
                    jid, n = payload
                    job = getattr(self.app, "jobs", {}).get(jid)
                    if job:
                        job["current"] = f"{human_count(n)} fichiers repérés…"
                        self._update_job_row(job)
                elif kind == "start":
                    jid, p = payload
                    job = getattr(self.app, "jobs", {}).get(jid)
                    if job:
                        job["total"] = p.get("total") or 0
                        job["t0"] = p.get("t0") or time.time()
                        self._update_job_row(job)
                elif kind == "tick":
                    jid, p = payload
                    job = getattr(self.app, "jobs", {}).get(jid)
                    if job:
                        job.update(
                            n=p["n"],
                            size=p["size"],
                            elapsed=p["elapsed"],
                            current=p.get("current", ""),
                        )
                        if p.get("total"):
                            job["total"] = p["total"]
                        self._update_job_row(job)
                elif kind == "results":
                    if hasattr(self.app, "_show_results"):
                        self.app._show_results(*payload)
                    elif hasattr(self.app, "search_tab") and hasattr(
                        self.app.search_tab, "_show_results"
                    ):
                        self.app.search_tab._show_results(*payload)
                elif kind == "search_error":
                    if hasattr(self.app, "searching"):
                        self.app.searching = False
                    if hasattr(self.app, "search_tab") and hasattr(
                        self.app.search_tab, "lbl_res"
                    ):
                        self.app.search_tab.lbl_res.config(
                            text="Échec de la recherche."
                        )
                    elif hasattr(self.app, "lbl_res"):
                        self.app.lbl_res.config(text="Échec de la recherche.")
                    messagebox.showerror(
                        APP_NAME, "Recherche impossible :\n" + payload
                    )
                elif kind == "job_error":
                    jid, msg = payload
                    job = getattr(self.app, "jobs", {}).get(jid)
                    if job:
                        job["state"] = "erreur"
                        job["current"] = msg
                        self._update_job_row(job)
                    self.log("ERREUR : " + msg)
                elif kind == "error":
                    self.log("ERREUR : " + str(payload))
                elif kind == "info":
                    self.app.status.set(str(payload))
                elif kind == "job_done":
                    jid, _ = payload
                    job = getattr(self.app, "jobs", {}).get(jid)
                    if job and job["state"] != "erreur":
                        job["state"] = (
                            "interrompu" if job["cancel"].is_set() else "terminé"
                        )
                        job["current"] = ""
                        self._update_job_row(job)
                    # La base a changé : on recharge le parc, les étiquettes, et
                    # la recherche pour que les données soient immédiatement utilisables.
                    self._refresh_online(silent=True)
                    self.refresh_volumes()
                    if hasattr(self.app, "refresh_dashboard"):
                        self.app.refresh_dashboard()
                    elif hasattr(self.app, "dashboard_tab") and hasattr(
                        self.app.dashboard_tab, "refresh"
                    ):
                        self.app.dashboard_tab.refresh()
                    if hasattr(self.app, "refresh_tags"):
                        self.app.refresh_tags()
                    elif hasattr(self.app, "tags_tab") and hasattr(
                        self.app.tags_tab, "refresh"
                    ):
                        self.app.tags_tab.refresh()
                    if hasattr(self.app, "searching"):
                        self.app.searching = False
                    if hasattr(self.app, "_do_search"):
                        self.app._do_search()
                    elif hasattr(self.app, "search_tab") and hasattr(
                        self.app.search_tab, "_do_search"
                    ):
                        self.app.search_tab._do_search()
                    self._schedule_jobs()
        except queue.Empty:
            pass
        self.after(200, self._pump)

    def refresh(self):
        """Rafraîchit l'onglet selon le contrat de BaseTab."""
        self.refresh_volumes()

    def refresh_volumes(self):
        for i in self.tv_vol.get_children():
            self.tv_vol.delete(i)
        for r in self.app.con.execute(
            "SELECT * FROM volumes ORDER BY priority DESC, name"
        ):
            path = getattr(self.app, "online", {}).get(r["id"])
            self.tv_vol.insert(
                "",
                "end",
                iid=str(r["id"]),
                tags=("on" if path else "off",),
                values=(
                    r["name"],
                    "● branché" if path else "○ absent",
                    r["priority"] or 0,
                    human_count(r["file_count"]),
                    human_size(r["total_size"]),
                    (r["scanned_at"] or "").replace("T", " "),
                    path or r["last_path"] or "",
                    r["note"] or "",
                ),
            )
        self.tv_vol.tag_configure("on", foreground="#81c784")
        self.tv_vol.tag_configure("off", foreground="#9e9e9e")
        v, f, _ = stats(self.app.con)
        self.lbl_stats.config(
            text=f'{v["n"]} disque(s) — {human_count(f["n"])} fichiers '
            f'— {human_size(f["s"])}'
        )
        vol_dict = {
            r["id"]: r["name"]
            for r in self.app.con.execute("SELECT id, name FROM volumes ORDER BY name")
        }
        for combo in (self.app.cmb_vol, self.app.cmb_dupvol, self.app.cmb_dashtree):
            if combo is not None and hasattr(combo, "set_options"):
                combo.set_options(vol_dict)

    def _delete_volume(self):
        sel = self.tv_vol.selection()
        if not sel:
            return
        name = self.tv_vol.item(sel[0])["values"][0]
        if messagebox.askyesno(
            APP_NAME,
            f"Retirer « {name} » du catalogue ?\n"
            "(aucun fichier n'est supprimé sur le disque)",
        ):
            self.app.con.execute(
                "DELETE FROM files WHERE volume_id=?", (int(sel[0]),)
            )
            self.app.con.execute(
                "DELETE FROM volumes WHERE id=?", (int(sel[0]),)
            )
            self.app.con.commit()
            self.refresh_volumes()
            if hasattr(self.app, "refresh_tags"):
                self.app.refresh_tags()
            elif hasattr(self.app, "tags_tab") and hasattr(
                self.app.tags_tab, "refresh"
            ):
                self.app.tags_tab.refresh()
            if hasattr(self.app, "refresh_dashboard"):
                self.app.refresh_dashboard()
            elif hasattr(self.app, "dashboard_tab") and hasattr(
                self.app.dashboard_tab, "refresh"
            ):
                self.app.dashboard_tab.refresh()

    def _run_vision_indexer(self):
        from catalogue_app.vision_indexer import VisionIndexerThread, test_vision_api

        ok_api, err_api = test_vision_api()
        if not ok_api:
            messagebox.showerror(
                APP_NAME,
                f"Impossible de démarrer l'indexation visuelle IA.\n\n{err_api}",
            )
            return

        if messagebox.askyesno(
            APP_NAME,
            "Cette opération va envoyer une image de chaque vidéo/photo non indexée à ton IA locale pour qu'elle génère une description textuelle. Cela peut prendre beaucoup de temps. Continuer ?",
        ):
            self.btn_start.config(state="disabled")

            # Create Progress Window
            top = tk.Toplevel(self)
            top.title("Indexation Visuelle IA")
            top.geometry("450x220")
            top.resizable(False, False)
            top.transient(self.winfo_toplevel())

            lbl_title = ttk.Label(
                top,
                text="Analyse Sémantique en cours...",
                font=("TkDefaultFont", 12, "bold"),
            )
            lbl_title.pack(pady=(15, 5))

            lbl_file = ttk.Label(
                top,
                text="Initialisation...",
                font=("TkDefaultFont", 9),
                foreground="#a6adc8",
            )
            lbl_file.pack(pady=5)

            pb = ttk.Progressbar(
                top, orient="horizontal", mode="determinate", length=400
            )
            pb.pack(pady=10)

            lbl_stats = ttk.Label(
                top, text="Temps écoulé : 00:00 | Restant : Calcul..."
            )
            lbl_stats.pack(pady=5)

            def stop_indexer():
                if (
                    hasattr(self, "vision_thread")
                    and self.vision_thread.is_alive()
                ):
                    self.vision_thread.stop()
                top.destroy()
                self.btn_start.config(state="normal")

            btn_cancel = ttk.Button(
                top,
                text="⏸️ Mettre en Pause (Reprendre plus tard)",
                command=stop_indexer,
            )
            btn_cancel.pack(pady=10)

            start_time = time.time()

            def on_progress(count, total, path):
                def update_ui():
                    pb["maximum"] = total
                    pb["value"] = count
                    lbl_file.config(text=f"Fichier {count}/{total} : {path[-45:]}")

                    elapsed = time.time() - start_time
                    if count > 0:
                        speed = count / elapsed
                        remaining = (total - count) / speed if speed > 0 else 0

                        m_el, s_el = divmod(int(elapsed), 60)
                        h_el, m_el = divmod(m_el, 60)

                        str_el = (
                            f"{h_el:02d}:{m_el:02d}:{s_el:02d}"
                            if h_el
                            else f"{m_el:02d}:{s_el:02d}"
                        )

                        if speed <= 0 or remaining > 86400 * 30:  # > 30 jours
                            str_rem = "Calcul / Estimation..."
                        else:
                            m_rem, s_rem = divmod(int(remaining), 60)
                            h_rem, m_rem = divmod(m_rem, 60)
                            d_rem, h_rem = divmod(h_rem, 24)
                            if d_rem > 0:
                                str_rem = f"{d_rem}j {h_rem:02d}h"
                            elif h_rem > 0:
                                str_rem = f"{h_rem:02d}h {m_rem:02d}m"
                            else:
                                str_rem = f"{m_rem:02d}:{s_rem:02d}"

                        lbl_stats.config(
                            text=f"Écoulé : {str_el} | Restant : {str_rem} ({speed:.2f} f/s)"
                        )

                self.after(0, update_ui)

            def on_finish(count):
                def finalize():
                    top.destroy()
                    self.btn_start.config(state="normal")
                    messagebox.showinfo(
                        APP_NAME,
                        f"Indexation terminée. {count} fichiers ont été analysés par l'IA.",
                    )

                self.after(0, finalize)

            def on_error(msg):
                def finalize_err():
                    top.destroy()
                    self.btn_start.config(state="normal")
                    messagebox.showwarning(
                        APP_NAME, f"Indexation IA interrompue :\n\n{msg}"
                    )

                self.after(0, finalize_err)

            self.vision_thread = VisionIndexerThread(
                DB_PATH,
                progress_callback=on_progress,
                finished_callback=on_finish,
                error_callback=on_error,
            )
            self.vision_thread.start()

            top.protocol("WM_DELETE_WINDOW", stop_indexer)

    def _rescan_volume(self):
        sel = self.tv_vol.selection()
        if not sel:
            messagebox.showinfo(
                APP_NAME,
                "Veuillez sélectionner un disque dans la liste à rescanner.",
            )
            return
        vid = int(sel[0])
        name = self.tv_vol.item(sel[0])["values"][0]
        path = getattr(self.app, "online", {}).get(vid)
        if not path:
            messagebox.showerror(
                APP_NAME,
                f"Le disque « {name} » n'est pas branché (ou n'a pas été détecté via 'Détecter les disques branchés').",
            )
            return
        self.var_path.set(path)
        self.var_volname.set(name)
        self.var_inc.set(True)
        self._add_job(start_now=True)

    def _export_all(self):
        p = filedialog.asksaveasfilename(
            defaultextension=".csv",
            initialfile="catalogue_complet.csv",
            filetypes=[("CSV", "*.csv")],
        )
        if not p:
            return
        rows = self.app.con.execute(
            """SELECT f.*, v.name AS volume_name FROM files f
               JOIN volumes v ON v.id=f.volume_id
               ORDER BY v.name, f.rel_path"""
        ).fetchall()
        export_rows(rows, p, con=self.app.con, with_tags=True)
        messagebox.showinfo(APP_NAME, f"{human_count(len(rows))} lignes exportées.")

    def _export_portable_package(self):
        p = filedialog.asksaveasfilename(
            defaultextension=".catpkg",
            initialfile="catalogue_portable.catpkg",
            filetypes=[
                ("Package Catalogue Portable", "*.catpkg"),
                ("Tous", "*.*"),
            ],
        )
        if not p:
            return
        sel = self.tv_vol.selection()
        vids = [int(i) for i in sel] if sel else None
        try:
            from catalogue_app.portability import export_catalog

            if hasattr(self.app, "status") and hasattr(self.app.status, "set"):
                self.app.status.set("Exportation du catalogue portable en cours…")
            self.update_idletasks()
            res = export_catalog(self.app.con, p, volume_ids=vids)
            messagebox.showinfo(
                APP_NAME,
                f"Exportation réussie !\n\n"
                f"• {res['volumes_count']} disque(s)\n"
                f"• {human_count(res['files_count'])} fichiers\n"
                f"• {human_count(res['tags_count'])} étiquettes\n"
                f"Fichier : {os.path.basename(p)}",
            )
        except Exception as e:
            messagebox.showerror(APP_NAME, f"Erreur lors de l'export : {e}")
        finally:
            if hasattr(self.app, "status") and hasattr(self.app.status, "set"):
                self.app.status.set(tools_status())

    def _import_portable_package(self):
        p = filedialog.askopenfilename(
            filetypes=[
                ("Package Catalogue Portable", "*.catpkg"),
                ("Tous", "*.*"),
            ]
        )
        if not p:
            return
        try:
            from catalogue_app.portability import import_catalog

            if hasattr(self.app, "status") and hasattr(self.app.status, "set"):
                self.app.status.set("Importation du catalogue en cours…")
            self.update_idletasks()
            res = import_catalog(self.app.con, p)
            self.refresh_volumes()
            if hasattr(self.app, "refresh_tags"):
                self.app.refresh_tags()
            elif hasattr(self.app, "tags_tab") and hasattr(
                self.app.tags_tab, "refresh"
            ):
                self.app.tags_tab.refresh()
            if hasattr(self.app, "refresh_dashboard"):
                self.app.refresh_dashboard()
            elif hasattr(self.app, "dashboard_tab") and hasattr(
                self.app.dashboard_tab, "refresh"
            ):
                self.app.dashboard_tab.refresh()
            messagebox.showinfo(
                APP_NAME,
                f"Importation terminée avec succès !\n\n"
                f"• {res['volumes_imported']} disque(s) ajouté(s)\n"
                f"• {human_count(res['files_imported'])} fichiers importés\n"
                f"• {human_count(res['tags_imported'])} étiquettes restaurées",
            )
        except Exception as e:
            messagebox.showerror(APP_NAME, f"Erreur lors de l'import : {e}")
        finally:
            if hasattr(self.app, "status") and hasattr(self.app.status, "set"):
                self.app.status.set(tools_status())

    def _open_treemap_for_selected_volume(self):
        sel = self.tv_vol.selection()
        if not sel:
            messagebox.showinfo(
                APP_NAME,
                "Veuillez sélectionner un disque dans la liste pour afficher sa carte visuelle.",
            )
            return
        vid = int(sel[0])
        vname = self.tv_vol.item(sel[0], "values")[0]
        from catalogue_app.treemap import TreemapWindow

        TreemapWindow(self, self.app.con, vid, vname)

    def _export_pdf_for_selected_volume(self):
        sel = self.tv_vol.selection()
        if not sel:
            messagebox.showinfo(
                APP_NAME,
                "Veuillez sélectionner un disque dans la liste pour l'exporter en PDF.",
            )
            return

        try:
            vid = int(sel[0])
            vname = self.tv_vol.item(sel[0], "values")[0]
        except Exception:
            vid = self.tv_vol.item(sel[0], "values")[0]
            vname = self.tv_vol.item(sel[0], "values")[1]

        safe_name = "".join(c if c.isalnum() else "_" for c in str(vname)).lower()

        out_path = filedialog.asksaveasfilename(
            title="Exporter le Rapport (PDF)",
            defaultextension=".pdf",
            initialfile=f"rapport_livraison_{safe_name}.pdf",
            filetypes=[("Fichiers PDF", "*.pdf")],
        )
        if out_path:
            self.btn_start.config(state="disabled")
            if hasattr(self.app, "status") and hasattr(self.app.status, "set"):
                self.app.status.set(f"Génération du rapport PDF pour {vname}...")
            self.update_idletasks()

            def worker():
                try:
                    from catalogue_app.pdf_report import generate_pdf_report

                    generate_pdf_report(self.app.con, vid, vname, out_path)
                    self.after(
                        0,
                        lambda: messagebox.showinfo(
                            APP_NAME,
                            f"Rapport PDF généré avec succès !\n{out_path}",
                        ),
                    )
                    subprocess.Popen(["open", out_path])
                except Exception as e:
                    self.after(
                        0,
                        lambda e=e: messagebox.showerror(
                            "Erreur PDF", f"Échec de l'exportation : {e}"
                        ),
                    )
                finally:
                    self.after(0, lambda: self.btn_start.config(state="normal"))
                    self.after(
                        0,
                        lambda: self.app.status.set("Prêt.")
                        if hasattr(self.app, "status")
                        and hasattr(self.app.status, "set")
                        else None,
                    )

            threading.Thread(target=worker, daemon=True).start()

    def _export_html_for_selected_volume(self):
        sel = self.tv_vol.selection()
        if not sel:
            messagebox.showinfo(
                APP_NAME,
                "Veuillez sélectionner un disque dans la liste pour l'exporter en HTML.",
            )
            return
        vid = int(sel[0])
        vname = self.tv_vol.item(sel[0], "values")[0]

        safe_name = re.sub(r"[^a-zA-Z0-9_-]", "_", vname)
        out_path = filedialog.asksaveasfilename(
            title="Exporter le Backup Visuel (HTML)",
            defaultextension=".html",
            initialfile=f"backup_visuel_{safe_name}.html",
            filetypes=[("Fichiers HTML", "*.html")],
        )

        if out_path:
            if hasattr(self.app, "status") and hasattr(self.app.status, "set"):
                self.app.status.set(f"Génération du fichier HTML pour {vname}...")
            self.update_idletasks()
            try:
                from catalogue_app.export_html import generate_volume_html

                generate_volume_html(self.app.con, vid, vname, out_path)
                messagebox.showinfo(
                    APP_NAME, f"Backup Visuel généré avec succès :\n{out_path}"
                )
            except Exception as e:
                messagebox.showerror(APP_NAME, f"Erreur lors de l'export : {e}")
            finally:
                if hasattr(self.app, "status") and hasattr(self.app.status, "set"):
                    self.app.status.set("Prêt.")

    def _repair(self):
        if not messagebox.askyesno(
            APP_NAME,
            "Vérifier et réparer le catalogue ?\n\n"
            "Cette opération retire les fiches en double pour un même chemin, "
            "supprime les étiquettes orphelines et recalcule les totaux de chaque "
            "disque. Aucun fichier de vos disques n'est touché.",
        ):
            return
        if hasattr(self.app, "status") and hasattr(self.app.status, "set"):
            self.app.status.set("Réparation du catalogue…")
        self.update_idletasks()
        try:
            rep = repair_catalog(self.app.con)
        except Exception as exc:
            messagebox.showerror(APP_NAME, str(exc))
            if hasattr(self.app, "status") and hasattr(self.app.status, "set"):
                self.app.status.set(tools_status())
            return
        self.refresh_volumes()
        if hasattr(self.app, "refresh_tags"):
            self.app.refresh_tags()
        elif hasattr(self.app, "tags_tab") and hasattr(
            self.app.tags_tab, "refresh"
        ):
            self.app.tags_tab.refresh()
        if hasattr(self.app, "_do_search"):
            self.app._do_search()
        elif hasattr(self.app, "search_tab") and hasattr(
            self.app.search_tab, "_do_search"
        ):
            self.app.search_tab._do_search()
        if hasattr(self.app, "status") and hasattr(self.app.status, "set"):
            self.app.status.set(tools_status())
        messagebox.showinfo(
            APP_NAME,
            f'{human_count(rep["removed"])} fiche(s) en double retirée(s), '
            f'soit {human_size(rep["size_removed"])} de volume fantôme.\n\n'
            f'Catalogue après réparation : {human_count(rep["files"])} fichiers, '
            f'{human_size(rep["size"])}.',
        )

    def _retag(self):
        if not messagebox.askyesno(
            APP_NAME,
            "Recalculer toutes les étiquettes automatiques ?\n\n"
            "Vos étiquettes manuelles sont conservées.\n"
            "L'opération peut durer quelques minutes.",
        ):
            return
        self.log("Recalcul des étiquettes…")

        def worker():
            try:
                rcon = connect()
                n = retag_all(rcon)
                rcon.close()
                self.app.msgq.put(
                    (
                        "log",
                        (
                            None,
                            f"Étiquettes recalculées pour "
                            f"{human_count(n)} fichiers.",
                        ),
                    )
                )
            except Exception as exc:
                self.app.msgq.put(("error", str(exc)))
            finally:
                self.app.msgq.put(("job_done", (None, None)))

        threading.Thread(target=worker, daemon=True).start()
