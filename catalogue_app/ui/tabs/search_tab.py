import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import os
import subprocess
import threading
import re

from catalogue_app.ui.tabs.base_tab import BaseTab
from catalogue_app.utils import human_size, human_duration, fmt_fps, fmt_date, normalize, human_count
from catalogue_app.ui.components import MultiSelectMenu
from catalogue_app.config import APP_NAME
from catalogue_app.queries import SEARCH_FIELDS, SORT_FIELDS
try:
    from tkinterdnd2 import DND_FILES
    HAS_DND = True
except:
    HAS_DND = False
from catalogue_app.queries import reveal
from catalogue_app.queries import add_manual_tag
from catalogue_app.queries import export_rows
from catalogue_app.export_nle import generate_fcp_xml
from catalogue_app.utils import human_clock
from catalogue_app.queries import full_path_of

class SearchTab(BaseTab):

    def _build_ui(self):
        f = self
        bar = ttk.Frame(f, padding=(8, 8, 8, 2))
        bar.pack(fill="x")
        ttk.Label(bar, text="Rechercher :").pack(side="left")
        self.var_q = tk.StringVar()
        e = ttk.Entry(bar, textvariable=self.var_q, width=26)
        e.pack(side="left", padx=6)
        self.var_semantic = __import__("tkinter").BooleanVar(value=False)
        ttk.Checkbutton(bar, text=" IA", variable=self.var_semantic).pack(side="left", padx=5)
        e.bind("<Return>", lambda _e: self._do_search())
        ttk.Label(bar, text="dans :").pack(side="left", padx=(4, 2))
        self.cmb_field = ttk.Combobox(bar, width=15, state="readonly",
                                      values=list(SEARCH_FIELDS.keys()))
        self.cmb_field.set("partout")
        self.cmb_field.pack(side="left")
        self.cmb_field.bind("<<ComboboxSelected>>", lambda _e: self._do_search())
        ttk.Label(bar, text="Étiquettes :").pack(side="left", padx=(10, 2))
        self.var_tagfilter = tk.StringVar()
        et = ttk.Entry(bar, textvariable=self.var_tagfilter, width=24)
        et.pack(side="left")
        et.bind("<Return>", lambda _e: self._do_search())
        ttk.Button(bar, text="Chercher", command=self._do_search).pack(side="left", padx=10)
        ttk.Button(bar, text="Réinitialiser", command=self._reset_search).pack(side="left")

        bar2 = ttk.Frame(f, padding=(8, 2, 8, 6))
        bar2.pack(fill="x")
        ttk.Label(bar2, text="Catégorie Globale :").pack(side="left", padx=(10, 2))
        self.cmb_global_cat = ttk.Combobox(bar2, width=15, state="readonly",
                                    values=["(toutes)"] + __import__("catalogue_app.settings_manager").settings_manager.get_global_categories())
        self.cmb_global_cat.set("(toutes)")
        self.cmb_global_cat.pack(side="left", padx=(2, 0))
        self.cmb_global_cat.bind("<<ComboboxSelected>>", lambda _e: self._do_search())
        
        ttk.Label(bar2, text="Type de Média :").pack(side="left", padx=(10, 2))
        self.cmb_cat = ttk.Combobox(bar2, width=10, state="readonly",
                                    values=["toutes", "video", "image", "audio", "projet",
                                            "document", "archive", "logiciel", "3d", "code", "autre"])
        self.cmb_cat.set("toutes")
        self.cmb_cat.pack(side="left", padx=(2, 0))
        self.cmb_cat.bind("<<ComboboxSelected>>", lambda _e: self._do_search())
        ttk.Label(bar2, text="Disque :").pack(side="left", padx=(10, 2))
        self.cmb_vol = MultiSelectMenu(bar2, text="(tous)")
        self.cmb_vol.command = self._do_search
        self.cmb_vol.pack(side="left")
        ttk.Label(bar2, text="Années de").pack(side="left", padx=(12, 2))
        self.var_y1 = tk.StringVar()
        ttk.Entry(bar2, textvariable=self.var_y1, width=6).pack(side="left")
        ttk.Label(bar2, text="à").pack(side="left", padx=2)
        self.var_y2 = tk.StringVar()
        ttk.Entry(bar2, textvariable=self.var_y2, width=6).pack(side="left")
        ttk.Label(bar2, text="≥ Mo :").pack(side="left", padx=(12, 2))
        self.var_minmb = tk.StringVar(value="0")
        ttk.Entry(bar2, textvariable=self.var_minmb, width=6).pack(side="left")
        ttk.Label(bar2, text="Trier par :").pack(side="left", padx=(12, 2))
        self.cmb_sort = ttk.Combobox(bar2, width=11, state="readonly",
                                     values=list(SORT_FIELDS.keys()))
        self.cmb_sort.set("taille")
        self.cmb_sort.pack(side="left")
        self.cmb_sort.bind("<<ComboboxSelected>>", lambda _e: self._do_search())
        self.var_desc = tk.BooleanVar(value=True)
        ttk.Checkbutton(bar2, text="décroissant", variable=self.var_desc,
                        command=self._do_search).pack(side="left", padx=6)
        ttk.Button(bar2, text="Détecter les disques branchés",
                   command=self.app._refresh_online).pack(side="left", padx=10)

        # Bar 3: Collections intelligentes & Recherches sauvegardées
        bar3 = ttk.Frame(f, padding=(8, 2, 8, 4))
        bar3.pack(fill="x")
        ttk.Label(bar3, text="⭐ Collections :", font=("TkDefaultFont", 9, "bold")).pack(side="left", padx=(0, 4))
        self.cmb_saved_searches = ttk.Combobox(bar3, width=28, state="readonly")
        self.cmb_saved_searches.pack(side="left", padx=(0, 6))
        self.cmb_saved_searches.bind("<<ComboboxSelected>>", self._on_select_saved_search)
        ttk.Button(bar3, text="⭐ Sauvegarder la recherche...", command=self._save_current_search).pack(side="left", padx=4)
        ttk.Button(bar3, text="🗑️ Supprimer", command=self._delete_current_saved_search).pack(side="left", padx=4)
        self._refresh_saved_searches_list()

        ttk.Label(f, text="Cliquez sur un en-tête de colonne pour trier, comme dans le Finder. "
                          "Les étiquettes se cumulent, séparées par une virgule : « 4K, interview, 2024 ».",
                  foreground="#666").pack(anchor="w", padx=12)

        self.search_paned = ttk.PanedWindow(f, orient="horizontal")
        self.search_paned.pack(fill="both", expand=True, padx=8, pady=4)
        
        # Left pane: Search results
        left_pane = ttk.Frame(self.search_paned)
        self.search_paned.add(left_pane, weight=4)

        cols = ("nom", "global_cat", "disque", "dispo", "dossier", "taille", "duree", "camera",
                "definition", "ips", "codec", "date", "etiquettes")
        heads = ("Nom", "Cat. Globale", "Disque", "Disponibilité", "Dossier", "Taille", "Durée", "Caméra",
                 "Définition", "IPS", "Codec", "Date", "Étiquettes")
        self.tv_res = self._make_tree(left_pane, cols, heads,
                                      (220, 110, 115, 95, 230, 85, 65, 135, 85, 50, 80, 85, 280))
        
        # Right pane: Drop Zone / Panier de Rushes
        self.basket_pane = ttk.Frame(self.search_paned)
        self.search_paned.add(self.basket_pane, weight=1)
        
        basket_header = ttk.Frame(self.basket_pane)
        basket_header.pack(fill="x", pady=(0, 5))
        ttk.Label(basket_header, text="🛒 Panier de Rushes", font=("TkDefaultFont", 12, "bold")).pack(side="left")
        ttk.Button(basket_header, text="Vider", command=self.app._clear_basket).pack(side="right")
        
        self.tv_basket = self._make_tree(self.basket_pane, ("nom", "duree", "disque"), ("Nom du Clip", "Durée", "Disque"), (150, 60, 100))
        
        basket_footer = ttk.Frame(self.basket_pane)
        basket_footer.pack(fill="x", pady=(5, 0))
        
        ttk.Button(basket_footer, text="✂️ Générer Proxies (H264)", command=self.app._generate_proxies).pack(fill="x", ipady=4, pady=(0, 4))
        ttk.Button(basket_footer, text="🎬 Envoyer au Monteur (XML)", command=self.app._export_basket_xml).pack(fill="x", ipady=4)

        
        self.basket_items = {} # dict mapping file path to row data
        self._make_sortable(self.tv_res, cols, heads)
        self.tv_res.tag_configure("on", foreground="#81c784")
        self.tv_res.tag_configure("off", foreground="#9e9e9e")
        self.tv_res.bind("<<TreeviewSelect>>", self._on_select_result)
        self.tv_res.bind("<Double-1>", lambda _e: self._reveal_sel())
        self.tv_res.bind("<space>", lambda _e: self._quicklook_sel())

        def _on_search_drop(event):
            path = event.data
            if path.startswith('{') and path.endswith('}'): path = path[1:-1]
            # Filter by this directory
            self.cmb_field.set("dossier")
            import os
            self.var_q.set(os.path.basename(path))
            self._do_search()
        
        if HAS_DND:
            left_pane.drop_target_register(DND_FILES)
            left_pane.dnd_bind('<<Drop>>', _on_search_drop)

        
        # --- Menu Contextuel ---
        self.menu_res = tk.Menu(f, tearoff=0)
        self.menu_res.add_command(label="👁️ Coup d'œil (Espace)", command=self._quicklook_sel)
        self.menu_res.add_command(label="Ouvrir dans le Finder", command=self._reveal_sel)
        self.menu_res.add_command(label="🛒 Ajouter au Panier", command=self.app._add_to_basket)
        self.menu_res.add_command(label="Copier le chemin", command=self._copy_path)
        self.menu_res.add_separator()
        self.menu_res.add_command(label="Ajouter une étiquette…", command=self._add_tag_to_selection)
        self.menu_res.add_command(label="Définir Cat. Globale…", command=self._set_global_cat_selection)
        self.menu_res.add_separator()
        self.menu_res.add_command(label="ℹ️ Fiche Technique du Format…", command=self._show_format_info)
        self.menu_res.add_command(label="🩺 Contrôle d'Intégrité / Rush Corrompu…", command=self._check_media_health_sel)
        self.menu_res.add_command(label="🎞️ Planche Contact / Storyboard…", command=self._show_contact_sheet_sel)
        
        def popup_res(event):
            # Check if we clicked on an item. If not selected, select it.
            iid = self.tv_res.identify_row(event.y)
            if iid:
                if iid not in self.tv_res.selection():
                    self.tv_res.selection_set(iid)
                self.menu_res.post(event.x_root, event.y_root)

        # macOS (<Button-2> or <Control-Button-1>), Windows/Linux (<Button-3>)
        import sys
        if sys.platform == "darwin":
            self.tv_res.bind("<Button-2>", popup_res)
            self.tv_res.bind("<Control-Button-1>", popup_res)
        else:
            self.tv_res.bind("<Button-3>", popup_res)
        # -----------------------

        act = ttk.Frame(f, padding=(8, 0, 8, 8))
        act.pack(fill="x")
        ttk.Button(act, text="Copier le chemin", command=self._copy_path).pack(side="left")
        ttk.Button(act, text="Ouvrir dans le Finder", command=self._reveal_sel).pack(side="left", padx=6)
        ttk.Button(act, text="👁️ Coup d'œil (Espace)", command=self._quicklook_sel).pack(side="left", padx=6)
        ttk.Button(act, text="Ajouter une étiquette…",
                   command=self._add_tag_to_selection).pack(side="left", padx=6)
        ttk.Button(act, text="Définir Cat. Globale…",
                   command=self._set_global_cat_selection).pack(side="left", padx=6)
        ttk.Button(act, text="Exporter (CSV)", command=self._export_results).pack(side="left")
        
        # Search Agent Frame
        ai_search = ttk.LabelFrame(f, text=" Agent Archiviste IA ", padding=5)
        ai_search.pack(fill="x", padx=8, pady=4)
        self.txt_search_agent = __import__("tkinter").Text(ai_search, height=2, wrap="word", bg="#1e1e2e", fg="#89b4fa", font=("TkDefaultFont", 11, "italic"))
        self.txt_search_agent.pack(fill="x", expand=True, side="left", padx=(0,10))
        self.txt_search_agent.insert("1.0", "Pose-moi une question sur ta recherche...")
        self.txt_search_agent.config(state="disabled")
        
        def ask_search_agent():
            self.btn_search_agent.config(text="Analyse...", state="disabled")
            self.update_idletasks()
            q = self.var_q.get()
            count = len(self.tv_res.get_children())
            rows_snapshot = [dict(r) for r in (getattr(self, "search_rows", None) or [])[:100]]
            def worker():
                try:
                    from catalogue_app.agents import SearchAgent
                    agent = SearchAgent()
                    
                    # Build technical profile from currently loaded search rows
                    tech_profile = {}
                    if rows_snapshot:
                        defs, codecs, cams, dates = {}, {}, {}, []
                        for r in rows_snapshot:
                            w, h = r.get("width"), r.get("height")
                            if w and h:
                                d_label = "4K/UHD" if (w >= 3840 or h >= 2160) else ("1080p" if h >= 1080 else f"{w}x{h}")
                                defs[d_label] = defs.get(d_label, 0) + 1
                            cdc = r.get("codec")
                            if cdc:
                                codecs[cdc] = codecs.get(cdc, 0) + 1
                            cam = r.get("camera")
                            if cam:
                                cams[cam] = cams.get(cam, 0) + 1
                            dt = r.get("shot_date") or r.get("mtime")
                            if dt:
                                dates.append(str(dt)[:10])
                        tech_profile["definitions"] = defs
                        tech_profile["codecs"] = codecs
                        tech_profile["cameras"] = cams
                        if dates:
                            tech_profile["dates"] = f"Du {min(dates)} au {max(dates)}"

                    resp = agent.analyze_search(q, count, tech_profile=tech_profile)
                    self.after(0, lambda r=resp: _update_search_txt(r))
                except Exception as e:
                    err_msg = str(e)
                    self.after(0, lambda err=err_msg: _update_search_txt(f"Erreur Agent: {err}"))
                finally:
                    self.after(0, lambda: self.btn_search_agent.config(text="🤖 Demander Conseil IA", state="normal"))
                    
            def _update_search_txt(t):
                import re as re_mod, json
                match = re_mod.search(r'```action\s*(.*?)\s*```', t, re_mod.DOTALL)
                action_data = None
                if match:
                    try:
                        action_data = json.loads(match.group(1))
                        t = t.replace(match.group(0), "\n[Action Détectée : Proposition de Timeline]")
                    except: pass

                self.txt_search_agent.config(state="normal")
                self.txt_search_agent.delete("1.0", "end")
                self.txt_search_agent.insert("1.0", t)
                self.txt_search_agent.config(state="disabled")

                if action_data:
                    cmd = action_data.get("command")
                    if cmd == "EXPORT_CHRONO_TIMELINE":
                        title = action_data.get("title", "Ours_Chronologique")
                        if messagebox.askyesno("Agent Monteur", "L'agent propose de créer une Timeline XML chronologique (rushes triés par date/heure de tournage).\n\nExporter le fichier XML de montage ?"):
                            self._export_fcp_xml(default_name=f"{title}.xml", sort_chrono=True)
                    elif cmd == "EXPORT_TIMELINE":
                        title = action_data.get("title", "Ours_de_Montage_IA")
                        if messagebox.askyesno("Agent Archiviste & Monteur", "L'agent propose de créer automatiquement une Timeline de montage XML avec vos résultats de recherche.\n\nExporter le fichier XML de montage ?"):
                            self._export_fcp_xml(default_name=f"{title}.xml", sort_chrono=False)
                
            import threading
            threading.Thread(target=worker, daemon=True).start()
            
        skills_search_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "agents", "skills_search_assistant.md"))
        ttk.Button(ai_search, text="⚙️ Skills", command=lambda: subprocess.Popen(["open", skills_search_path])).pack(side="right", padx=5)
        self.btn_search_agent = ttk.Button(ai_search, text="🤖 Demander Conseil IA", command=ask_search_agent)
        self.btn_search_agent.pack(side="right")

        ttk.Button(act, text="🎬 Exporter Timeline XML", command=self._export_fcp_xml).pack(side="left", padx=6)
        ttk.Button(act, text="Générer XMP Sidecars", command=self._export_xmp).pack(side="left", padx=6)
        self.lbl_res = ttk.Label(act, text="")
        self.lbl_res.pack(side="right")

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

    def _reset_search(self):
        self.var_q.set("")
        self.var_tagfilter.set("")
        self.cmb_field.set("partout")
        self.cmb_cat.set("toutes")
        if hasattr(self, "cmb_global_cat"):
            self.cmb_global_cat.set("(toutes)")
        for var in self.cmb_vol.vars.values(): var.set(False)
        self.cmb_vol._update_text()
        self.var_y1.set("")
        self.var_y2.set("")
        self.var_minmb.set("0")
        self.cmb_sort.set("taille")
        self.var_desc.set(True)
        if hasattr(self, "cmb_saved_searches"):
            self.cmb_saved_searches.set("(Sélectionner une collection / recherche...)")
        self._do_search()

    def _refresh_saved_searches_list(self):
        from catalogue_app.queries import get_saved_searches
        saved = get_saved_searches(self.app.con)
        self._saved_searches_data = {s["name"]: s["query"] for s in saved}
        vals = ["(Sélectionner une collection / recherche...)"] + list(self._saved_searches_data.keys())
        self.cmb_saved_searches.config(values=vals)
        self.cmb_saved_searches.set("(Sélectionner une collection / recherche...)")

    def _on_select_saved_search(self, _e=None):
        name = self.cmb_saved_searches.get()
        if not name or name not in getattr(self, "_saved_searches_data", {}):
            return
        q = self._saved_searches_data[name]
        self.var_q.set(q.get("text", ""))
        self.cmb_field.set(q.get("field", "partout"))
        self.cmb_global_cat.set(q.get("global_cat", "(toutes)"))
        self.cmb_cat.set(q.get("category", "toutes"))
        tags = q.get("tags", [])
        self.var_tagfilter.set(", ".join(tags) if isinstance(tags, list) else str(tags))
        self.var_y1.set(q.get("year_from") or "")
        self.var_y2.set(q.get("year_to") or "")
        self.var_minmb.set(str(q.get("min_size_mb", 0)))
        self.cmb_sort.set(q.get("sort", "taille"))
        self.var_desc.set(bool(q.get("desc", True)))
        self._do_search()

    def _save_current_search(self):
        from catalogue_app.queries import save_search_query
        from tkinter import simpledialog
        name = simpledialog.askstring("Sauvegarder la recherche", "Nom de la collection intelligente / recherche :", parent=self)
        if not name or not name.strip():
            return
        name = name.strip()
        q_dict = {
            "text": self.var_q.get(),
            "field": self.cmb_field.get(),
            "global_cat": self.cmb_global_cat.get(),
            "category": self.cmb_cat.get(),
            "tags": [t.strip() for t in self.var_tagfilter.get().split(",") if t.strip()],
            "year_from": self.var_y1.get().strip() or None,
            "year_to": self.var_y2.get().strip() or None,
            "min_size_mb": self.var_minmb.get() or 0,
            "sort": self.cmb_sort.get(),
            "desc": bool(self.var_desc.get()),
        }
        save_search_query(self.app.con, name, q_dict, is_smart_collection=1)
        self._refresh_saved_searches_list()
        self.cmb_saved_searches.set(name)
        messagebox.showinfo("Collection sauvegardée", f"La collection « {name} » a été enregistrée avec succès !")

    def _delete_current_saved_search(self):
        from catalogue_app.queries import delete_saved_search
        name = self.cmb_saved_searches.get()
        if not name or name not in getattr(self, "_saved_searches_data", {}):
            messagebox.showwarning("Supprimer", "Veuillez d'abord sélectionner une collection sauvegardée.")
            return
        if messagebox.askyesno("Confirmer", f"Supprimer définitivement la collection « {name} » ?"):
            delete_saved_search(self.app.con, name)
            self._refresh_saved_searches_list()

    def _make_tree(self, parent, cols, heads, widths, selectmode="extended"):
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
        self._make_sortable(tv, cols, heads)
        return tv

    def _do_search(self):
        """La recherche s'exécute dans un thread : sur un catalogue de plusieurs
        centaines de milliers de fichiers, l'interface ne se fige plus."""
        if getattr(self, "searching", False):
            return
        self.searching = True
        self.lbl_res.config(text="Recherche en cours…")
        self.update_idletasks()
        
        search_text = self.var_q.get()
        is_ai = self.var_semantic.get()
        file_ids_from_ai = None
        
        if is_ai and search_text:
            try:
                # Remplacer les espaces par AND pour FTS5
                ai_query = " AND ".join(search_text.split())
                ai_rows = self.app.con.execute("SELECT file_id FROM fts_vision WHERE fts_vision MATCH ? LIMIT 100", (ai_query,)).fetchall()
                if ai_rows:
                    file_ids_from_ai = [str(r["file_id"]) for r in ai_rows]
                else:
                    file_ids_from_ai = [] # Force empty results
            except Exception as e:
                print("Erreur recherche sémantique FTS5 :", e)
                file_ids_from_ai = []
        
        params = {
            "text": "" if is_ai else search_text,
            "file_ids": file_ids_from_ai,
            "field": self.cmb_field.get(),
            "category": self.cmb_cat.get(),
            "global_cat": self.cmb_global_cat.get(),
            "volume_id": None,
            "volume_ids": self.cmb_vol.get_selected(),
            "tags": [t.strip() for t in self.var_tagfilter.get().split(",") if t.strip()],
            "min_size_mb": self.var_minmb.get() or 0,
            "year_from": self.var_y1.get().strip() or None,
            "year_to": self.var_y2.get().strip() or None,
            "sort": self.cmb_sort.get(),
            "desc": bool(self.var_desc.get()),
        }

        is_ai = getattr(self, "var_semantic", None) and self.var_semantic.get()
        def worker():
            scon = None
            try:
                from catalogue_app.db import connect
                from catalogue_app.queries import search_files, tags_for_files
                scon = connect()
                if is_ai and params["text"].strip():
                    t = params["text"].strip()
                    params["text"] = ""
                    try:
                        import catalogue_app.ai_search as ai_search
                        if ai_search.HAS_AI:
                            vec = ai_search.encode_text(t)
                            if vec is not None:
                                c = scon.cursor()
                                c.execute("SELECT file_id, embedding FROM file_embeddings")
                                scores = []
                                for r in c.fetchall():
                                    emb = ai_search.deserialize_vector(r["embedding"])
                                    sim = ai_search.compute_similarity(vec, emb)
                                    if sim > 0.22:
                                        scores.append((r["file_id"], sim))
                                scores.sort(key=lambda x: x[1], reverse=True)
                                if scores:
                                    params["file_ids"] = [str(x[0]) for x in scores[:100]]
                                else:
                                    params["file_ids"] = ["-1"] # no results
                        else:
                            params["tags"].append(f"ia:{t.lower()}")
                    except Exception as e:
                        print("Erreur semantique:", e)
                        params["tags"].append(f"ia:{t.lower()}")
                        
                rows = search_files(scon, **params)
                
                if is_ai and params.get("file_ids"):
                    # Re-sort rows according to similarity score order
                    score_map = {fid: idx for idx, fid in enumerate(params["file_ids"])}
                    rows.sort(key=lambda r: score_map.get(r["id"], 999))
                tagmap = tags_for_files(scon, [r["id"] for r in rows])
                self.app.msgq.put(("results", (rows, tagmap)))
            except Exception as exc:
                self.app.msgq.put(("search_error", str(exc)))
            finally:
                if scon is not None:
                    try:
                        scon.close()
                    except Exception:
                        pass

        threading.Thread(target=worker, daemon=True).start()

    def _show_results(self, rows, tagmap):
        self.searching = False
        self.search_rows = rows
        for i in self.tv_res.get_children():
            self.tv_res.delete(i)
        online = self.app.online
        for idx, r in enumerate(rows):
            res = f'{r["width"]}×{r["height"]}' if r["width"] and r["height"] else ""
            tag_txt = ", ".join(tagmap.get(r["id"], [])[:8])
            dispo = "● branché" if online.get(r["volume_id"]) else "○ absent"
            self.tv_res.insert("", "end", iid=str(idx), tags=(
                "on" if online.get(r["volume_id"]) else "off",), values=(
                r["name"], r["global_cat"] or "", r["volume_name"], dispo, r["folder"], human_size(r["size"]),
                human_duration(r["duration"]), r["camera"] or "", res,
                fmt_fps(r["fps"]), r["codec"] or "",
                (r["shot_date"] or "")[:10] or fmt_date(r["mtime"]), tag_txt))
        total = sum(r["size"] or 0 for r in rows)
        nb_on = sum(1 for r in rows if online.get(r["volume_id"]))
        
        cur_cat = self.cmb_cat.get()
        q_text = self.var_q.get().strip()
        
        if len(rows) == 0 and cur_cat not in ("toutes", "") and q_text:
            try:
                from catalogue_app.db import connect
                from catalogue_app.queries import search_files
                c_tmp = connect()
                unfiltered = search_files(c_tmp, text=q_text, category="toutes", limit=5000)
                c_tmp.close()
                if unfiltered:
                    n_unf = len(unfiltered)
                    self.lbl_res.config(
                        text=f"0 résultat dans '{cur_cat}' — 💡 {human_count(n_unf)} fichier(s) trouvé(s) dans 'toutes les catégories' ! (👉 Cliquez ici pour les afficher)",
                        foreground="#38bdf8", cursor="pointinghand"
                    )
                    def switch_and_search(_e):
                        self.cmb_cat.set("toutes")
                        self.lbl_res.unbind("<Button-1>")
                        self.lbl_res.config(foreground="", cursor="")
                        self._do_search()
                    self.lbl_res.bind("<Button-1>", switch_and_search)
                    return
            except Exception as e:
                pass

        limit_warn = "   ⚠️ (Limite de 5 000 résultats atteinte — affinez vos filtres)" if len(rows) >= 5000 else ""
        self.lbl_res.config(
            text=f"{human_count(len(rows))} résultat(s) — {human_size(total)}"
                 f"   ·   {human_count(nb_on)} accessible(s) tout de suite{limit_warn}",
            foreground="#f9e2af" if limit_warn else "", cursor=""
        )
        self.lbl_res.unbind("<Button-1>")

    def _on_select_result(self, _e=None):
        r = self._sel_row()
        if r:
            base_info = f'[{r["volume_name"]}]  {r["rel_path"]}'
            try:
                row_ai = self.app.con.execute("SELECT vision_desc FROM ai_metadata WHERE file_id = ?", (r["id"],)).fetchone()
                if row_ai and row_ai[0]:
                    self.app.status.set(f'{base_info}  |  🤖 Vision IA : {row_ai[0]}')
                    return
            except:
                pass
            self.app.status.set(base_info)

    def _sel_rows(self):
        return [self.search_rows[int(i)] for i in self.tv_res.selection()]

    def _sel_row(self):
        rows = self._sel_rows()
        return rows[0] if rows else None

    def _copy_path(self):
        r = self._sel_row()
        if not r:
            return
        self.clipboard_clear()
        self.clipboard_append(f'[{r["volume_name"]}] {r["rel_path"]}')
        self.app.status.set("Chemin copié dans le presse-papiers.")


    def _show_format_info(self):
        import webbrowser
        from catalogue_app.format_database import get_format_info

        sel = self.tv_res.selection()
        if not sel:
            return

        row = self.tv_res.item(sel[0], "values")
        filename = row[0]
        ext = os.path.splitext(filename)[1].lstrip(".")
        if not ext:
            messagebox.showinfo("Format", "Ce fichier n'a pas d'extension identifiable.")
            return

        info = get_format_info(ext)

        top = tk.Toplevel(self)
        top.title(f"Fiche Technique : {info['name']} ({info['extension']})")
        top.geometry("560x420")
        top.resizable(False, False)
        top.transient(self)

        card = ttk.LabelFrame(top, text=f" Spécifications du Format {info['extension'].upper()} ", padding=16)
        card.pack(fill="both", expand=True, padx=16, pady=16)

        ttk.Label(card, text="Nom Officiel :", font=("TkDefaultFont", 10, "bold")).grid(row=0, column=0, sticky="w", pady=4)
        ttk.Label(card, text=info["name"], font=("TkDefaultFont", 11, "bold"), foreground="#89b4fa").grid(row=0, column=1, sticky="w", padx=10, pady=4)

        ttk.Label(card, text="Catégorie :", font=("TkDefaultFont", 10, "bold")).grid(row=1, column=0, sticky="w", pady=4)
        ttk.Label(card, text=info["category"]).grid(row=1, column=1, sticky="w", padx=10, pady=4)

        ttk.Label(card, text="Logiciel / Créateur :", font=("TkDefaultFont", 10, "bold")).grid(row=2, column=0, sticky="w", pady=4)
        ttk.Label(card, text=info["software"]).grid(row=2, column=1, sticky="w", padx=10, pady=4)

        ttk.Label(card, text="Description :", font=("TkDefaultFont", 10, "bold")).grid(row=3, column=0, sticky="nw", pady=(10, 4))
        desc_txt = tk.Text(card, height=5, wrap="word", font=("TkDefaultFont", 10), relief="flat", bg="#1e1e2e", fg="#cdd6f4")
        desc_txt.grid(row=3, column=1, sticky="nsew", padx=10, pady=(10, 4))
        desc_txt.insert("1.0", info["description"])
        desc_txt.config(state="disabled")

        # Badges de Capacités (Vignette, Texte FTS, Rendu PDF)
        badge_frame = ttk.Frame(card)
        badge_frame.grid(row=4, column=0, columnspan=2, sticky="w", pady=(12, 4))

        thumb_color = "#a6e3a1" if info.get("supports_thumbnail") else "#6c7086"
        txt_color = "#a6e3a1" if info.get("supports_text") else "#6c7086"
        pdf_color = "#a6e3a1" if info.get("supports_pdf") else "#6c7086"

        thumb_txt = "🖼️ Vignette : ✅ Oui" if info.get("supports_thumbnail") else "🖼️ Vignette : ❌ Non"
        txt_txt = "📝 Texte FTS5 : ✅ Indexable" if info.get("supports_text") else "📝 Texte FTS5 : ❌ Non"
        pdf_txt = "📄 Rendu PDF : ✅ Compatible" if info.get("supports_pdf") else "📄 Rendu PDF : ❌ Non"

        ttk.Label(badge_frame, text=thumb_txt, font=("TkDefaultFont", 9, "bold"), foreground=thumb_color).pack(side="left", padx=(0, 12))
        ttk.Label(badge_frame, text=txt_txt, font=("TkDefaultFont", 9, "bold"), foreground=txt_color).pack(side="left", padx=(0, 12))
        ttk.Label(badge_frame, text=pdf_txt, font=("TkDefaultFont", 9, "bold"), foreground=pdf_color).pack(side="left")

        card.columnconfigure(1, weight=1)

        btn_box = ttk.Frame(top, padding=(16, 0, 16, 16))
        btn_box.pack(fill="x")

        def open_web():
            webbrowser.open(info["ffi_url"])

        ttk.Button(btn_box, text="🌐 Spécifications FileFormat.Info", command=open_web).pack(side="left")
        ttk.Button(btn_box, text="Fermer", command=top.destroy).pack(side="right")

    def _check_media_health_sel(self):
        from catalogue_app.media_health import check_media_file_health, batch_check_media_health
        sel = self.tv_res.selection()
        if not sel:
            messagebox.showinfo(APP_NAME, "Sélectionnez au moins un rush pour vérifier son intégrité.")
            return

        if len(sel) == 1:
            r = self._sel_row()
            if not r:
                return
            full = full_path_of(self.app.con, r, self.app.online)
            if not full or not os.path.exists(full):
                messagebox.showwarning("Intégrité", f"Le fichier n'est pas accessible (disque « {r['volume_name']} » non branché).")
                return

            rep = check_media_file_health(full, deep_check=False)

            top = tk.Toplevel(self)
            top.title(f"Contrôle d'Intégrité : {rep['name']}")
            top.geometry("540x440")
            top.resizable(False, False)
            top.transient(self)

            card = ttk.LabelFrame(top, text=" Résultat du Contrôle d'Intégrité (Health Check) ", padding=16)
            card.pack(fill="both", expand=True, padx=16, pady=16)

            status_map = {
                "healthy": ("🟢 Rush Intègre & Parfaitement Lisible", "#a6e3a1"),
                "warning": ("🟡 Avertissement (En-tête ou flux atypique)", "#f9e2af"),
                "corrupt": ("🔴 RUSH CORROMPU / ILLISIBLE", "#f38ba8"),
                "unknown": ("⚪ Inconnu / Analyse impossible", "#cdd6f4"),
            }
            st_txt, st_col = status_map.get(rep["status"], status_map["unknown"])
            ttk.Label(card, text=st_txt, font=("TkDefaultFont", 12, "bold"), foreground=st_col).pack(anchor="w", pady=(0, 10))

            details = rep.get("details", {})
            det_frame = ttk.Frame(card)
            det_frame.pack(fill="x", pady=5)

            ttk.Label(det_frame, text="Format :", font=("TkDefaultFont", 10, "bold")).grid(row=0, column=0, sticky="w", pady=2)
            ttk.Label(det_frame, text=details.get("format_name", "N/A")).grid(row=0, column=1, sticky="w", padx=10, pady=2)

            ttk.Label(det_frame, text="Résolution :", font=("TkDefaultFont", 10, "bold")).grid(row=1, column=0, sticky="w", pady=2)
            ttk.Label(det_frame, text=details.get("resolution", "N/A")).grid(row=1, column=1, sticky="w", padx=10, pady=2)

            ttk.Label(det_frame, text="Codec Vidéo :", font=("TkDefaultFont", 10, "bold")).grid(row=2, column=0, sticky="w", pady=2)
            ttk.Label(det_frame, text=details.get("video_codec", "N/A")).grid(row=2, column=1, sticky="w", padx=10, pady=2)

            ttk.Label(det_frame, text="Codec Audio :", font=("TkDefaultFont", 10, "bold")).grid(row=3, column=0, sticky="w", pady=2)
            ttk.Label(det_frame, text=f"{details.get('audio_codec', 'N/A')} ({details.get('channels', 0)} canaux)").grid(row=3, column=1, sticky="w", padx=10, pady=2)

            ttk.Label(det_frame, text="Durée :", font=("TkDefaultFont", 10, "bold")).grid(row=4, column=0, sticky="w", pady=2)
            ttk.Label(det_frame, text=f"{details.get('duration', 0.0):.2f}s").grid(row=4, column=1, sticky="w", padx=10, pady=2)

            if rep.get("issues"):
                ttk.Label(card, text="Anomalies détectées :", font=("TkDefaultFont", 10, "bold"), foreground="#f38ba8").pack(anchor="w", pady=(10, 2))
                txt_issues = tk.Text(card, height=4, wrap="word", bg="#1e1e2e", fg="#f38ba8", font=("TkDefaultFont", 9))
                txt_issues.pack(fill="x", pady=2)
                for iss in rep["issues"]:
                    txt_issues.insert("end", f"• {iss}\n")
                txt_issues.config(state="disabled")

            btn_box = ttk.Frame(top, padding=(16, 0, 16, 16))
            btn_box.pack(fill="x")
            ttk.Button(btn_box, text="Fermer", command=top.destroy).pack(side="right")
        else:
            rows = self._sel_rows()
            paths = []
            for r in rows:
                p = full_path_of(self.app.con, r, self.app.online)
                if p and os.path.exists(p):
                    paths.append(p)

            if not paths:
                messagebox.showwarning("Intégrité", "Aucun des fichiers sélectionnés n'est accessible sur un disque monté.")
                return

            top = tk.Toplevel(self)
            top.title(f"Contrôle d'Intégrité par Lot ({len(paths)} fichiers)")
            top.geometry("680x450")
            top.transient(self)

            lbl = ttk.Label(top, text=f"Analyse de {len(paths)} rushes en cours...", font=("TkDefaultFont", 11, "bold"))
            lbl.pack(anchor="w", padx=16, pady=10)

            pb = ttk.Progressbar(top, mode="determinate", maximum=len(paths))
            pb.pack(fill="x", padx=16, pady=(0, 10))

            tv_health = ttk.Treeview(top, columns=("nom", "statut", "details", "anomalie"), show="headings")
            tv_health.heading("nom", text="Fichier")
            tv_health.heading("statut", text="État")
            tv_health.heading("details", text="Résolution / Codec")
            tv_health.heading("anomalie", text="Diagnostic")
            tv_health.column("nom", width=180)
            tv_health.column("statut", width=90)
            tv_health.column("details", width=150)
            tv_health.column("anomalie", width=220)
            tv_health.pack(fill="both", expand=True, padx=16, pady=(0, 10))

            def bg_batch():
                def prog(curr, tot, p):
                    top.after(0, lambda: pb.configure(value=curr))
                    top.after(0, lambda: lbl.config(text=f"Vérification {curr}/{tot} : {os.path.basename(p)}"))

                reps = batch_check_media_health(paths, deep_check=False, progress_cb=prog)
                
                def finish():
                    lbl.config(text=f"Vérification terminée ({len(reps)} fichiers analysés)")
                    corrupt_count = 0
                    for rep in reps:
                        st = rep["status"]
                        if st == "corrupt": corrupt_count += 1
                        det = rep.get("details", {})
                        det_str = f"{det.get('resolution', '')} {det.get('video_codec', '')}".strip() or "N/A"
                        iss_str = ", ".join(rep.get("issues", [])) or "OK"
                        st_label = "🟢 Intègre" if st == "healthy" else ("🟡 Avertissement" if st == "warning" else "🔴 Corrompu")
                        tv_health.insert("", "end", values=(rep["name"], st_label, det_str, iss_str))
                    
                    if corrupt_count > 0:
                        messagebox.showwarning("Rushes corrompus", f"⚠️ Attention : {corrupt_count} fichier(s) corrompu(s) détecté(s) !", parent=top)

                top.after(0, finish)

            import threading
            threading.Thread(target=bg_batch, daemon=True).start()

    def _show_contact_sheet_sel(self):
        from catalogue_app.contact_sheet import ContactSheetDialog
        r = self._sel_row()
        if not r:
            messagebox.showinfo(APP_NAME, "Sélectionnez un clip vidéo pour générer sa planche contact.")
            return
        full = full_path_of(self.app.con, r, self.app.online)
        if not full or not os.path.exists(full):
            messagebox.showwarning("Planche Contact", f"Le fichier n'est pas accessible (disque « {r['volume_name']} » non branché).")
            return
        ext = os.path.splitext(full)[1].lower()
        from catalogue_app.config import VIDEO_EXT
        if ext not in VIDEO_EXT and r.get("category") != "video":
            messagebox.showinfo("Planche Contact", "La planche contact s'applique uniquement aux fichiers vidéo.")
            return
        meta = {
            "camera": r.get("camera"),
            "volume_name": r.get("volume_name"),
            "date": r.get("shot_date") or fmt_date(r.get("mtime")),
        }
        ContactSheetDialog(self, full, metadata=meta)

    def _show_shooting_timeline(self):
        from catalogue_app.shooting_timeline import ShootingTimelineDialog
        ShootingTimelineDialog(self, self.app.con)

    def _quicklook_sel(self, _e=None):
        sel = self.tv_res.selection()
        if not sel:
            return
        # Collect paths for all selected items (multi-file QuickLook gallery)
        paths = []
        offline_name = None
        for iid in sel:
            idx = int(iid)
            if idx < len(self.search_rows):
                r = self.search_rows[idx]
                full = full_path_of(self.app.con, r, self.app.online)
                if full and os.path.exists(full):
                    paths.append(full)
                else:
                    fid = r["id"] if "id" in r.keys() else None
                    from catalogue_app.config import THUMBNAILS_DIR
                    thumb_path = os.path.join(THUMBNAILS_DIR, f"{fid}.jpg") if fid else None
                    if thumb_path and os.path.exists(thumb_path):
                        paths.append(thumb_path)
                    else:
                        offline_name = r["volume_name"]
        if paths:
            quick_preview(paths)
        elif offline_name:
            messagebox.showinfo(
                APP_NAME,
                f'Le disque « {offline_name} » n\'est pas branché actuellement.')

    def _reveal_sel(self):
        r = self._sel_row()
        if not r:
            return
        if not reveal(full_path_of(self.app.con, r, self.app.online)):
            self.app._refresh_online(silent=True)
            if reveal(full_path_of(self.app.con, r, self.app.online)):
                return
            messagebox.showinfo(
                APP_NAME,
                f'Le disque « {r["volume_name"]} » n\'est pas branché.\n\n'
                f'Branchez-le, puis cliquez sur « Détecter les disques branchés ».\n\n'
                f'Chemin sur le disque :\n{r["rel_path"]}')

    def _set_global_cat_selection(self):
        sel = self.tv_res.selection()
        if not sel:
            messagebox.showinfo(APP_NAME, "Sélectionnez des fichiers d'abord.")
            return
        
        try:
            from catalogue_app.settings_manager import get_global_categories
            cats = get_global_categories()
        except Exception:
            cats = ["B-Roll", "Interviews", "Vlogs", "Archives", "Rushes", "Masters"]
            
        from tkinter import simpledialog
        
        # Simple custom dialog to select from combobox
        top = tk.Toplevel(self)
        top.title("Catégorie Globale")
        ttk.Label(top, text=f"Choisir la catégorie globale pour {len(sel)} fichiers :").pack(padx=20, pady=10)
        cmb = ttk.Combobox(top, values=cats)
        cmb.pack(padx=20, pady=5)
        if cats: cmb.set(cats[0])
        
        res = {"cat": None}
        def on_ok():
            res["cat"] = cmb.get()
            top.destroy()
            
        ttk.Button(top, text="OK", command=on_ok).pack(pady=10)
        
        top.transient(self)
        top.grab_set()
        self.wait_window(top)
        
        cat_val = res["cat"]
        if cat_val:
            try:
                from catalogue_app.db import connect
                local_con = connect()
                file_ids = [self.search_rows[int(i)]["id"] for i in sel]
                placeholders = ",".join("?" for _ in file_ids)
                local_con.execute(f"UPDATE files SET global_cat = ? WHERE id IN ({placeholders})", [cat_val] + file_ids)
                local_con.commit()
                self._do_search()
            except Exception as e:
                messagebox.showerror(APP_NAME, f"Erreur : {e}")

    def _add_tag_to_selection(self):

        rows = self._sel_rows()
        if not rows:
            messagebox.showinfo(APP_NAME, "Sélectionnez d'abord un ou plusieurs fichiers.")
            return
        name = simpledialog.askstring(
            APP_NAME, f"Étiquette à ajouter aux {len(rows)} fichier(s) sélectionné(s) :\n"
                      "(ex. « interview ministre », « Al Oubour séq. 12 »)", parent=self)
        if not name:
            return
        add_manual_tag(self.app.con, [r["id"] for r in rows], name)
        self.app.refresh_tags()
        self._do_search()
        self.app.status.set(f'Étiquette « {name} » ajoutée à {len(rows)} fichier(s).')

    def _export_fcp_xml(self, default_name="montage_rushes.xml", sort_chrono=False):
        if not getattr(self, "search_rows", None):
            messagebox.showinfo(APP_NAME, "Aucun résultat de recherche à exporter.")
            return
        p = filedialog.asksaveasfilename(defaultextension=".xml",
                                         initialfile=default_name,
                                         filetypes=[("Final Cut Pro 7 / Premiere XML", "*.xml")])
        if not p:
            return
        rows_to_export = [dict(r) for r in self.search_rows]
        if sort_chrono:
            rows_to_export.sort(key=lambda r: str(r.get("shot_date") or r.get("mtime") or ""))
        clips = []
        for r in rows_to_export:
            full = full_path_of(self.app.con, r, self.app.online) or r.get("rel_path") or r.get("name", "")
            clips.append({
                "name": r["name"],
                "path": full,
                "width": r.get("width"),
                "height": r.get("height"),
                "fps": r.get("fps"),
                "duration": r.get("duration")
            })
        try:
            generate_fcp_xml(clips, p, project_name="Montage Rushes Catalogue", create_sequence=True)
            if messagebox.askyesno(APP_NAME, f"Timeline XML générée avec succès pour {len(clips)} clip(s) !\n\nCompatible avec Adobe Premiere Pro, DaVinci Resolve et Final Cut.\n\nSouhaitez-vous afficher le fichier dans le Finder ?"):
                import subprocess
                subprocess.Popen(["open", "-R", p])
        except Exception as e:
            messagebox.showerror(APP_NAME, f"Erreur export XML : {e}")

    def _export_xmp(self):
        if not getattr(self, "search_rows", None):
            messagebox.showinfo(APP_NAME, "Aucun résultat de recherche à exporter.")
            return
        out_dir = filedialog.askdirectory(title="Choisir le dossier de destination pour les fichiers XMP sidecars")
        if not out_dir:
            return
        try:
            from catalogue_app.export_xmp import export_xmp_sidecars
            n = export_xmp_sidecars(self.app.con, self.search_rows, output_dir=out_dir)
            messagebox.showinfo(APP_NAME, f"{n} fichier(s) sidecar .xmp généré(s) avec succès dans :\n{out_dir}")
        except Exception as e:
            messagebox.showerror(APP_NAME, f"Erreur export XMP : {e}")

    def _export_results(self):
        if not self.search_rows:
            return
        p = filedialog.asksaveasfilename(defaultextension=".csv",
                                         initialfile="resultats_recherche.csv",
                                         filetypes=[("CSV", "*.csv")])
        if p:
            export_rows(self.search_rows, p, con=self.app.con, with_tags=True)
            messagebox.showinfo(APP_NAME, "Export terminé.")



    # ===== Panier de sélection (Monteur) =====
    @staticmethod
    def _rget(row, key, default=None):
        try:
            v = row[key]
            return default if v is None else v
        except (KeyError, IndexError):
            return default

    def _add_to_basket(self):
        rows = self._sel_rows()
        if not rows:
            return
        added = 0
        for row in rows:
            path = full_path_of(self.app.con, row, self.app.online) or self._rget(row, "rel_path", "")
            if not path or path in self.basket_items:
                continue
            self.basket_items[path] = row
            dur = self._rget(row, "duration", 0) or 0
            try:
                dur_s = human_clock(float(dur)) if dur else ""
            except (TypeError, ValueError):
                dur_s = ""
            vol = self._rget(row, "volume_name", "") or self._rget(row, "vol_name", "")
            self.tv_basket.insert("", "end", iid=path, values=(self._rget(row, "name", ""), dur_s, vol))
            added += 1
        if added:
            self.app.status.set(f"{added} clip(s) ajouté(s) au panier.")

    def _clear_basket(self):
        for item in self.tv_basket.get_children():
            self.tv_basket.delete(item)
        self.basket_items.clear()
        self.app.status.set("Le panier a été vidé.")

    def _generate_proxies(self):
        if not self.basket_items:
            messagebox.showinfo("Panier vide", "Le panier est vide. Ajoutez des vidéos depuis la recherche !")
            return
        import shutil
        if not shutil.which("ffmpeg"):
            messagebox.showerror("FFmpeg introuvable", "FFmpeg n'est pas installé (brew install ffmpeg).")
            return
        from catalogue_app.proxy_generator import ProxyWindow
        ProxyWindow(self.app, list(self.basket_items.keys()))

    def _export_basket_xml(self):
        if not self.basket_items:
            messagebox.showinfo("Panier vide", "Le panier est vide. Ajoutez des clips depuis la recherche !")
            return
        save_path = filedialog.asksaveasfilename(
            title="Exporter l'ours de montage XML", defaultextension=".xml",
            filetypes=[("Final Cut Pro XML", "*.xml")], initialfile="Rushes_Selection.xml")
        if not save_path:
            return
        clips = []
        for path, row in self.basket_items.items():
            try:
                fps = float(self._rget(row, "fps", 25.0) or 25.0)
                dur = float(self._rget(row, "duration", 5.0) or 5.0)
            except (TypeError, ValueError):
                fps, dur = 25.0, 5.0
            clips.append({"name": self._rget(row, "name", os.path.basename(path)), "path": path,
                          "fps": fps, "duration": dur,
                          "width": int(self._rget(row, "width", 1920) or 1920),
                          "height": int(self._rget(row, "height", 1080) or 1080)})
        try:
            generate_fcp_xml(clips, save_path, project_name="Sélection Rushes")
            self.app.status.set(f"Export XML réussi : {os.path.basename(save_path)}")
            if messagebox.askyesno("Ouvrir", "Ouvrir le dossier contenant le XML ?"):
                subprocess.call(["open", os.path.dirname(save_path)])
        except Exception as e:
            messagebox.showerror("Erreur", f"Échec de l'export XML : {e}")
