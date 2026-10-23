"""
Onglet Synchronisation Image & Son pour CatalogueApp.
Permet d'apparier et de synchroniser automatiquement les rushes vidéo et les prises de son externes
(par analyse de forme d'onde FFT, détection de clap, timecode ou mode hybride),
puis d'exporter une timeline synchronisée XML compatible Premiere Pro 2026, DaVinci Resolve et FCP.

Supporte :
- Multi-Caméras dynamiques : Caméra 1 (A), Caméra 2 (B), Caméra 3 (C)... avec ajout/suppression [+] / [-]
- Support de dossiers complets OU de fichiers individuels par caméra et son
- Séparation multipistes Zoom F8 / Sound Devices : chaque micro (Ch 1 à 8) sur sa propre piste timeline (A1, A2, A3...)
- Liaison Audio/Vidéo native (<link>) sous Adobe Premiere Pro 2026
"""

import os
import sys
import subprocess
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

try:
    from tkinterdnd2 import DND_FILES
    HAS_DND = True
except ImportError:
    HAS_DND = False

from catalogue_app.ui.tabs.base_tab import BaseTab
from catalogue_app.config import *
from catalogue_app.utils import *
from catalogue_app.db import *
from catalogue_app.queries import *
from catalogue_app.sync_engine import (
    scan_media_directory, pair_and_sync, generate_synced_xml,
    resolve_media_inputs, VIDEO_EXTS, AUDIO_EXTS
)


class SyncTab(BaseTab):
    def __init__(self, parent, app, **kwargs):
        super().__init__(parent, app, **kwargs)

    def _set_status(self, text):
        """Met à jour le statut global de l'application s'il est disponible."""
        if hasattr(self, 'app') and hasattr(self.app, 'status'):
            self.app.status.set(text)
        elif hasattr(self, 'status') and hasattr(self.app.status, 'set'):
            self.app.status.set(text)

    def _build_ui(self):
        f = self

        # Variables de contrôle
        self.var_sync_method = tk.StringVar(value="Forme d'onde (Waveform FFT Matching)")
        self.var_multicam = tk.BooleanVar(value=True)
        self.var_split_tracks = tk.BooleanVar(value=True)
        self.sync_results = []

        # Listes dynamiques des lignes Caméras et Audio
        self.cam_rows = []
        self.audio_rows = []

        # --- En-tête : Sélection des Sources Multi-Caméras & Audio ---
        self.top_box = ttk.LabelFrame(f, text=" Sélection des Sources Multi-Caméras & Son Master (Zoom F8 / Multipistes) ", padding=10)
        self.top_box.pack(fill="x", padx=10, pady=(10, 5))

        # Conteneur des lignes de caméras
        self.cams_container = ttk.Frame(self.top_box)
        self.cams_container.pack(fill="x", pady=2)

        # Ligne de séparation visuelle
        ttk.Separator(self.top_box, orient="horizontal").pack(fill="x", pady=6)

        # Conteneur des lignes audio
        self.audios_container = ttk.Frame(self.top_box)
        self.audios_container.pack(fill="x", pady=2)

        # Créer les premières lignes par défaut (Caméra 1 et Son Master)
        self._add_cam_row()
        self._add_audio_row()

        # Ligne de séparation
        ttk.Separator(self.top_box, orient="horizontal").pack(fill="x", pady=6)

        # Ligne Options, Technique de Synchro & Bouton Lancer
        row_opts = ttk.Frame(self.top_box)
        row_opts.pack(fill="x", pady=(4, 2))

        ttk.Label(row_opts, text="⚙️ Technique :", font=("TkDefaultFont", 9, "bold"), width=14, anchor="w").pack(side="left")
        cmb_method = ttk.Combobox(row_opts, textvariable=self.var_sync_method, state="readonly", width=34,
                                  values=[
                                      "Forme d'onde (Waveform FFT Matching)",
                                      "Détection de Clap (Pic Transitoire)",
                                      "Timecode & Horodatage (TC / BWF)",
                                      "Hybride Automatique (Waveform + Clap fallback)"
                                  ])
        cmb_method.pack(side="left", padx=4)

        ttk.Checkbutton(
            row_opts,
            text="🎚️ Séparer chaque micro Zoom F8 (A1, A2, A3...)",
            variable=self.var_split_tracks
        ).pack(side="left", padx=8)

        ttk.Checkbutton(
            row_opts,
            text="🔗 Multi-Cam (V1, V2... + A1)",
            variable=self.var_multicam
        ).pack(side="left", padx=6)

        self.btn_start_sync = ttk.Button(row_opts, text="⚡ Lancer la Synchronisation",
                                         command=self._do_auto_sync, style="Accent.TButton")
        self.btn_start_sync.pack(side="right", padx=5)

        # Barre de progression de synchro
        self.pb_sync = ttk.Progressbar(self.top_box, orient="horizontal", mode="determinate")
        self.pb_sync.pack(fill="x", pady=(8, 2))

        # --- Zone Centrale : Tableau des Rushes Synchronisés ---
        mid_box = ttk.LabelFrame(f, text=" Tableau des Paires & Angles Multi-Cam Synchronisés ", padding=6)
        mid_box.pack(fill="both", expand=True, padx=10, pady=5)

        cols = ("video", "audio", "track", "method", "offset_sec", "offset_frames", "confidence", "status")
        heads = ("Rush Vidéo", "Son Master / Zoom F8", "Piste & Liaison", "Technique", "Décalage (s)", "Décalage (Images)", "Précision", "Statut")
        widths = (210, 210, 160, 130, 90, 110, 80, 90)

        self.tv_sync = ttk.Treeview(mid_box, columns=cols, show="headings", height=10)
        for c_name, h_text, w in zip(cols, heads, widths):
            self.tv_sync.heading(c_name, text=h_text)
            self.tv_sync.column(c_name, width=w, anchor="w" if c_name in ("video", "audio") else "center")

        self.tv_sync.pack(side="left", fill="both", expand=True)

        sb_sync = ttk.Scrollbar(mid_box, orient="vertical", command=self.tv_sync.yview)
        sb_sync.pack(side="right", fill="y")
        self.tv_sync.configure(yscrollcommand=sb_sync.set)

        # Coup d'œil macOS QuickLook
        self.tv_sync.bind("<space>", self._ql_sync_video)

        # Menu contextuel
        self.menu_sync = tk.Menu(mid_box, tearoff=0)
        self.menu_sync.add_command(label="👁️ Voir la Vidéo (Espace)", command=self._ql_sync_video)
        self.menu_sync.add_command(label="🎵 Écouter le Son Master (afplay)", command=self._play_sync_audio)
        self.menu_sync.add_command(label="📂 Révéler la Vidéo dans le Finder", command=self._reveal_sync_v)
        self.menu_sync.add_command(label="📂 Révéler le Son dans le Finder", command=self._reveal_sync_a)

        if sys.platform == "darwin":
            self.tv_sync.bind("<Button-2>", self._popup_sync_menu)
            self.tv_sync.bind("<Control-Button-1>", self._popup_sync_menu)
        else:
            self.tv_sync.bind("<Button-3>", self._popup_sync_menu)

        # --- Zone Inférieure : Rapport & Export XML ---
        bot_box = ttk.Frame(f, padding=(10, 8))
        bot_box.pack(fill="x", padx=10, pady=(0, 10))

        self.lbl_sync_report = ttk.Label(
            bot_box,
            text="Sélectionnez vos caméras (Cam 1, Cam 2...) et le son du Zoom F8 pour synchroniser.",
            font=("TkDefaultFont", 10), foreground="#89b4fa"
        )
        self.lbl_sync_report.pack(side="left", padx=5)

        self.btn_export_sync_xml = ttk.Button(bot_box, text="🎬 Exporter Timeline Synchronisée (XML NLE)",
                                              command=self._export_synced_xml)
        self.btn_export_sync_xml.pack(side="right", padx=5)

    # ---------------------------------------------------------
    # Gestion Dynamique des Caméras (Caméra 1, Caméra 2, etc.)
    # ---------------------------------------------------------
    def _add_cam_row(self):
        idx = len(self.cam_rows)
        letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        cam_letter = letters[idx] if idx < len(letters) else str(idx + 1)
        cam_num = idx + 1
        label_text = f"🎥 Caméra {cam_num} ({cam_letter}) :"

        row = ttk.Frame(self.cams_container)
        row.pack(fill="x", pady=2)

        lbl = ttk.Label(row, text=label_text, font=("TkDefaultFont", 9, "bold"), width=20, anchor="w")
        lbl.pack(side="left")

        var_path = tk.StringVar()
        entry = ttk.Entry(row, textvariable=var_path)
        entry.pack(side="left", fill="x", expand=True, padx=4)

        lbl_count = ttk.Label(row, text="0 vidéo", foreground="gray", width=12, anchor="e")

        btn_dir = ttk.Button(row, text="📂 Dossier...", command=lambda v=var_path: self._browse_dir_for(v))
        btn_dir.pack(side="left", padx=2)

        btn_file = ttk.Button(row, text="📄 Fichier...", command=lambda v=var_path: self._browse_file_for(v, VIDEO_EXTS))
        btn_file.pack(side="left", padx=2)

        lbl_count.pack(side="left", padx=4)

        cam_data = {
            "index": cam_num,
            "label": f"Cam-{cam_letter}",
            "var_path": var_path,
            "row_frame": row,
            "lbl_count": lbl_count
        }

        # Bouton d'action (+) ou (-)
        if idx == 0:
            btn_add = ttk.Button(row, text="➕ Ajouter Caméra", command=self._add_cam_row)
            btn_add.pack(side="left", padx=3)
            cam_data["btn_action"] = btn_add
        else:
            btn_del = ttk.Button(row, text="➖ Retirer", command=lambda cd=cam_data: self._remove_cam_row(cd))
            btn_del.pack(side="left", padx=3)
            cam_data["btn_action"] = btn_del

        # Drag & Drop macOS
        if HAS_DND:
            entry.drop_target_register(DND_FILES)
            entry.dnd_bind('<<Drop>>', lambda e, v=var_path: self._on_generic_drop(e, v))

        var_path.trace_add("write", lambda *args: self._update_sync_counts())
        self.cam_rows.append(cam_data)
        self._update_cam_headers()

    def _remove_cam_row(self, cam_data):
        if cam_data in self.cam_rows:
            cam_data["row_frame"].destroy()
            self.cam_rows.remove(cam_data)
            self._update_cam_headers()
            self._update_sync_counts()

    def _update_cam_headers(self):
        letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        for i, c in enumerate(self.cam_rows):
            c["index"] = i + 1
            cam_letter = letters[i] if i < len(letters) else str(i + 1)
            c["label"] = f"Cam-{cam_letter}"
            # Mettre à jour le texte du label
            for child in c["row_frame"].winfo_children():
                if isinstance(child, ttk.Label) and "Caméra" in child.cget("text"):
                    child.config(text=f"🎥 Caméra {i + 1} ({cam_letter}) :")
                    break

    # ---------------------------------------------------------
    # Gestion Dynamique des Sources Audio (Zoom F8, Sound Devices)
    # ---------------------------------------------------------
    def _add_audio_row(self):
        idx = len(self.audio_rows)
        row = ttk.Frame(self.audios_container)
        row.pack(fill="x", pady=2)

        label_text = "🎙️ Son Master (F8) :" if idx == 0 else f"🎙️ Source Son {idx + 1} :"
        lbl = ttk.Label(row, text=label_text, font=("TkDefaultFont", 9, "bold"), width=20, anchor="w")
        lbl.pack(side="left")

        var_path = tk.StringVar()
        entry = ttk.Entry(row, textvariable=var_path)
        entry.pack(side="left", fill="x", expand=True, padx=4)

        lbl_count = ttk.Label(row, text="0 audio", foreground="gray", width=12, anchor="e")

        btn_dir = ttk.Button(row, text="📂 Dossier...", command=lambda v=var_path: self._browse_dir_for(v))
        btn_dir.pack(side="left", padx=2)

        btn_file = ttk.Button(row, text="📄 Fichier...", command=lambda v=var_path: self._browse_file_for(v, AUDIO_EXTS))
        btn_file.pack(side="left", padx=2)

        lbl_count.pack(side="left", padx=4)

        aud_data = {
            "index": idx + 1,
            "label": f"Audio-{idx + 1}",
            "var_path": var_path,
            "row_frame": row,
            "lbl_count": lbl_count
        }

        if idx == 0:
            btn_add = ttk.Button(row, text="➕ Ajouter Son", command=self._add_audio_row)
            btn_add.pack(side="left", padx=3)
            aud_data["btn_action"] = btn_add
        else:
            btn_del = ttk.Button(row, text="➖ Retirer", command=lambda ad=aud_data: self._remove_audio_row(ad))
            btn_del.pack(side="left", padx=3)
            aud_data["btn_action"] = btn_del

        if HAS_DND:
            entry.drop_target_register(DND_FILES)
            entry.dnd_bind('<<Drop>>', lambda e, v=var_path: self._on_generic_drop(e, v))

        var_path.trace_add("write", lambda *args: self._update_sync_counts())
        self.audio_rows.append(aud_data)

    def _remove_audio_row(self, aud_data):
        if aud_data in self.audio_rows:
            aud_data["row_frame"].destroy()
            self.audio_rows.remove(aud_data)
            self._update_sync_counts()

    # ---------------------------------------------------------
    # Sélection de Dossiers ou Fichiers & Drag & Drop
    # ---------------------------------------------------------
    def _browse_dir_for(self, str_var):
        d = filedialog.askdirectory(title="Sélectionner un dossier")
        if d:
            str_var.set(d)

    def _browse_file_for(self, str_var, exts):
        filetypes = [("Médias compatibles", "*" + ";*".join(exts)), ("Tous les fichiers", "*.*")]
        f = filedialog.askopenfilename(title="Sélectionner un fichier média", filetypes=filetypes)
        if f:
            str_var.set(f)

    def _on_generic_drop(self, event, str_var):
        p = event.data.strip()
        if p.startswith('{') and p.endswith('}'):
            p = p[1:-1]
        if os.path.exists(p):
            str_var.set(p)

    def _update_sync_counts(self):
        # Mettre à jour les compteurs pour chaque caméra
        for c in self.cam_rows:
            path_val = c["var_path"].get().strip()
            if path_val and os.path.exists(path_val):
                res = resolve_media_inputs([path_val], VIDEO_EXTS, default_label_prefix="Cam")
                n = len(res)
                c["lbl_count"].config(text=f"{n} vidéo(s)", foreground="#a6e3a1" if n else "gray")
            else:
                c["lbl_count"].config(text="0 vidéo", foreground="gray")

        # Mettre à jour les compteurs pour chaque source audio
        for a in self.audio_rows:
            path_val = a["var_path"].get().strip()
            if path_val and os.path.exists(path_val):
                res = resolve_media_inputs([path_val], AUDIO_EXTS, default_label_prefix="Audio")
                n = len(res)
                a["lbl_count"].config(text=f"{n} audio(s)", foreground="#a6e3a1" if n else "gray")
            else:
                a["lbl_count"].config(text="0 audio", foreground="gray")

    # ---------------------------------------------------------
    # QuickLook & Commandes contextuelles
    # ---------------------------------------------------------
    def _ql_sync_video(self, _e=None):
        sel = self.tv_sync.selection()
        if not sel:
            return
        idx = int(sel[0])
        if 0 <= idx < len(self.sync_results):
            p = self.sync_results[idx]["video_path"]
            if os.path.exists(p):
                subprocess.Popen(["qlmanage", "-p", p])

    def _play_sync_audio(self):
        sel = self.tv_sync.selection()
        if not sel:
            return
        idx = int(sel[0])
        if 0 <= idx < len(self.sync_results):
            ap = self.sync_results[idx]["audio_path"]
            if os.path.exists(ap):
                subprocess.Popen(["afplay", ap])

    def _reveal_sync_v(self):
        sel = self.tv_sync.selection()
        if not sel:
            return
        idx = int(sel[0])
        if 0 <= idx < len(self.sync_results):
            p = self.sync_results[idx]["video_path"]
            if os.path.exists(p):
                subprocess.Popen(["open", "-R", p])

    def _reveal_sync_a(self):
        sel = self.tv_sync.selection()
        if not sel:
            return
        idx = int(sel[0])
        if 0 <= idx < len(self.sync_results):
            p = self.sync_results[idx]["audio_path"]
            if os.path.exists(p):
                subprocess.Popen(["open", "-R", p])

    def _popup_sync_menu(self, event):
        iid = self.tv_sync.identify_row(event.y)
        if iid:
            self.tv_sync.selection_set(iid)
            self.menu_sync.post(event.x_root, event.y_root)

    # ---------------------------------------------------------
    # Exécution de la Synchronisation
    # ---------------------------------------------------------
    def _do_auto_sync(self):
        cam_sources = []
        for c in self.cam_rows:
            p = c["var_path"].get().strip()
            if p and os.path.exists(p):
                cam_sources.append({"path": p, "label": c["label"]})

        audio_sources = []
        for a in self.audio_rows:
            p = a["var_path"].get().strip()
            if p and os.path.exists(p):
                audio_sources.append(p)

        if not cam_sources:
            messagebox.showinfo("Sources Caméras", "Veuillez sélectionner au moins un dossier ou fichier vidéo pour la Caméra 1.")
            return

        if not audio_sources:
            # Fallback Multi-Caméras pur entre caméras
            audio_sources = [cam_sources[0]["path"]]

        m_str = self.var_sync_method.get()
        if "Clap" in m_str:
            tech = "clap"
        elif "Timecode" in m_str:
            tech = "timecode"
        elif "Hybride" in m_str:
            tech = "auto"
        else:
            tech = "waveform"

        self.btn_start_sync.config(state="disabled", text="Synchronisation en cours...")
        self._set_status("Analyse et synchronisation audio/vidéo (Multi-Cam & Zoom F8) en cours...")
        self.pb_sync.config(value=0)
        self.tv_sync.delete(*self.tv_sync.get_children())
        self.sync_results = []

        def worker():
            try:
                def progress(cur, tot, name):
                    pct = int((cur / max(tot, 1)) * 100)
                    self.after(0, lambda: [
                        self.pb_sync.config(value=pct),
                        self._set_status(f"Synchro ({cur}/{tot}) : {name}")
                    ])

                res = pair_and_sync(cam_sources, audio_sources, method=tech, progress_cb=progress)
                self.sync_results = res

                def update_ui():
                    self.tv_sync.delete(*self.tv_sync.get_children())
                    good = 0
                    seen_mc = set()
                    f8_detected = False

                    for i, r in enumerate(self.sync_results):
                        sign = "+" if r["offset_sec"] >= 0 else ""
                        off_s = f"{sign}{r['offset_sec']:.3f} s"
                        off_f = f"{sign}{r['offset_frames']} img"
                        conf_s = f"{r['confidence']}%"
                        st = "🟢 Synchro" if r["confidence"] >= 60 else "⚠️ Vérifier"
                        if r["confidence"] >= 60:
                            good += 1

                        cam_tr = r.get("cam_track", 1)
                        mc_angles = r.get("multicam_angles", 1)
                        cam_lbl = r.get("cam_label", f"Cam {cam_tr}")
                        ch_cnt = r.get("audio_channels", 2)
                        extra_m = len(r.get("extra_mono_tracks", []))
                        tot_ch = max(ch_cnt, 1 + extra_m)

                        if tot_ch > 2:
                            f8_detected = True

                        if cam_tr == 1:
                            if self.var_split_tracks.get() and tot_ch > 1:
                                track_str = f"🎥 V1 ({cam_lbl}) 🔗 A1-A{tot_ch} ({tot_ch} Micros F8)"
                            else:
                                track_str = f"🎥 V1 ({cam_lbl}) 🔗 A1"
                        else:
                            track_str = f"🎥 V{cam_tr} ({cam_lbl}) 🔗 A{tot_ch + cam_tr - 1} [Son Cam]"

                        seen_mc.add(r["audio_path"])

                        self.tv_sync.insert("", "end", iid=str(i), values=(
                            r["video_name"],
                            r["audio_name"],
                            track_str,
                            r["method"],
                            off_s,
                            off_f,
                            conf_s,
                            st
                        ))

                    multicam_groups = len(seen_mc)
                    tot = len(self.sync_results)
                    if tot > 0:
                        mc_info = f" | 🎥 {multicam_groups} prise(s) Multi-Cam" if multicam_groups else ""
                        f8_info = " | 🎚️ Micros Zoom F8 séparés sur pistes A1, A2, A3..." if f8_detected else ""
                        self.lbl_sync_report.config(
                            text=f"🎉 {tot} rushes traités | {good}/{tot} synchronisés{mc_info}{f8_info}. Prêt pour export XML Premiere 2026 !",
                            foreground="#a6e3a1"
                        )
                        messagebox.showinfo(
                            "Synchronisation Terminée",
                            f"🎉 {tot} rush(es) analysé(s) et synchronisé(s) !\n\n"
                            f"• Précision acoustique : {good}/{tot} synchronisés à l'image près\n"
                            f"• Prises Multi-Caméras (V1, V2, V3...) : {multicam_groups}\n"
                            f"• Séparation des micros Zoom F8 : {'Activée (A1, A2, A3...)' if self.var_split_tracks.get() else 'Désactivée'}\n\n"
                            "Cliquez sur 'Exporter Timeline Synchronisée (XML NLE)' "
                            "pour importer la séquence directement dans Adobe Premiere Pro 2026, DaVinci Resolve ou Final Cut Pro."
                        )
                    else:
                        self.lbl_sync_report.config(
                            text="Aucun rush correspondant trouvé entre les sources vidéo et audio.",
                            foreground="#f38ba8"
                        )

                self.after(0, update_ui)
            except Exception as e:
                self.after(0, lambda messagebox_err=str(e): messagebox.showerror("Erreur Synchro", f"Erreur lors de la synchronisation : {messagebox_err}"))
            finally:
                self.after(0, lambda: [
                    self.btn_start_sync.config(state="normal", text="⚡ Lancer la Synchronisation"),
                    self._set_status("Prêt.")
                ])

        threading.Thread(target=worker, daemon=True).start()

    # ---------------------------------------------------------
    # Export Timeline XML (Premiere Pro 2026 / DaVinci Resolve)
    # ---------------------------------------------------------
    def _export_synced_xml(self):
        if not self.sync_results:
            messagebox.showinfo("Export XML", "Aucun rush synchronisé à exporter. Lancez d'abord la synchronisation.")
            return

        out_file = filedialog.asksaveasfilename(
            title="Enregistrer la Timeline Synchronisée XML (Premiere 2026 / Resolve / FCP)",
            defaultextension=".xml",
            initialfile="Rushes_MultiCam_Synchronises.xml",
            filetypes=[("FCP 7 / Premiere 2026 / Resolve XML", "*.xml"), ("Tous les fichiers", "*.*")]
        )
        if not out_file:
            return

        try:
            is_mc = self.var_multicam.get() if hasattr(self, "var_multicam") else True
            split_tr = self.var_split_tracks.get() if hasattr(self, "var_split_tracks") else True

            generate_synced_xml(
                self.sync_results,
                out_file,
                project_name="Tournage Multi-Cam Synchronisé",
                multicam=is_mc,
                split_audio_tracks=split_tr
            )

            messagebox.showinfo(
                "Exportation Réussie",
                f"🎉 Le fichier XML Multi-Cam & Multipistes a été généré avec succès :\n{os.path.basename(out_file)}\n\n"
                "👉 Compatible directement avec :\n"
                "• Adobe Premiere Pro 2026 (Fichier > Importer)\n"
                "• DaVinci Resolve (Fichier > Importer > Timeline XML)\n"
                "• Final Cut Pro\n\n"
                "🔗 Fonctionnalités actives dans la Timeline :\n"
                "• Caméras empilées : Caméra 1 sur V1, Caméra 2 sur V2, Caméra 3 sur V3...\n"
                "• Micros Zoom F8 séparés : Chaque micro est sur sa propre piste A1, A2, A3, A4...\n"
                "• Liaison Audio/Vidéo : Tous les micros Zoom F8 sont liés (<link>) à Caméra 1 !"
            )
        except Exception as e:
            messagebox.showerror("Erreur Export", f"Échec de l'exportation XML : {e}")

    def refresh(self):
        """Rafraîchit les compteurs de fichiers."""
        self._update_sync_counts()
