import os
import sys
import time
import subprocess
import threading
import json
import re
import shutil
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

from catalogue_app.ui.tabs.base_tab import BaseTab
from catalogue_app.ui.components import MultiSelectMenu
from catalogue_app.config import APP_NAME
from catalogue_app.utils import human_size, fmt_date, normalize
from catalogue_app.queries import list_projects, export_rows, reveal, full_path_of
from catalogue_app.project_relinker import locate_project_media
from catalogue_app.agents import ProjectAgent


class ProjectsTab(BaseTab):
    def __init__(self, parent, app, **kwargs):
        self.proj_rows = []
        super().__init__(parent, app, **kwargs)

    @property
    def online(self):
        return getattr(self.app, "online", None)

    def _refresh_online(self, silent=False):
        if hasattr(self.app, "_refresh_online"):
            return self.app._refresh_online(silent=silent)

    def _build_ui(self):
        f = self
        bar = ttk.Frame(f, padding=8)
        bar.pack(fill="x")
        ttk.Label(bar, text="Filtrer :").pack(side="left")
        self.var_pq = tk.StringVar()
        e = ttk.Entry(bar, textvariable=self.var_pq, width=30)
        e.pack(side="left", padx=6)
        e.bind("<Return>", lambda _e: self._do_proj())
        
        ttk.Label(bar, text="Disque(s) :").pack(side="left", padx=(10, 0))
        self.cmb_projvol = MultiSelectMenu(bar, text="Sélectionner les disques")
        self.cmb_projvol.pack(side="left", padx=6)
        self.cmb_projvol.on_change = lambda: self._do_proj()

        ttk.Button(bar, text="Afficher les projets", command=self._do_proj).pack(side="left", padx=6)
        ttk.Button(bar, text="Exporter (CSV)", command=self._export_proj).pack(side="left")
        ttk.Button(bar, text="📂 Ouvrir dans le Finder", command=self._reveal_proj_sel).pack(side="left", padx=6)
        ttk.Button(bar, text="🔗 Localiser les Médias", command=self._locate_project_media).pack(side="left", padx=6)
        self.lbl_proj = ttk.Label(bar, text="")
        self.lbl_proj.pack(side="right")
        
        # Project Agent Frame
        ai_proj = ttk.LabelFrame(f, text=" Agent Chef de Projet IA ", padding=5)
        ai_proj.pack(fill="x", padx=8, pady=4)
        self.txt_proj_agent = tk.Text(ai_proj, height=2, wrap="word", bg="#1e1e2e", fg="#cba6f7", font=("TkDefaultFont", 11, "italic"))
        self.txt_proj_agent.pack(fill="x", expand=True, side="left", padx=(0, 10))
        self.txt_proj_agent.insert("1.0", "L'agent peut faire le point sur tes projets en cours...")
        self.txt_proj_agent.config(state="disabled")
        
        self.btn_proj_agent = ttk.Button(ai_proj, text="🤖 Demander Conseil IA", command=self.ask_proj_agent)
        self.btn_proj_agent.pack(side="right")

        cols = ("nom", "logiciel", "disque", "dossier", "taille", "modifie")
        heads = ("Projet", "Logiciel", "Disque", "Dossier", "Taille", "Modifié le")
        self.tv_proj = self._make_tree(f, cols, heads, (250, 180, 130, 350, 90, 100))
        self.tv_proj.bind("<Double-1>", self._reveal_proj_sel)

        # Initialisation options disques si connexion DB disponible
        if hasattr(self.app, 'con') and self.app.con:
            try:
                vol_dict = {r["id"]: r["name"] for r in self.app.con.execute("SELECT id, name FROM volumes ORDER BY name")}
                self.cmb_projvol.set_options(vol_dict)
            except Exception:
                pass

    def ask_proj_agent(self):
        self.btn_proj_agent.config(text="Analyse...", state="disabled")
        self.update_idletasks()

        sel = self.tv_proj.selection()
        selected_row = None
        if sel and hasattr(self, "proj_rows") and self.proj_rows:
            selected_row = dict(self.proj_rows[int(sel[0])])

        context_list = []
        for grp in self.tv_proj.get_children()[:10]:
            vals = self.tv_proj.item(grp, "values")
            context_list.append({"nom": vals[0], "logiciel": vals[1], "disque": vals[2], "modifie": vals[5]})

        online_snapshot = dict(getattr(self.app, "online", getattr(self, "online", {})) or {})

        def worker():
            local_con = None
            try:
                local_con = connect()
                agent = ProjectAgent()

                selected_info = None
                if selected_row:
                    reloc = locate_project_media(
                        local_con,
                        selected_row["name"],
                        full_path_of(local_con, selected_row, online_snapshot) or "",
                        online_snapshot
                    )
                    selected_info = reloc

                resp = agent.analyze_projects(context_list, selected_project_report=selected_info)
                self.after(0, lambda r=resp, s=selected_info: self._update_proj_txt(r, selected_info=s))
            except Exception as e:
                err_msg = str(e)
                self.after(0, lambda err=err_msg: self._update_proj_txt(f"Erreur Agent: {err}"))
            finally:
                if local_con is not None:
                    try:
                        local_con.close()
                    except Exception:
                        pass
                self.after(0, lambda: self.btn_proj_agent.config(text="🤖 Demander Conseil IA", state="normal"))

        threading.Thread(target=worker, daemon=True).start()

    _ask_proj_agent = ask_proj_agent

    def _update_proj_txt(self, t, selected_info=None):
        match = re.search(r'```action\s*(.*?)\s*```', t, re.DOTALL)
        action_data = None
        if match:
            try:
                action_data = json.loads(match.group(1))
                t = t.replace(match.group(0), "\n[Action Détectée : En attente de validation]")
            except Exception:
                pass

        self.txt_proj_agent.config(state="normal")
        self.txt_proj_agent.delete("1.0", "end")
        self.txt_proj_agent.insert("1.0", t)
        self.txt_proj_agent.config(state="disabled")

        if action_data:
            cmd = action_data.get("command")
            if cmd == "ARCHIVE_PROJECT":
                path_to_archive = action_data.get("path")
                if messagebox.askyesno("Agent Projet", f"L'agent propose d'archiver (ZIP) le dossier suivant :\n\n{path_to_archive}\n\nAutoriser l'agent à effectuer cette action ?"):
                    try:
                        if os.path.exists(path_to_archive):
                            shutil.make_archive(path_to_archive, 'zip', path_to_archive)
                            messagebox.showinfo("Succès", f"Le dossier a été archivé en ZIP à côté du dossier original.\n{path_to_archive}.zip")
                        else:
                            messagebox.showwarning("Introuvable", "Le dossier n'existe pas ou le disque n'est pas branché.")
                    except Exception as e:
                        messagebox.showerror("Erreur", f"L'agent n'a pas pu archiver le dossier : {e}")
            elif cmd == "EXPORT_PROJECT_MEMO":
                pname = action_data.get("project", "Projet")
                if messagebox.askyesno("Agent Chef de Projet", f"L'agent propose d'exporter la Fiche d'Intervention Monteur pour « {pname} » (liste des disques physiques et rushes).\n\nExporter le mémo ?"):
                    p = filedialog.asksaveasfilename(
                        defaultextension=".md",
                        initialfile=f"Fiche_Monteur_{pname}.md",
                        filetypes=[("Document Markdown", "*.md"), ("Fichier Texte", "*.txt")]
                    )
                    if p:
                        try:
                            with open(p, "w", encoding="utf-8") as fh:
                                fh.write(f"# 🎬 Fiche d'Intervention Monteur : {pname}\n\n")
                                fh.write(f"- Date d'émission : {time.strftime('%Y-%m-%d %H:%M')}\n")
                                if selected_info:
                                    fh.write(f"- Rushes indexés : {selected_info.get('total_media_found', 0)}\n")
                                    fh.write(f"- Volume total : {selected_info.get('total_size_human', '0 Mo')}\n\n")
                                    fh.write("### 💽 Disques requis pour le montage :\n")
                                    for d in selected_info.get("drives_to_plug", []):
                                        fh.write(f"- [ ] 🔴 **DISQUE À BRANCHER** : {d}\n")
                                    for d in selected_info.get("drives_online", []):
                                        fh.write(f"- [x] 🟢 **DISQUE DÉJÀ BRANCHÉ** : {d}\n")
                                fh.write("\n---\n*Généré automatiquement par l'Agent Chef de Projet de Repertoir.*\n")
                            if messagebox.askyesno("Succès", f"Fiche monteur enregistrée !\n\nL'afficher dans le Finder ?"):
                                subprocess.Popen(["open", "-R", p])
                        except Exception as err:
                            messagebox.showerror("Erreur", f"Impossible d'écrire le mémo : {err}")

    def _do_proj(self):
        sel_vols = []
        if hasattr(self, 'cmb_projvol'):
            sel_vols = self.cmb_projvol.get_selected()
            
        q = self.var_pq.get().strip().lower()
        # On passe sel_vols à la db
        rows = list_projects(self.app.con, q, sel_vols)
        self.proj_rows = rows
        for i in self.tv_proj.get_children():
            self.tv_proj.delete(i)
        for idx, r in enumerate(rows):
            self.tv_proj.insert("", "end", iid=str(idx), values=(
                r["name"], r["app"] or "", r["volume_name"], r["folder"],
                human_size(r["size"]), fmt_date(r["mtime"])))
        self.lbl_proj.config(text=f"{len(rows)} projet(s)")

    def _locate_project_media(self):
        sel = self.tv_proj.selection()
        if not sel or not hasattr(self, "proj_rows") or not self.proj_rows:
            messagebox.showinfo(APP_NAME, "Veuillez sélectionner un projet dans la liste pour localiser ses médias.")
            return
        r = self.proj_rows[int(sel[0])]
        pname = r["name"]
        ppath = full_path_of(self.app.con, r, self.online) or ""
        
        report = locate_project_media(self.app.con, pname, ppath, self.online)
        
        top = tk.Toplevel(self)
        top.title(f"Localisation des Médias — {pname}")
        top.geometry("640x480")
        top.transient(self.winfo_toplevel())
        
        f = ttk.Frame(top, padding=15)
        f.pack(fill="both", expand=True)
        
        ttk.Label(f, text=f"Projet : {pname}", font=("TkDefaultFont", 12, "bold")).pack(anchor="w", pady=(0, 5))
        
        tot_txt = f"{report['total_media_found']} média(s) identifié(s) dans le catalogue ({report['total_size_human']})"
        ttk.Label(f, text=tot_txt, foreground="#89b4fa", font=("TkDefaultFont", 10)).pack(anchor="w", pady=(0, 10))
        
        if report["drives_to_plug"]:
            alert_frame = ttk.LabelFrame(f, text="⚠️ Action requise pour monter ce projet", padding=10)
            alert_frame.pack(fill="x", pady=(0, 10))
            drives_str = ", ".join(f'« {d} »' for d in report["drives_to_plug"])
            ttk.Label(alert_frame, text=f"Certains médias sont sur des disques débranchés !\nVeuillez brancher les disques suivants :\n👉 {drives_str}", foreground="#f38ba8").pack(anchor="w")
        else:
            ok_lbl = ttk.Label(f, text="✅ Tous les disques nécessaires sont actuellement branchés et en ligne !", foreground="#a6e3a1")
            ok_lbl.pack(anchor="w", pady=(0, 10))
            
        cols = ("disque", "statut", "fichiers", "taille")
        heads = ("Disque", "Statut", "Rushes trouvés", "Poids total")
        tv = ttk.Treeview(f, columns=cols, show="headings", height=8)
        for c_id, h, w in zip(cols, heads, (200, 140, 120, 100)):
            tv.heading(c_id, text=h)
            tv.column(c_id, width=w, anchor="w")
        tv.tag_configure("online", foreground="#a6e3a1")
        tv.tag_configure("offline", foreground="#fab387")
        tv.pack(fill="both", expand=True, pady=5)
        
        for v in report["volumes_distribution"]:
            stat = "🟢 En ligne (Branché)" if v["is_online"] else "🟡 Hors ligne (À brancher)"
            tag = "online" if v["is_online"] else "offline"
            tv.insert("", "end", values=(v["volume_name"], stat, f"{v['count']} rushes", human_size(v['size'])), tags=(tag,))
            
        btn_box = ttk.Frame(f)
        btn_box.pack(fill="x", pady=(10, 0))
        ttk.Button(btn_box, text="Fermer", command=top.destroy).pack(side="right")

    def _reveal_proj_sel(self, _e=None):
        sel = self.tv_proj.selection()
        if not sel or not hasattr(self, "proj_rows") or not self.proj_rows:
            return
        r = self.proj_rows[int(sel[0])]
        if not reveal(full_path_of(self.app.con, r, self.online)):
            self._refresh_online(silent=True)
            if reveal(full_path_of(self.app.con, r, self.online)):
                return
            messagebox.showinfo(
                APP_NAME,
                f"Le disque « {r['volume_name']} » n'est pas branché.\n\n"
                f"Branchez-le pour accéder à ce projet :\n{r['rel_path']}")

    def _export_proj(self):
        if not self.proj_rows:
            return
        p = filedialog.asksaveasfilename(defaultextension=".csv", initialfile="projets.csv",
                                         filetypes=[("CSV", "*.csv")])
        if p:
            export_rows(self.proj_rows, p, con=self.app.con, with_tags=True)
            messagebox.showinfo(APP_NAME, "Export terminé.")

    def _make_tree(self, parent, cols, heads, widths, selectmode="extended"):
        if hasattr(self.app, "_make_tree"):
            return self.app._make_tree(parent, cols, heads, widths, selectmode=selectmode)
        wrap = ttk.Frame(parent)
        wrap.pack(fill="both", expand=True, padx=8, pady=4)
        tv = ttk.Treeview(wrap, columns=cols, show="headings", selectmode=selectmode)
        for c, h, w in zip(cols, heads, widths):
            tv.heading(c, text=h)
            tv.column(c, width=w, anchor="w")
        vs = ttk.Scrollbar(wrap, orient="vertical", command=tv.yview)
        hs = ttk.Scrollbar(wrap, orient="horizontal", command=tv.xview)
        tv.configure(yscrollcommand=vs.set, xscrollcommand=hs.set)
        tv.grid(row=0, column=0, sticky="nsew")
        vs.grid(row=0, column=1, sticky="ns")
        hs.grid(row=1, column=0, sticky="we")
        wrap.rowconfigure(0, weight=1)
        wrap.columnconfigure(0, weight=1)
        if hasattr(self.app, "_make_sortable"):
            self.app._make_sortable(tv, cols, heads)
        else:
            self._make_sortable(tv, cols, heads)
        return tv

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
            for c in cols:
                h = heads[cols.index(c)]
                arrow = " ▼" if (state["desc"] and state["col"] == c) else (" ▲" if state["col"] == c else "")
                tv.heading(c, text=h + arrow)

        for col in cols:
            tv.heading(col, command=lambda c=col: sort_by(c))

    def refresh(self):
        """Rafraîchit la liste des volumes et recharge les projets."""
        if hasattr(self, 'cmb_projvol') and hasattr(self.app, 'con') and self.app.con:
            try:
                vol_dict = {r["id"]: r["name"] for r in self.app.con.execute("SELECT id, name FROM volumes ORDER BY name")}
                self.cmb_projvol.set_options(vol_dict)
            except Exception:
                pass
        self._do_proj()
