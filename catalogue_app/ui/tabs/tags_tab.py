import os
import json
import re as re_mod
import threading
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

from catalogue_app.ui.tabs.base_tab import BaseTab
from catalogue_app.ui.components import MultiSelectMenu

from catalogue_app.config import APP_NAME, APP_DIR
from catalogue_app.utils import human_size, human_count
from catalogue_app.db import tag_cloud, TAG_KINDS
from catalogue_app.queries import *
from catalogue_app.tag_engine import merge_tags, clean_orphan_tags, auto_tag_from_vision


class TagsTab(BaseTab):
    def __init__(self, parent, app, **kwargs):
        self.tag_rows = []
        super().__init__(parent, app, **kwargs)

    def _build_ui(self):
        f = self
        bar = ttk.Frame(f, padding=8)
        bar.pack(fill="x")
        ttk.Label(bar, text="Genre :").pack(side="left")
        self.cmb_kind = ttk.Combobox(bar, width=14, state="readonly",
                                     values=["(tous)"] + list(TAG_KINDS))
        self.cmb_kind.set("(tous)")
        self.cmb_kind.pack(side="left", padx=6)
        self.cmb_kind.bind("<<ComboboxSelected>>", lambda _e: self.refresh_tags())
        
        ttk.Label(bar, text="Disque(s) :").pack(side="left", padx=(10, 0))
        self.cmb_tagvol = MultiSelectMenu(bar, text="Sélectionner les disques")
        self.cmb_tagvol.pack(side="left", padx=6)
        self.cmb_tagvol.on_change = lambda: self.refresh_tags()

        ttk.Button(bar, text="Actualiser", command=self.refresh_tags).pack(side="left")
        ttk.Button(bar, text="🤖 Extraire Étiquettes IA", command=self._auto_tag_vision).pack(side="left", padx=6)
        ttk.Label(bar, text="   Double-cliquez sur une étiquette pour voir les fichiers "
                            "correspondants.", foreground="#666").pack(side="left", padx=10)
        ttk.Button(bar, text="Renommer", command=self._rename_tag).pack(side="right")
        ttk.Button(bar, text="Supprimer l'étiquette", command=self._delete_tag).pack(side="right", padx=6)

        # Tag Agent Frame
        ai_tags = ttk.LabelFrame(f, text=" Agent Documentaliste & Taggeur IA ", padding=5)
        ai_tags.pack(fill="x", padx=8, pady=4)
        self.txt_tag_agent = tk.Text(ai_tags, height=2, wrap="word", bg="#1e1e2e", fg="#a6e3a1", font=("TkDefaultFont", 11, "italic"))
        self.txt_tag_agent.pack(fill="x", expand=True, side="left", padx=(0, 10))
        self.txt_tag_agent.insert("1.0", "L'agent peut analyser tes étiquettes, détecter les doublons et extraire des thèmes...")
        self.txt_tag_agent.config(state="disabled")

        skills_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "agents", "skills_tags.md"))
        ttk.Button(ai_tags, text="⚙️ Skills", command=lambda: subprocess.Popen(["open", skills_file])).pack(side="right", padx=5)
        self.btn_tag_agent = ttk.Button(ai_tags, text="🤖 Demander Conseil IA", command=self.ask_tag_agent)
        self.btn_tag_agent.pack(side="right")

        cols = ("nom", "genre", "fichiers", "volume")
        heads = ("Étiquette", "Genre", "Fichiers", "Volume total")
        self.tv_tags = self._make_tree(f, cols, heads, (330, 130, 110, 130), selectmode="browse")
        self.tv_tags.bind("<Double-1>", self._open_tag)
        self.lbl_tags = ttk.Label(f, text="", padding=(12, 0, 12, 8))
        self.lbl_tags.pack(anchor="w")

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
        return tv

    def ask_tag_agent(self):
        self.btn_tag_agent.config(text="Analyse...", state="disabled")
        self.update_idletasks()

        def worker():
            local_con = None
            try:
                import sqlite3
                from catalogue_app.config import DB_PATH
                local_con = sqlite3.connect(DB_PATH)
                local_con.row_factory = sqlite3.Row
                
                from catalogue_app.agents import TagAgent
                agent = TagAgent()
                context_list = []
                for grp in self.tv_tags.get_children()[:30]:
                    vals = self.tv_tags.item(grp, "values")
                    context_list.append({"nom": vals[0], "genre": vals[1], "fichiers": vals[2]})
                
                # Count orphan tags (tags without any linked files)
                try:
                    orph_row = local_con.execute(
                        "SELECT count(*) as n FROM tags WHERE id NOT IN (SELECT DISTINCT tag_id FROM file_tags)"
                    ).fetchone()
                    orphan_count = orph_row["n"] if orph_row else 0
                except Exception:
                    orphan_count = 0
                    
                resp = agent.analyze_tags(context_list, orphan_count=orphan_count)
                self.after(0, lambda r=resp: self._update_tag_txt(r))
            except Exception as e:
                err_msg = str(e)
                self.after(0, lambda err=err_msg: self._update_tag_txt(f"Erreur Agent: {err}"))
            finally:
                if local_con:
                    local_con.close()
                self.after(0, lambda: self.btn_tag_agent.config(text="🤖 Demander Conseil IA", state="normal"))

        threading.Thread(target=worker, daemon=True).start()

    def _update_tag_txt(self, t):
        match = re_mod.search(r'```action\s*(.*?)\s*```', t, re_mod.DOTALL)
        action_data = None
        if match:
            try:
                action_data = json.loads(match.group(1))
                t = t.replace(match.group(0), "\n[Action Détectée : En attente de validation]")
            except Exception:
                pass

        self.txt_tag_agent.config(state="normal")
        self.txt_tag_agent.delete("1.0", "end")
        self.txt_tag_agent.insert("1.0", t)
        self.txt_tag_agent.config(state="disabled")

        if action_data:
            cmd = action_data.get("command")
            if cmd == "MERGE_TAGS":
                src = action_data.get("source_tag")
                tgt = action_data.get("target_tag")
                if messagebox.askyesno("Agent Taggeur", f"L'agent propose de fusionner l'étiquette « {src} » dans « {tgt} ».\n\nConfirmer cette fusion ?"):
                    ok, msg = merge_tags(self.app.con, src, tgt)
                    if ok:
                        messagebox.showinfo("Succès", msg)
                        self.refresh_tags()
                    else:
                        messagebox.showerror("Erreur", msg)
            elif cmd == "PURGE_EMPTY_TAGS":
                if messagebox.askyesno("Agent Taggeur", "L'agent propose de supprimer définitivement toutes les étiquettes orphelines (associées à 0 fichier).\n\nLancer le nettoyage ?"):
                    n = clean_orphan_tags(self.app.con)
                    messagebox.showinfo("Succès", f"{n} étiquette(s) orpheline(s) supprimée(s).")
                    self.refresh_tags()
            elif cmd == "AUTO_TAG_VISION":
                if messagebox.askyesno("Agent Taggeur", "L'agent propose d'extraire automatiquement des étiquettes sémantiques depuis toutes les analyses visuelles IA existantes.\n\nLancer l'opération ?"):
                    self._auto_tag_vision()

    def refresh(self):
        """Rafraîchit l'onglet étiquettes."""
        self.refresh_tags()

    def refresh_tags(self):
        sel_vols = []
        if hasattr(self, 'cmb_tagvol'):
            sel_vols = self.cmb_tagvol.get_selected()

        kind = self.cmb_kind.get()
        rows = tag_cloud(self.app.con, kind, vols=sel_vols)
        self.tag_rows = rows
        for i in self.tv_tags.get_children():
            self.tv_tags.delete(i)
        for idx, r in enumerate(rows):
            self.tv_tags.insert("", "end", iid=str(idx), values=(
                r["name"], r["kind"], human_count(r["n"]), human_size(r["s"])))
        self.lbl_tags.config(text=f"{len(rows)} étiquette(s) affichée(s).")

    def _open_tag(self, _e=None):
        sel = self.tv_tags.selection()
        if not sel:
            return
        r = self.tag_rows[int(sel[0])]
        tag_name = r["name"]

        if hasattr(self.app, "open_tag_in_search"):
            self.app.open_tag_in_search(tag_name)
            return

        st = getattr(self.app, "search_tab", None) or getattr(self.app, "tab_search", None)
        if st:
            if hasattr(st, "var_tagfilter"):
                st.var_tagfilter.set(tag_name)
            if hasattr(st, "var_q"):
                st.var_q.set("")
            if hasattr(st, "cmb_cat"):
                st.cmb_cat.set("toutes")
            if hasattr(st, "cmb_vol") and hasattr(st.cmb_vol, "vars"):
                for v in st.cmb_vol.vars.values():
                    v.set(False)
                st.cmb_vol._update_text()
            if hasattr(st, "_do_search"):
                st._do_search()
        if hasattr(self.app, "nb") and hasattr(self.app, "tab_search"):
            self.app.nb.select(self.app.tab_search)

    def _rename_tag(self):
        sel = self.tv_tags.selection()
        if not sel:
            return
        r = self.tag_rows[int(sel[0])]
        new = simpledialog.askstring(APP_NAME, "Nouveau nom :",
                                     initialvalue=r["name"], parent=self)
        if new and new.strip():
            self.app.con.execute("UPDATE tags SET name=? WHERE id=?", (new.strip(), r["id"]))
            self.app.con.commit()
            self.refresh_tags()

    def _auto_tag_vision(self):
        def worker():
            local_con = None
            try:
                import sqlite3
                from catalogue_app.config import DB_PATH
                local_con = sqlite3.connect(DB_PATH)
                local_con.row_factory = sqlite3.Row
                
                from catalogue_app.tag_engine import auto_tag_from_vision
                n = auto_tag_from_vision(local_con)
                self.after(0, lambda: self.refresh_tags())
                self.after(0, lambda: messagebox.showinfo(APP_NAME, f"Extraction terminée : {n} étiquette(s) thématique(s) attribuée(s) aux médias !"))
            finally:
                if local_con:
                    local_con.close()

        if hasattr(self.app, "status"):
            self.app.status.set("Extraction des étiquettes sémantiques IA en cours...")
        elif hasattr(self, "status"):
            self.app.status.set("Extraction des étiquettes sémantiques IA en cours...")
        threading.Thread(target=worker, daemon=True).start()

    def _delete_tag(self):
        sel = self.tv_tags.selection()
        if not sel:
            return
        r = self.tag_rows[int(sel[0])]
        if messagebox.askyesno(APP_NAME, f"Supprimer l'étiquette « {r['name']} » ?\n"
                                         "(aucun fichier n'est touché)"):
            self.app.con.execute("DELETE FROM file_tags WHERE tag_id=?", (r["id"],))
            self.app.con.execute("DELETE FROM tags WHERE id=?", (r["id"],))
            self.app.con.commit()
            self.refresh_tags()
