import os
import sys
import subprocess
import threading
import csv
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

from catalogue_app.ui.tabs.base_tab import BaseTab
from catalogue_app.config import *
from catalogue_app.utils import *
from catalogue_app.db import *
from catalogue_app.queries import *
from catalogue_app.scanner import *

from catalogue_app.ui.components import MultiSelectMenu

class DuplicatesTab(BaseTab):
    def _build_ui(self):
        f = self
        self.var_dupmode = tk.StringVar(value="file")

        # Ligne 1 : Mode & Paramètres de base
        bar1 = ttk.Frame(f, padding=(8, 6, 8, 2))
        bar1.pack(fill="x")

        ttk.Label(bar1, text="Mode :", font=("TkDefaultFont", 9, "bold")).pack(side="left", padx=(0, 4))
        ttk.Radiobutton(bar1, text="📄 Par Fichier", variable=self.var_dupmode, value="file",
                        command=self._on_change_dupmode).pack(side="left", padx=(0, 4))
        ttk.Radiobutton(bar1, text="📁 Par Dossier", variable=self.var_dupmode, value="folder",
                        command=self._on_change_dupmode).pack(side="left", padx=(0, 10))

        ttk.Separator(bar1, orient="vertical").pack(side="left", fill="y", padx=6)

        ttk.Label(bar1, text="Garder :").pack(side="left", padx=(4, 2))
        self.var_keep = tk.StringVar(value="1")
        ttk.Spinbox(bar1, from_=1, to=10, width=3, textvariable=self.var_keep).pack(side="left", padx=2)

        ttk.Label(bar1, text="Taille min (Mo) :").pack(side="left", padx=(10, 2))
        self.var_dupmb = tk.StringVar(value="20")
        ttk.Entry(bar1, textvariable=self.var_dupmb, width=4).pack(side="left", padx=2)
        
        self.var_strict = tk.BooleanVar(value=True)
        self.chk_strict = ttk.Checkbutton(bar1, text="Nom identique (Fichiers)", variable=self.var_strict)
        self.chk_strict.pack(side="left", padx=(10, 4))

        self.btn_plan = ttk.Button(bar1, text="⚡ Calculer le plan", command=self._do_plan)
        self.btn_plan.pack(side="left", padx=(12, 4))
        ttk.Button(bar1, text="🔍 Vérifier ce groupe", command=self._verify_group).pack(side="left", padx=4)
        ttk.Button(bar1, text="📂 Ouvrir dans Finder", command=self._reveal_dup_sel).pack(side="left", padx=4)
        ttk.Button(bar1, text="📊 Exporter CSV", command=self._export_plan).pack(side="left", padx=4)

        # Ligne 2 : Filtres (Disques, Catégories, Extensions libres)
        bar2 = ttk.Frame(f, padding=(8, 2, 8, 6))
        bar2.pack(fill="x")

        ttk.Label(bar2, text="Filtres :", font=("TkDefaultFont", 9, "bold")).pack(side="left", padx=(0, 4))
        ttk.Label(bar2, text="Disques :").pack(side="left", padx=(4, 2))
        self.cmb_dupvol = MultiSelectMenu(bar2, text="(tous)", popup_title="Filtrer par disques", empty_label="(tous)")
        self.cmb_dupvol.pack(side="left", padx=2)

        ttk.Label(bar2, text="Types :").pack(side="left", padx=(10, 2))
        self.cmb_dupcat = MultiSelectMenu(bar2, text="(tous les types)", popup_title="Filtrer par catégories", empty_label="(tous les types)")
        self.cmb_dupcat.pack(side="left", padx=2)
        self.cmb_dupcat.set_options(DUP_CATEGORIES)

        ttk.Label(bar2, text="Extensions :").pack(side="left", padx=(10, 2))
        self.var_dupext = tk.StringVar(value="")
        e_dupext = ttk.Entry(bar2, textvariable=self.var_dupext, width=15)
        e_dupext.pack(side="left", padx=2)
        e_dupext.bind("<Return>", lambda _e: self._do_plan())
        ttk.Label(bar2, text="(ex: .mov, .iso, .zip)", foreground="#888").pack(side="left", padx=(2, 6))

        def _clear_dup_filters():
            for v in self.cmb_dupvol.vars.values():
                v.set(False)
            self.cmb_dupvol._update_text()
            for v in self.cmb_dupcat.vars.values():
                v.set(False)
            self.cmb_dupcat._update_text()
            self.var_dupext.set("")
            self._do_plan()

        ttk.Button(bar2, text="✕ Effacer filtres", command=_clear_dup_filters).pack(side="left", padx=4)

        self.lbl_dupsum = ttk.Label(f, text="", padding=(12, 2), style="Big.TLabel")
        self.lbl_dupsum.pack(anchor="w")
        ttk.Label(f, text="L'application ne supprime jamais rien : elle indique quelles copies "
                          "retirer, disque par disque. Vérifiez un groupe avant d'agir.",
                  foreground="#666", padding=(12, 0)).pack(anchor="w")

        # Duplicate Agent Frame
        ai_dup = ttk.LabelFrame(f, text=" Agent Nettoyeur IA ", padding=5)
        ai_dup.pack(fill="x", padx=8, pady=4)
        self.txt_dup_agent = __import__("tkinter").Text(ai_dup, height=2, wrap="word", bg="#1e1e2e", fg="#f9e2af", font=("TkDefaultFont", 11, "italic"))
        self.txt_dup_agent.pack(fill="x", expand=True, side="left", padx=(0,10))
        self.txt_dup_agent.insert("1.0", "L'agent peut t'aider à choisir quel doublon conserver...")
        self.txt_dup_agent.config(state="disabled")
        
        def ask_dup_agent():
            self.btn_dup_agent.config(text="Analyse...", state="disabled")
            self.update_idletasks()
            sel = self.tv_dup.selection()
            def worker():
                try:
                    import sqlite3
                    from catalogue_app.config import DB_PATH
                    local_con = sqlite3.connect(DB_PATH)
                    local_con.row_factory = sqlite3.Row
                    
                    from catalogue_app.agents import DuplicateAgent
                    agent = DuplicateAgent()
                    
                    context_list = []
                    if sel and hasattr(self, "plan") and self.plan:
                        g = self.plan[int(sel[0])]
                        all_copies = g.get("keep", []) + g.get("drop", [])
                        is_fld = (g.get("type") == "folder")
                        for r in all_copies:
                            full = full_path_of(local_con, r, getattr(self.app, 'online', getattr(self, 'online', False)))
                            is_online = bool(full and os.path.exists(full))
                            item_p = full or r.get("folder") or r.get("rel_path", r.get("name"))
                            sz = r.get("total_size") if "total_size" in r else r.get("size", 0)
                            cd = {
                                "chemin": item_p,
                                "disque": r.get("volume_name", "?"),
                                "taille": human_size(sz),
                                "online": is_online
                            }
                            if is_fld:
                                cd["type"] = "dossier"
                                cd["fichiers"] = r.get("file_count", 0)
                            context_list.append(cd)
                    elif hasattr(self, "current_dup_items") and self.current_dup_items:
                        for r in self.current_dup_items:
                            full = full_path_of(local_con, r, getattr(self.app, 'online', getattr(self, 'online', False)))
                            item_p = full or r.get("folder") or r.get("rel_path", r.get("name"))
                            sz = r.get("total_size") if "total_size" in r else r.get("size", 0)
                            context_list.append({
                                "chemin": item_p,
                                "disque": r.get("volume_name", "?"),
                                "taille": human_size(sz),
                                "online": bool(full and os.path.exists(full))
                            })
                        
                    resp = agent.analyze_duplicates(context_list)
                    self.after(0, lambda r=resp: _update_dup_txt(r))
                except Exception as e:
                    err_msg = str(e)
                    self.after(0, lambda err=err_msg: _update_dup_txt(f"Erreur Agent: {err}"))
                finally:
                    if 'local_con' in locals() and local_con:
                        local_con.close()
                    self.after(0, lambda: self.btn_dup_agent.config(text="🤖 Demander Conseil IA", state="normal"))
                    
            def _update_dup_txt(t):
                import re as re_mod, json
                match = re_mod.search(r'```action\s*(.*?)\s*```', t, re_mod.DOTALL)
                action_data = None
                if match:
                    try:
                        action_data = json.loads(match.group(1))
                        t = t.replace(match.group(0), "\n[Action Détectée : En attente de validation]")
                    except:
                        pass
                        
                self.txt_dup_agent.config(state="normal")
                self.txt_dup_agent.delete("1.0", "end")
                self.txt_dup_agent.insert("1.0", t)
                self.txt_dup_agent.config(state="disabled")
                
                cmd = action_data.get("command") if action_data else None
                if cmd in ("TRASH_FILE", "DELETE_FILE"):
                    path_to_trash = action_data.get("path")
                    reason = action_data.get("reason", "Nettoyage de doublon")
                    prompt_msg = (
                        f"L'Agent Nettoyeur propose de déplacer ce doublon vers la Corbeille macOS :\n\n"
                        f"📁 Élément : {path_to_trash}\n"
                        f"💡 Motif : {reason}\n\n"
                        f"Déplacer dans la Corbeille ?"
                    )
                    if messagebox.askyesno("Agent Nettoyeur (Corbeille macOS)", prompt_msg):
                        from catalogue_app.utils import move_to_trash
                        ok, msg = move_to_trash(path_to_trash)
                        if ok:
                            messagebox.showinfo("Corbeille macOS", f"Succès : {msg}\n\nL'élément peut être restauré depuis la Corbeille si nécessaire.")
                            self._do_plan()
                        else:
                            messagebox.showerror("Erreur", msg)
            
            import threading
            threading.Thread(target=worker, daemon=True).start()
            
        self.btn_dup_agent = ttk.Button(ai_dup, text="🤖 Demander Conseil IA", command=ask_dup_agent)
        self.btn_dup_agent.pack(side="right")


        paned = ttk.Panedwindow(f, orient="horizontal")
        paned.pack(fill="both", expand=True, padx=8, pady=6)

        left = ttk.Labelframe(paned, text="Groupes de doublons", padding=4)
        cols = ("nom", "copies", "disques", "info_col", "taille", "recup")
        self.tv_dup = ttk.Treeview(left, columns=cols, show="headings", selectmode="browse")
        for c, h, w in zip(cols, ("Fichier", "Copies", "Disques", "Type", "Taille", "Récupérable"),
                           (340, 60, 60, 85, 90, 100)):
            self.tv_dup.heading(c, text=h)
            min_w = max(50, int(w * 0.6))
            self.tv_dup.column(c, width=w, minwidth=min_w, anchor="w", stretch=True)
        sb1 = ttk.Scrollbar(left, orient="vertical", command=self.tv_dup.yview)
        self.tv_dup.configure(yscrollcommand=sb1.set)
        self.tv_dup.pack(side="left", fill="both", expand=True)
        sb1.pack(side="right", fill="y")
        self.tv_dup.bind("<<TreeviewSelect>>", self._show_group)
        if hasattr(self, '_make_sortable'):
            self.app._make_sortable(self.tv_dup, cols, ("Fichier", "Copies", "Disques", "Type", "Taille", "Récupérable"))
        elif hasattr(self.app, '_make_sortable'):
            self.app._make_sortable(self.tv_dup, cols, ("Fichier", "Copies", "Disques", "Type", "Taille", "Récupérable"))
        try:
            from catalogue_app.ui.components.tooltip import attach_treeview_tooltip
            attach_treeview_tooltip(self.tv_dup)
        except Exception:
            pass
        paned.add(left, weight=3)

        right = ttk.Labelframe(paned, text="Détail : à conserver / à retirer", padding=4)
        cols2 = ("action", "disque", "dossier", "nom", "taille")
        self.tv_dupdet = ttk.Treeview(right, columns=cols2, show="headings")
        for c, h, w in zip(cols2, ("Action", "Disque", "Dossier / Emplacement", "Nom / Éléments", "Taille"),
                           (85, 125, 320, 280, 90)):
            self.tv_dupdet.heading(c, text=h)
            min_w = max(50, int(w * 0.6))
            self.tv_dupdet.column(c, width=w, minwidth=min_w, anchor="w", stretch=True)
        self.tv_dupdet.tag_configure("keep", background="#e8f5e9", foreground="black")
        self.tv_dupdet.tag_configure("drop", background="#ffebee", foreground="black")
        sb2 = ttk.Scrollbar(right, orient="vertical", command=self.tv_dupdet.yview)
        self.tv_dupdet.configure(yscrollcommand=sb2.set)
        self.tv_dupdet.pack(side="left", fill="both", expand=True)
        self.tv_dupdet.bind("<Double-1>", self._on_dupdet_double_click)
        self.tv_dupdet.bind("<space>", lambda _e: self._quicklook_dup_sel())
        try:
            from catalogue_app.ui.components.tooltip import attach_treeview_tooltip
            attach_treeview_tooltip(self.tv_dupdet)
        except Exception:
            pass
        
        # --- Menu Contextuel Doublons ---
        self.menu_dup = tk.Menu(right, tearoff=0)
        self.menu_dup.add_command(label="👁️ Coup d'œil (Espace)", command=self._quicklook_dup_sel)
        self.menu_dup.add_command(label="📂 Ouvrir dans le Finder", command=self._reveal_dup_sel)
        self.menu_dup.add_command(label="📋 Copier le chemin", command=self._copy_dup_path)
        self.menu_dup.add_separator()
        self.menu_dup.add_command(label="🔍 Explorer les fichiers du dossier...", command=self._inspect_dup_folder)
        
        def popup_dup(event):
            iid = self.tv_dupdet.identify_row(event.y)
            if iid:
                if iid not in self.tv_dupdet.selection():
                    self.tv_dupdet.selection_set(iid)
                self.menu_dup.post(event.x_root, event.y_root)
        if sys.platform == "darwin":
            self.tv_dupdet.bind("<Button-2>", popup_dup)
            self.tv_dupdet.bind("<Control-Button-1>", popup_dup)
        else:
            self.tv_dupdet.bind("<Button-3>", popup_dup)
        sb2.pack(side="right", fill="y")
        if hasattr(self, '_make_sortable'):
            self.app._make_sortable(self.tv_dupdet, cols2, ("Action", "Disque", "Dossier / Emplacement", "Nom / Éléments", "Taille"))
        elif hasattr(self.app, '_make_sortable'):
            self.app._make_sortable(self.tv_dupdet, cols2, ("Action", "Disque", "Dossier / Emplacement", "Nom / Éléments", "Taille"))
        paned.add(right, weight=4)

        bot = ttk.Labelframe(f, text="Espace récupérable par disque", padding=4)
        bot.pack(fill="x", padx=8, pady=(0, 8))
        cols3 = ("disque", "fichiers", "espace")
        self.tv_dupvol = ttk.Treeview(bot, columns=cols3, show="headings", height=6)
        for c, h, w in zip(cols3, ("Disque", "Copies en trop", "Espace libérable"),
                           (280, 140, 160)):
            self.tv_dupvol.heading(c, text=h)
            min_w = max(50, int(w * 0.6))
            self.tv_dupvol.column(c, width=w, minwidth=min_w, anchor="w", stretch=True)
        self.tv_dupvol.pack(fill="x")
        if hasattr(self, '_make_sortable'):
            self.app._make_sortable(self.tv_dupvol, cols3, ("Disque", "Copies en trop", "Espace libérable"))
        elif hasattr(self.app, '_make_sortable'):
            self.app._make_sortable(self.tv_dupvol, cols3, ("Disque", "Copies en trop", "Espace libérable"))
        try:
            from catalogue_app.ui.components.tooltip import attach_treeview_tooltip
            attach_treeview_tooltip(self.tv_dupvol)
        except Exception:
            pass

    def _on_change_dupmode(self):
        mode = self.var_dupmode.get()
        if mode == "folder":
            self.tv_dup.heading("nom", text="Dossier")
            self.tv_dup.heading("info_col", text="Nb Fichiers")
            self.tv_dup.heading("taille", text="Taille dossier")
            if hasattr(self, 'chk_strict'):
                self.chk_strict.config(state="disabled")
            if self.var_keep.get() == "2":
                self.var_keep.set("1")
        else:
            self.tv_dup.heading("nom", text="Fichier")
            self.tv_dup.heading("info_col", text="Type")
            self.tv_dup.heading("taille", text="Taille")
            if hasattr(self, 'chk_strict'):
                self.chk_strict.config(state="normal")
            if self.var_keep.get() == "1":
                self.var_keep.set("2")
        self._do_plan()

    def _on_dupdet_double_click(self, event=None):
        if self.var_dupmode.get() == "folder":
            self._inspect_dup_folder()
        else:
            self._reveal_dup_sel()

    def _update_plan_ui(self, plan, is_folder, keep):
        self.plan = plan
        if getattr(self, '_pop_timer', None):
            try:
                self.after_cancel(self._pop_timer)
            except Exception:
                pass
            self._pop_timer = None

        for i in self.tv_dup.get_children():
            self.tv_dup.delete(i)
        for i in self.tv_dupdet.get_children():
            self.tv_dupdet.delete(i)

        total = sum(g["reclaim"] for g in self.plan)

        for i in self.tv_dupvol.get_children():
            self.tv_dupvol.delete(i)
        for vol, n, size in plan_by_volume(self.plan):
            self.tv_dupvol.insert("", "end", values=(vol, human_count(n), human_size(size)))

        item_noun = "dossier(s)" if is_folder else "fichier(s)"
        self.lbl_dupsum.config(
            text=f"{human_count(len(self.plan))} {item_noun} en surnombre  —  "
                 f"espace libérable en gardant {keep} copie(s) : {human_size(total)}")

        CHUNK_SIZE = 50
        def _populate_batch(start_idx):
            if not hasattr(self, "plan") or not self.plan:
                return
            end_idx = min(start_idx + CHUNK_SIZE, len(self.plan))
            for idx in range(start_idx, end_idx):
                g = self.plan[idx]
                if is_folder:
                    info_val = f"{g.get('file_count', 0)} fichiers"
                else:
                    info_val = g.get("category") or g.get("ext") or "—"
                self.tv_dup.insert("", "end", iid=str(idx), values=(
                    g["name"], g["copies"], g["volumes"], info_val, human_size(g["size"]),
                    human_size(g["reclaim"])))
            
            if end_idx < len(self.plan):
                self._pop_timer = self.after(5, lambda: _populate_batch(end_idx))

        _populate_batch(0)

        if hasattr(self, 'app') and hasattr(self.app, 'status'):
            self.app.status.set(tools_status())
        elif hasattr(self, 'status'):
            self.app.status.set(tools_status())

    def _do_plan(self):
        mode = self.var_dupmode.get()
        is_folder = (mode == "folder")
        try:
            keep = max(1, int(self.var_keep.get()))
        except ValueError:
            keep = 1 if is_folder else 2

        self.lbl_dupsum.config(text="⏳ Calcul du plan de dédoublonnage en cours...")
        if hasattr(self, 'btn_plan'):
            self.btn_plan.config(state="disabled")

        if hasattr(self, 'app') and hasattr(self.app, 'status'):
            self.app.status.set("Calcul du plan de dédoublonnage…")
        elif hasattr(self, 'status'):
            self.app.status.set("Calcul du plan de dédoublonnage…")

        selected_vols = self.cmb_dupvol.get_selected()
        if not selected_vols or (self.cmb_dupvol.options and len(selected_vols) == len(self.cmb_dupvol.options)):
            selected_vols = None

        categories = self.cmb_dupcat.get_selected()
        if not categories or (self.cmb_dupcat.options and len(categories) == len(self.cmb_dupcat.options)):
            categories = None
        extensions = self.var_dupext.get().strip()
        min_mb = self.var_dupmb.get() or 0

        def worker():
            local_con = None
            try:
                import sqlite3
                from catalogue_app.config import DB_PATH
                local_con = sqlite3.connect(DB_PATH)
                local_con.row_factory = sqlite3.Row

                if is_folder:
                    plan = plan_folder_deduplication(
                        local_con,
                        keep=keep,
                        min_size_mb=min_mb,
                        selected_vols=selected_vols,
                        categories=categories,
                        extensions=extensions
                    )
                else:
                    plan = plan_deduplication(
                        local_con, 
                        keep=keep, 
                        min_size_mb=min_mb,
                        selected_vols=selected_vols,
                        categories=categories,
                        extensions=extensions,
                        strict_name=self.var_strict.get()
                    )
                self.after(0, lambda p=plan: self._update_plan_ui(p, is_folder, keep))
            except Exception as e:
                err_msg = str(e)
                self.after(0, lambda err=err_msg: self.lbl_dupsum.config(text=f"❌ Erreur lors du calcul : {err}"))
            finally:
                if local_con:
                    local_con.close()
                if hasattr(self, 'btn_plan'):
                    self.after(0, lambda: self.btn_plan.config(state="normal"))

        threading.Thread(target=worker, daemon=True).start()

    def _show_group(self, _e=None):
        sel = self.tv_dup.selection()
        for i in self.tv_dupdet.get_children():
            self.tv_dupdet.delete(i)
        if not sel:
            return
        g = self.plan[int(sel[0])]
        is_folder = (g.get("type") == "folder")
        self.current_dup_items = []
        for r in g["keep"]:
            idx = str(len(self.current_dup_items))
            self.current_dup_items.append(r)
            if is_folder:
                item_desc = f"{r.get('file_count', 0)} fichiers"
                item_sz = human_size(r.get("total_size", r.get("size", 0)))
            else:
                item_desc = r["name"]
                item_sz = human_size(r["size"])
            self.tv_dupdet.insert("", "end", iid=idx, tags=("keep",), values=(
                "CONSERVER", r["volume_name"], r["folder"], item_desc, item_sz))
        for r in g["drop"]:
            idx = str(len(self.current_dup_items))
            self.current_dup_items.append(r)
            if is_folder:
                item_desc = f"{r.get('file_count', 0)} fichiers"
                item_sz = human_size(r.get("total_size", r.get("size", 0)))
            else:
                item_desc = r["name"]
                item_sz = human_size(r["size"])
            self.tv_dupdet.insert("", "end", iid=idx, tags=("drop",), values=(
                "RETIRER", r["volume_name"], r["folder"], item_desc, item_sz))

    def _inspect_dup_folder(self):
        sel = self.tv_dupdet.selection()
        if not sel or not hasattr(self, "current_dup_items") or not self.current_dup_items:
            messagebox.showinfo(APP_NAME, "Sélectionnez un dossier dans le tableau de droite.")
            return
        r = self.current_dup_items[int(sel[0])]
        vol_id = r.get("volume_id")
        folder_rel = r.get("folder") or r.get("rel_path")
        if not folder_rel or not vol_id:
            messagebox.showinfo(APP_NAME, "Sélectionnez un dossier répertorié.")
            return

        rows = self.app.con.execute(
            "SELECT name, size, category, ext, shot_date, mtime FROM files WHERE volume_id=? AND folder=? ORDER BY name_norm",
            (vol_id, folder_rel)
        ).fetchall()

        if not rows:
            messagebox.showinfo(APP_NAME, f"Aucun fichier répertorié dans ce dossier :\n{folder_rel}")
            return

        top = tk.Toplevel(self)
        top.title(f"Contenu du dossier : {os.path.basename(folder_rel) or folder_rel}")
        top.geometry("750x450")
        top.transient(self)

        header_f = ttk.Frame(top, padding=10)
        header_f.pack(fill="x")
        vol_name = r.get("volume_name", "?")
        total_sz = sum(row["size"] or 0 for row in rows)
        ttk.Label(header_f, text=f"📁 {folder_rel}", font=("TkDefaultFont", 10, "bold")).pack(anchor="w")
        ttk.Label(
            header_f,
            text=f"Disque : {vol_name}  |  {len(rows)} fichiers  |  Taille totale : {human_size(total_sz)}",
            foreground="#666"
        ).pack(anchor="w", pady=(2, 0))

        tree_f = ttk.Frame(top, padding=(10, 0, 10, 10))
        tree_f.pack(fill="both", expand=True)

        insp_cols = ("nom", "taille", "type", "date")
        tv_insp = ttk.Treeview(tree_f, columns=insp_cols, show="headings")
        for ic, ih, iw in zip(insp_cols, ("Nom du fichier", "Taille", "Type", "Date"), (320, 100, 100, 120)):
            tv_insp.heading(ic, text=ih)
            tv_insp.column(ic, width=iw, anchor="w")

        sb_insp = ttk.Scrollbar(tree_f, orient="vertical", command=tv_insp.yview)
        tv_insp.configure(yscrollcommand=sb_insp.set)
        tv_insp.pack(side="left", fill="both", expand=True)
        sb_insp.pack(side="right", fill="y")

        for fr in rows:
            dt_str = fr["shot_date"] or fmt_date(fr["mtime"]) or "—"
            cat_str = fr["category"] or fr["ext"] or "—"
            tv_insp.insert("", "end", values=(fr["name"], human_size(fr["size"] or 0), cat_str, dt_str))

        if hasattr(self, '_make_sortable'):
            self.app._make_sortable(tv_insp, insp_cols, ("Nom du fichier", "Taille", "Type", "Date"))
        elif hasattr(self.app, '_make_sortable'):
            self.app._make_sortable(tv_insp, insp_cols, ("Nom du fichier", "Taille", "Type", "Date"))

        btn_f = ttk.Frame(top, padding=8)
        btn_f.pack(fill="x")
        ttk.Button(btn_f, text="📂 Ouvrir dans le Finder", command=self._reveal_dup_sel).pack(side="left", padx=5)
        ttk.Button(btn_f, text="Fermer", command=top.destroy).pack(side="right", padx=5)

    def _quicklook_dup_sel(self, _e=None):
        sel = self.tv_dupdet.selection()
        if not sel or not hasattr(self, "current_dup_items") or not self.current_dup_items:
            return
        r = self.current_dup_items[int(sel[0])]
        full = full_path_of(self.app.con, r, getattr(self.app, 'online', getattr(self, 'online', False)))
        if full and os.path.exists(full):
            quick_preview(full)
        else:
            item_name = r.get("name") or r.get("folder") or "élément"
            messagebox.showinfo(APP_NAME, f"Le disque « {r['volume_name']} » n\'est pas branché actuellement.\n\nÉlément hors ligne : {item_name}")

    def _reveal_dup_sel(self, _e=None):
        sel = self.tv_dupdet.selection()
        if not sel or not hasattr(self, "current_dup_items") or not self.current_dup_items:
            messagebox.showinfo(APP_NAME, "Sélectionnez un élément dans le tableau de droite.")
            return
        r = self.current_dup_items[int(sel[0])]
        full = full_path_of(self.app.con, r, getattr(self.app, 'online', getattr(self, 'online', False)))
        if not reveal(full):
            if hasattr(self.app, '_refresh_online'):
                self.app._refresh_online(silent=True)
            elif hasattr(self, '_refresh_online'):
                self.app._refresh_online(silent=True)
            full = full_path_of(self.app.con, r, getattr(self.app, 'online', getattr(self, 'online', False)))
            if reveal(full):
                return
            item_rel = r.get("folder") or r.get("rel_path") or r.get("name", "")
            messagebox.showinfo(
                APP_NAME,
                f"Le disque « {r['volume_name']} » n'est pas branché.\n\n"
                f"Branchez-le pour accéder à cet élément :\n{item_rel}")

    def _copy_dup_path(self):
        sel = self.tv_dupdet.selection()
        if not sel or not hasattr(self, "current_dup_items") or not self.current_dup_items:
            return
        r = self.current_dup_items[int(sel[0])]
        full = full_path_of(self.app.con, r, getattr(self.app, 'online', getattr(self, 'online', False)))
        p = full or r.get("folder") or r.get("rel_path") or r.get("name", "")
        self.clipboard_clear()
        self.clipboard_append(p)
        if hasattr(self, 'app') and hasattr(self.app, 'status'):
            self.app.status.set("Chemin copié dans le presse-papiers.")
        elif hasattr(self, 'status'):
            self.app.status.set("Chemin copié dans le presse-papiers.")

    def _copy_rename_path(self):
        if not hasattr(self, 'tv_rename'):
            return
        sel = self.app.tv_rename.selection()
        if not sel:
            return
        p = self.app.tv_rename.item(sel[0], "values")[0]
        self.clipboard_clear()
        self.clipboard_append(p)
        if hasattr(self, 'app') and hasattr(self.app, 'status'):
            self.app.status.set("Chemin copié dans le presse-papiers.")
        elif hasattr(self, 'status'):
            self.app.status.set("Chemin copié dans le presse-papiers.")

    def _verify_group(self):
        sel = self.tv_dup.selection()
        if not sel:
            messagebox.showinfo(APP_NAME, "Sélectionnez d'abord un groupe.")
            return
        g = self.plan[int(sel[0])]
        if hasattr(self, 'app') and hasattr(self.app, 'status'):
            self.app.status.set("Vérification par empreinte complète…")
        elif hasattr(self, 'status'):
            self.app.status.set("Vérification par empreinte complète…")
            
        self.update_idletasks()
        state, msg = verify_group(self.app.con, g)
        
        if hasattr(self, 'app') and hasattr(self.app, 'status'):
            self.app.status.set(tools_status())
        elif hasattr(self, 'status'):
            self.app.status.set(tools_status())
            
        (messagebox.showwarning if state == "different" else messagebox.showinfo)(APP_NAME, msg)

    def _export_plan(self):
        if not hasattr(self, "plan") or not self.plan:
            messagebox.showinfo(APP_NAME, "Calculez d'abord le plan.")
            return
        p = filedialog.asksaveasfilename(defaultextension=".csv",
                                         initialfile="plan_dedoublonnage.csv",
                                         filetypes=[("CSV", "*.csv")])
        if p:
            export_plan(self.plan, p)
            messagebox.showinfo(APP_NAME, "Plan exporté : une ligne par copie, "
                                          "avec la mention CONSERVER ou RETIRER.")
