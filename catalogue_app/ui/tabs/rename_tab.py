import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import subprocess
import threading
import json
import re as re_mod
import datetime

# DND import, fallback gracefully
try:
    from tkinterdnd2 import DND_FILES
    HAS_DND = True
except ImportError:
    HAS_DND = False

from catalogue_app.ui.tabs.base_tab import BaseTab
from catalogue_app.batch_renamer import (
    scan_files_for_renaming, preview_batch_rename, execute_batch_rename,
    sanitize_filename, DEFAULT_MEDIA_EXTS
)

class RenameTab(BaseTab):
    def _build_ui(self):
        f = self
        
        # Variables de contrôle
        self.var_rename_dir = tk.StringVar()
        self.var_rename_prefix = tk.StringVar(value="PROJET_A_RUSH")
        self.var_rename_num_mode = tk.StringVar(value="Séquence ordonnée (001, 002...)")
        self.var_rename_start = tk.StringVar(value="1")
        self.var_rename_padding = tk.StringVar(value="3 chiffres (001)")
        self.var_rename_sort = tk.StringVar(value="Date de tournage (chronologique)")
        self.var_rename_recursive = tk.BooleanVar(value=True)
        self.var_rename_media_only = tk.BooleanVar(value=True)
        self.var_rename_link_sidecars = tk.BooleanVar(value=True)
        self.var_rename_clean_nle = tk.BooleanVar(value=True)
        self.rename_scanned_files = []
        self.rename_preview_data = []

        # --- Agent Renommeur IA ---
        ai_renamer = ttk.LabelFrame(f, text=" Agent Renommeur IA ", padding=5)
        ai_renamer.pack(fill="x", padx=10, pady=(10, 0))
        
        self.txt_renamer_agent = tk.Text(ai_renamer, height=2, wrap="word", bg="#1e1e2e", fg="#f38ba8", font=("TkDefaultFont", 11, "italic"))
        self.txt_renamer_agent.pack(fill="x", expand=True, side="left", padx=(0,10))
        self.txt_renamer_agent.insert("1.0", "L'agent peut suggérer des préfixes ou analyser le nommage. Sélectionne un dossier d'abord.")
        self.txt_renamer_agent.config(state="disabled")

        def ask_renamer_agent():
            self.btn_renamer_agent.config(text="Analyse...", state="disabled")
            self.update_idletasks()
            def worker():
                try:
                    from catalogue_app.agents import RenamerAgent
                    agent = RenamerAgent()
                    
                    d = self.var_rename_dir.get().strip()
                    folder_hint = os.path.basename(d) if d else "Racine"
                    
                    # Context: first 5 files
                    samples = [{"filename": item["old_name"]} for item in self.rename_preview_data[:5]]
                    
                    context_data = {
                        "dossier": folder_hint,
                        "fichiers_exemple": samples
                    }
                    
                    resp = agent.analyze_naming(context_data)
                    self.after(0, lambda r=resp: _update_renamer_txt(r))
                except Exception as e:
                    err_msg = str(e)
                    self.after(0, lambda err=err_msg: _update_renamer_txt(f"Erreur Agent: {err}"))
                finally:
                    self.after(0, lambda: self.btn_renamer_agent.config(text="🤖 Demander Conseil IA", state="normal"))
                    
            def _update_renamer_txt(t):
                match = re_mod.search(r'```action\s*(.*?)\s*```', t, re_mod.DOTALL)
                clean_t = t
                if match:
                    clean_t = t.replace(match.group(0), "").strip()
                    try:
                        act = json.loads(match.group(1))
                        if act.get("command") == "RENAME_FILE":
                            new_name = act.get("new_name", "")
                            if new_name:
                                prefix = new_name.split("_")[0] if "_" in new_name else new_name
                                self.var_rename_prefix.set(prefix)
                                self._update_rename_preview()
                    except:
                        pass
                self.txt_renamer_agent.config(state="normal")
                self.txt_renamer_agent.delete("1.0", "end")
                self.txt_renamer_agent.insert("1.0", clean_t)
                self.txt_renamer_agent.config(state="disabled")

            threading.Thread(target=worker, daemon=True).start()

        self.btn_renamer_agent = ttk.Button(ai_renamer, text="🤖 Demander Conseil IA", command=ask_renamer_agent)
        self.btn_renamer_agent.pack(side="right")

        # --- 1. En-tête : Configuration ---
        cfg_frame = ttk.LabelFrame(f, text=" Configuration du Renommage de Carte / Rushes ", padding=10)
        cfg_frame.pack(fill="x", padx=10, pady=(10, 5))

        # Ligne 1 : Source & Dossier
        row1 = ttk.Frame(cfg_frame)
        row1.pack(fill="x", pady=2)
        ttk.Label(row1, text="📁 Dossier Source / Carte :", font=("TkDefaultFont", 9, "bold")).pack(side="left")
        e_dir = ttk.Entry(row1, textvariable=self.var_rename_dir)
        e_dir.pack(side="left", fill="x", expand=True, padx=6)

        def _browse_rename_dir():
            d = filedialog.askdirectory(title="Sélectionner le dossier des rushes ou la carte mémoire")
            if d:
                self.var_rename_dir.set(d)
                base_n = os.path.basename(d)
                if base_n and base_n not in ("DCIM", "CONTENTS", "CLIPS"):
                    self.var_rename_prefix.set(sanitize_filename(base_n))
                self._update_rename_preview()

        ttk.Button(row1, text="📂 Parcourir...", command=_browse_rename_dir).pack(side="left", padx=2)

        chk_rec = ttk.Checkbutton(row1, text="Inclure sous-dossiers (respecter l'arborescence)",
                                  variable=self.var_rename_recursive, command=lambda: self._update_rename_preview())
        chk_rec.pack(side="left", padx=(10, 5))

        chk_media = ttk.Checkbutton(row1, text="Médias uniquement",
                                    variable=self.var_rename_media_only, command=lambda: self._update_rename_preview())
        chk_media.pack(side="left", padx=5)

        # Support Drag & Drop natif macOS
        def _on_rename_drop(event):
            path = event.data.strip()
            if path.startswith('{') and path.endswith('}'):
                path = path[1:-1]
            if os.path.isfile(path):
                path = os.path.dirname(path)
            if os.path.isdir(path):
                self.var_rename_dir.set(path)
                base_n = os.path.basename(path)
                if base_n and base_n not in ("DCIM", "CONTENTS", "CLIPS"):
                    self.var_rename_prefix.set(sanitize_filename(base_n))
                self._update_rename_preview()

        if HAS_DND:
            cfg_frame.drop_target_register(DND_FILES)
            cfg_frame.dnd_bind('<<Drop>>', _on_rename_drop)
            e_dir.drop_target_register(DND_FILES)
            e_dir.dnd_bind('<<Drop>>', _on_rename_drop)

        # Ligne 2 : Nouveau Nom & Modèle
        row2 = ttk.Frame(cfg_frame)
        row2.pack(fill="x", pady=(6, 2))
        ttk.Label(row2, text="🏷️ Nouveau Nom de base (Préfixe) :", font=("TkDefaultFont", 9, "bold")).pack(side="left")
        e_prefix = ttk.Entry(row2, textvariable=self.var_rename_prefix, width=28)
        e_prefix.pack(side="left", padx=6)
        e_prefix.bind("<KeyRelease>", lambda _e: self._update_rename_preview())

        def _insert_today():
            today_str = datetime.datetime.now().strftime("%Y%m%d_")
            cur = self.var_rename_prefix.get()
            if not cur.startswith(today_str):
                self.var_rename_prefix.set(today_str + cur)
            self._update_rename_preview()

        def _insert_folder_name():
            d = self.var_rename_dir.get().strip()
            if d and os.path.isdir(d):
                b = sanitize_filename(os.path.basename(d))
                self.var_rename_prefix.set(b)
                self._update_rename_preview()

        ttk.Button(row2, text="[+ Date AAAAMMJJ]", command=_insert_today).pack(side="left", padx=2)
        ttk.Button(row2, text="[+ Nom Dossier]", command=_insert_folder_name).pack(side="left", padx=2)

        # Ligne 3 : Options de numérotation
        row3 = ttk.Frame(cfg_frame)
        row3.pack(fill="x", pady=(6, 2))

        ttk.Label(row3, text="🔢 Numérotation :").pack(side="left")
        cmb_mode = ttk.Combobox(row3, textvariable=self.var_rename_num_mode, state="readonly", width=28,
                                values=["Séquence ordonnée (001, 002...)",
                                        "Conserver le numéro d'origine du rush",
                                        "Aucun numéro (préfixe seul)"])
        cmb_mode.pack(side="left", padx=4)
        cmb_mode.bind("<<ComboboxSelected>>", lambda _e: self._update_rename_preview())

        ttk.Label(row3, text="Chiffres :").pack(side="left", padx=(8, 2))
        cmb_pad = ttk.Combobox(row3, textvariable=self.var_rename_padding, state="readonly", width=14,
                               values=["3 chiffres (001)", "4 chiffres (0001)", "2 chiffres (01)", "5 chiffres (00001)"])
        cmb_pad.pack(side="left", padx=2)
        cmb_pad.bind("<<ComboboxSelected>>", lambda _e: self._update_rename_preview())

        ttk.Label(row3, text="Départ :").pack(side="left", padx=(8, 2))
        e_start = ttk.Entry(row3, textvariable=self.var_rename_start, width=5)
        e_start.pack(side="left", padx=2)
        e_start.bind("<KeyRelease>", lambda _e: self._update_rename_preview())

        ttk.Label(row3, text="Ordre :").pack(side="left", padx=(8, 2))
        cmb_sort = ttk.Combobox(row3, textvariable=self.var_rename_sort, state="readonly", width=24,
                                values=["Date de tournage (chronologique)", "Nom d'origine (alphabétique)"])
        cmb_sort.pack(side="left", padx=2)
        cmb_sort.bind("<<ComboboxSelected>>", lambda _e: self._update_rename_preview())

        chk_sidecar = ttk.Checkbutton(row3, text="Lier sidecars (.XML, .THM)",
                                      variable=self.var_rename_link_sidecars, command=lambda: self._update_rename_preview())
        chk_sidecar.pack(side="left", padx=(10, 2))

        chk_clean = ttk.Checkbutton(row3, text="Zéro accent",
                                    variable=self.var_rename_clean_nle, command=lambda: self._update_rename_preview())
        chk_clean.pack(side="left", padx=4)

        # --- 2. Zone Centrale : Tableau Prévisualisation (Avant ➡️ Après) ---
        tree_frame = ttk.LabelFrame(f, text=" Prévisualisation des Rushes (Avant ➡️ Après) ", padding=6)
        tree_frame.pack(fill="both", expand=True, padx=10, pady=5)

        cols = ("rel_dir", "old_name", "new_name", "size", "date", "status")
        heads = ("Arborescence (Dossier)", "Nom Actuel (Ancien)", "➡️ Nouveau Nom Prévu", "Taille", "Date Prise / Modif", "Statut")
        self.tv_rename = ttk.Treeview(tree_frame, columns=cols, show="headings", height=10)

        widths = (160, 230, 250, 85, 140, 90)
        for c_name, h_text, w in zip(cols, heads, widths):
            self.tv_rename.heading(c_name, text=h_text)
            self.tv_rename.column(c_name, width=w, anchor="w" if c_name not in ("size", "status") else "center")

        self.tv_rename.pack(side="left", fill="both", expand=True)

        rsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tv_rename.yview)
        rsb.pack(side="right", fill="y")
        self.tv_rename.configure(yscrollcommand=rsb.set)

        # Coup d'œil QuickLook macOS
        def _ql_batch_rename(_e=None):
            sel = self.tv_rename.selection()
            if not sel: return
            idx = int(sel[0])
            if 0 <= idx < len(self.rename_preview_data):
                p = self.rename_preview_data[idx]["full_old_path"]
                if os.path.exists(p):
                    quick_preview(p)

        self.tv_rename.bind("<space>", _ql_batch_rename)

        # Menu contextuel
        self.menu_batch_rename = tk.Menu(tree_frame, tearoff=0)
        self.menu_batch_rename.add_command(label="👁️ Coup d'œil (Espace)", command=_ql_batch_rename)
        def _reveal_in_finder():
            sel = self.tv_rename.selection()
            if not sel: return
            idx = int(sel[0])
            if 0 <= idx < len(self.rename_preview_data):
                p = self.rename_preview_data[idx]["full_old_path"]
                if os.path.exists(p):
                    subprocess.Popen(["open", "-R", p])
        self.menu_batch_rename.add_command(label="📂 Révéler dans le Finder", command=_reveal_in_finder)

        def popup_batch_rename(event):
            iid = self.tv_rename.identify_row(event.y)
            if iid:
                self.tv_rename.selection_set(iid)
                self.menu_batch_rename.post(event.x_root, event.y_root)

        if sys.platform == "darwin":
            self.tv_rename.bind("<Button-2>", popup_batch_rename)
            self.tv_rename.bind("<Control-Button-1>", popup_batch_rename)
        else:
            self.tv_rename.bind("<Button-3>", popup_batch_rename)

        # --- 3. Barre Inférieure : Actions & Sécurité ---
        bot_frame = ttk.Frame(f, padding=(10, 6))
        bot_frame.pack(fill="x", padx=10, pady=(0, 10))

        self.lbl_rename_count = ttk.Label(bot_frame, text="Glissez-déposez un dossier ou cliquez sur 'Parcourir' pour commencer.",
                                          font=("TkDefaultFont", 10), foreground="#89b4fa")
        self.lbl_rename_count.pack(side="left", padx=5)

        self.btn_execute_rename = ttk.Button(bot_frame, text="⚡ Renommer les Rushes en Masse",
                                             command=self._do_batch_rename, style="Accent.TButton")
        self.btn_execute_rename.pack(side="right", padx=5)

        ttk.Button(bot_frame, text="🔄 Actualiser / Prévisualiser",
                   command=self._update_rename_preview).pack(side="right", padx=5)

    def _update_rename_preview(self):
        d = self.var_rename_dir.get().strip()
        if not d or not os.path.isdir(d):
            self.tv_rename.delete(*self.tv_rename.get_children())
            self.lbl_rename_count.config(text="Veuillez sélectionner un dossier valide contenant des rushes.")
            return

        try:
            # 1. Scanner les fichiers
            self.rename_scanned_files = scan_files_for_renaming(
                d,
                recursive=self.var_rename_recursive.get(),
                filter_media_only=self.var_rename_media_only.get()
            )

            if not self.rename_scanned_files:
                self.tv_rename.delete(*self.tv_rename.get_children())
                self.lbl_rename_count.config(text="Aucun fichier correspondant trouvé dans ce dossier.")
                return

            # 2. Options de numérotation
            mode_str = self.var_rename_num_mode.get()
            if "Séquence" in mode_str:
                num_mode = "seq"
            elif "origine" in mode_str:
                num_mode = "orig"
            else:
                num_mode = "keep"

            try:
                start_num = int(self.var_rename_start.get().strip())
            except:
                start_num = 1

            pad_str = self.var_rename_padding.get()
            pad_val = 3
            if "4" in pad_str: pad_val = 4
            elif "2" in pad_str: pad_val = 2
            elif "5" in pad_str: pad_val = 5

            sort_val = "date" if "Date" in self.var_rename_sort.get() else "name"

            # 3. Calculer la prévisualisation
            self.rename_preview_data = preview_batch_rename(
                files=self.rename_scanned_files,
                prefix=self.var_rename_prefix.get(),
                numbering_mode=num_mode,
                start_num=start_num,
                padding=pad_val,
                sort_by=sort_val,
                link_sidecars=self.var_rename_link_sidecars.get(),
                clean_nle=self.var_rename_clean_nle.get()
            )

            # 4. Remplir le tableau
            self.tv_rename.delete(*self.tv_rename.get_children())
            conflits = 0
            a_renommer = 0

            for i, item in enumerate(self.rename_preview_data):
                sz_mb = f"{item['size'] / (1024*1024):.1f} Mo" if item['size'] >= 1024*1024 else f"{item['size'] // 1024} Ko"
                date_str = datetime.datetime.fromtimestamp(item['mtime']).strftime("%Y-%m-%d %H:%M") if item['mtime'] else "--"
                
                if item['status'] == "⚠️ Conflit":
                    conflits += 1
                if item['old_name'] != item['new_name']:
                    a_renommer += 1

                self.tv_rename.insert("", "end", iid=str(i), values=(
                    item["rel_dir"],
                    item["old_name"],
                    item["new_name"],
                    sz_mb,
                    date_str,
                    item["status"]
                ))

            # Statut récapitulatif
            tot = len(self.rename_preview_data)
            if conflits > 0:
                self.lbl_rename_count.config(text=f"⚠️ {tot} fichiers détectés | {a_renommer} à renommer | ⛔ {conflits} CONFLIT(S) DÉTECTÉ(S) !", foreground="#f38ba8")
            else:
                self.lbl_rename_count.config(text=f"✅ {tot} rush(es) détecté(s) | {a_renommer} prêt(s) à être renommé(s) en conservant l'arborescence.", foreground="#a6e3a1")

        except Exception as e:
            self.lbl_rename_count.config(text=f"Erreur d'analyse : {e}", foreground="#f38ba8")

    def _do_batch_rename(self):
        if not self.rename_preview_data:
            messagebox.showinfo("Renommage", "Aucun fichier à renommer. Veuillez d'abord sélectionner un dossier.")
            return

        items_to_rename = [it for it in self.rename_preview_data if it["old_name"] != it["new_name"]]
        if not items_to_rename:
            messagebox.showinfo("Renommage", "Tous les fichiers portent déjà le nouveau nom (rien à changer).")
            return

        conflits = [it for it in self.rename_preview_data if it["status"] == "⚠️ Conflit"]
        if conflits:
            messagebox.showerror("Conflit de noms", f"Impossible d'exécuter : {len(conflits)} fichier(s) ont un nom en conflit.\nModifiez le préfixe ou le numéro de départ.")
            return

        # Demande d'autorisation stricte à l'utilisateur (Règle d'or de sécurité)
        msg = (
            f"🚨 CONFIRMATION DE RENOMMAGE\n\n"
            f"Nombre de rushes à renommer : {len(items_to_rename)}\n"
            f"Dossier source : {self.var_rename_dir.get()}\n\n"
            f"Exemple de renommage :\n"
            f"  Ancien : {items_to_rename[0]['old_name']}\n"
            f"  ➡️ Nouveau : {items_to_rename[0]['new_name']}\n\n"
            f"L'arborescence des sous-dossiers sera strictement conservée.\n"
            f"Voulez-vous lancer le renommage physique sur le disque ?"
        )
        if not messagebox.askyesno("Autorisation de renommage", msg, icon="warning"):
            return

        if hasattr(self.app, 'status'):
            self.app.status.set(f"Renommage de {len(items_to_rename)} fichiers en cours...")
        self.update_idletasks()

        try:
            succ, err_count, errors = execute_batch_rename(self.rename_preview_data, db_connection=self.app.con)
            if err_count == 0:
                messagebox.showinfo("Renommage Réussi", f"🎉 Félicitations !\n\n{succ} rush(es) ont été renommés avec succès.\nL'arborescence a été scrupuleusement conservée.")
            else:
                err_msg = "\n".join(errors[:5])
                messagebox.showwarning("Renommage partiel", f"{succ} fichier(s) renommés avec succès.\n{err_count} erreur(s) :\n{err_msg}")
            
            # Actualiser la vue et le catalogue
            self._update_rename_preview()
            if hasattr(self.app, '_do_search'):
                self.app._do_search()
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors du renommage : {e}")
        finally:
            if hasattr(self.app, 'status'):
                self.app.status.set("Prêt.")
