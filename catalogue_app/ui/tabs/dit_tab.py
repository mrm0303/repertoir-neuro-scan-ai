import os
import sys
import subprocess
import threading
import json
import re as re_mod
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import tkinter.scrolledtext as st

# DND import, fallback gracefully
try:
    from tkinterdnd2 import DND_FILES
    HAS_DND = True
except ImportError:
    HAS_DND = False

from catalogue_app.ui.tabs.base_tab import BaseTab
from catalogue_app.config import APP_NAME
from catalogue_app.utils import check_directory_access, prompt_directory_access_fix
from catalogue_app import dit
from catalogue_app.dit import DITCopyJob

try:
    from catalogue_app.dit import ai_dit
except ImportError:
    ai_dit = None

try:
    from catalogue_app.agents.dit_agent import DITAgent
except ImportError:
    DITAgent = None


class DitTab(BaseTab):
    def _build_ui(self):
        f = self

        top = ttk.LabelFrame(f, text=" 📥 Transfert Vérifié de Rushes (DIT) ", padding=15)
        top.pack(fill="x", padx=10, pady=10)

        ttk.Label(top, text="Copiez vos rushes depuis une carte SD/SSD vers un disque de destination.\n"
                           "Chaque fichier est vérifié bit-à-bit par checksum pour garantir l'intégrité à 100%.",
                  foreground="#89b4fa", wraplength=700).grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 12))

        # Source
        ttk.Label(top, text="Source (carte/SSD) :").grid(row=1, column=0, sticky="w", pady=4)
        self.var_dit_src = tk.StringVar()
        ttk.Entry(top, textvariable=self.var_dit_src, width=50).grid(row=1, column=1, sticky="ew", padx=5)
        ttk.Button(top, text="Parcourir…", command=lambda: self.var_dit_src.set(
            filedialog.askdirectory(title="Sélectionnez le dossier source (carte SD, SSD…)") or self.var_dit_src.get()
        )).grid(row=1, column=2, padx=5)

        # Destination 1 (Principale)
        ttk.Label(top, text="Destination 1 (Principale) :").grid(row=2, column=0, sticky="w", pady=4)
        self.var_dit_dst = tk.StringVar()
        ttk.Entry(top, textvariable=self.var_dit_dst, width=50).grid(row=2, column=1, sticky="ew", padx=5)
        ttk.Button(top, text="Parcourir…", command=lambda: self.var_dit_dst.set(
            filedialog.askdirectory(title="Sélectionnez le disque de destination 1") or self.var_dit_dst.get()
        )).grid(row=2, column=2, padx=5)

        # Destination 2 (Miroir / Backup 3-2-1)
        ttk.Label(top, text="Destination 2 (Miroir / Optionnel) :").grid(row=3, column=0, sticky="w", pady=4)
        self.var_dit_dst2 = tk.StringVar()
        ttk.Entry(top, textvariable=self.var_dit_dst2, width=50).grid(row=3, column=1, sticky="ew", padx=5)
        ttk.Button(top, text="Parcourir…", command=lambda: self.var_dit_dst2.set(
            filedialog.askdirectory(title="Sélectionnez le disque de backup miroir (3-2-1)") or self.var_dit_dst2.get()
        )).grid(row=3, column=2, padx=5)

        top.grid_columnconfigure(1, weight=1)

        # Options
        opt = ttk.Frame(top)
        opt.grid(row=4, column=0, columnspan=3, sticky="w", pady=(10, 0))

        ttk.Label(opt, text="Algorithme :").pack(side="left")
        self.var_dit_algo = tk.StringVar(value="xxhash")
        ttk.Radiobutton(opt, text="xxHash (ultra-rapide)", variable=self.var_dit_algo, value="xxhash").pack(side="left", padx=5)
        ttk.Radiobutton(opt, text="MD5 (universel)", variable=self.var_dit_algo, value="md5").pack(side="left", padx=5)

        self.var_dit_mhl = tk.BooleanVar(value=True)
        ttk.Checkbutton(opt, text="Générer rapport ASC-MHL standard (.mhl)",
                        variable=self.var_dit_mhl).pack(side="left", padx=(15, 0))

        self.var_dit_autoscan = tk.BooleanVar(value=True)
        ttk.Checkbutton(opt, text="Scanner automatiquement après transfert",
                        variable=self.var_dit_autoscan).pack(side="left", padx=(15, 0))

        # Action buttons
        btn_frame = ttk.Frame(top)
        btn_frame.grid(row=5, column=0, columnspan=3, sticky="w", pady=(10, 0))

        self.btn_dit_start = ttk.Button(btn_frame, text="🚀 Lancer le Transfert Vérifié", command=self._start_dit_copy)
        self.btn_dit_start.pack(side="left", padx=(0, 10))
        self.btn_dit_stop = ttk.Button(btn_frame, text="⏹️ Arrêter", command=self._stop_dit_copy, state="disabled")
        self.btn_dit_stop.pack(side="left")

        # Agent DIT Frame
        ai_dit_frame = ttk.LabelFrame(f, text=" 🤖 Agent DIT & Contrôle d'Ingestion ", padding=8)
        ai_dit_frame.pack(fill="x", padx=10, pady=5)
        self.txt_dit_agent = tk.Text(ai_dit_frame, height=2, wrap="word", bg="#1e1e2e", fg="#89dceb", font=("TkDefaultFont", 11, "italic"))
        self.txt_dit_agent.pack(fill="x", expand=True, side="left", padx=(0, 10))
        self.txt_dit_agent.insert("1.0", "Sélectionnez une source et demandez conseil à l'Agent DIT (détection caméra, vérification d'espace, nomenclature).")
        self.txt_dit_agent.config(state="disabled")

        self.btn_dit_agent = ttk.Button(ai_dit_frame, text="🤖 Analyser la Carte", command=self._ask_dit_agent)
        self.btn_dit_agent.pack(side="right")

        # Progress
        prog_frame = ttk.LabelFrame(f, text=" Progression ", padding=10)
        prog_frame.pack(fill="x", padx=10, pady=5)

        self.lbl_dit_status = ttk.Label(prog_frame, text="En attente…")
        self.lbl_dit_status.pack(anchor="w")
        self.pb_dit = ttk.Progressbar(prog_frame, mode="determinate")
        self.pb_dit.pack(fill="x", pady=5)
        self.lbl_dit_file = ttk.Label(prog_frame, text="", foreground="#888")
        self.lbl_dit_file.pack(anchor="w")

        # Log
        log_frame = ttk.LabelFrame(f, text=" Journal de Transfert ", padding=10)
        log_frame.pack(fill="both", expand=True, padx=10, pady=(5, 10))

        self.txt_dit_log = st.ScrolledText(log_frame, height=8, wrap="word", state="disabled",
                                            font=("Menlo", 9), bg="#1e1e2e", fg="#cdd6f4")
        self.txt_dit_log.pack(fill="both", expand=True)

        self._dit_job = None

        if HAS_DND:
            try:
                f.drop_target_register(DND_FILES)
                f.dnd_bind('<<Drop>>', self._on_dit_drop)
            except Exception:
                pass

    def _ask_dit_agent(self):
        src = self.var_dit_src.get().strip()
        dst = self.var_dit_dst.get().strip()
        if not src or not os.path.exists(src):
            messagebox.showwarning(APP_NAME, "Sélectionnez d'abord un dossier source ou une carte SD valide.")
            return
        self.btn_dit_agent.config(text="Analyse...", state="disabled")
        self.update_idletasks()

        def worker():
            try:
                from catalogue_app.agents.dit_agent import DITAgent
                agent = DITAgent()
                resp = agent.analyze_source(src, dst)
                self.after(0, lambda r=resp: self._update_dit_txt(r))
            except Exception as e:
                err_msg = str(e)
                self.after(0, lambda err=err_msg: self._update_dit_txt(f"Erreur Agent DIT : {err}"))
            finally:
                self.after(0, lambda: self.btn_dit_agent.config(text="🤖 Analyser la Carte", state="normal"))

        threading.Thread(target=worker, daemon=True).start()

    def _update_dit_txt(self, t):
        match = re_mod.search(r'```action\s*(.*?)\s*```', t, re_mod.DOTALL)
        action_data = None
        if match:
            try:
                action_data = json.loads(match.group(1))
                t = t.replace(match.group(0), "\n[Action Détectée : Configuration DIT]")
            except Exception:
                pass

        self.txt_dit_agent.config(state="normal")
        self.txt_dit_agent.delete("1.0", "end")
        self.txt_dit_agent.insert("1.0", t)
        self.txt_dit_agent.config(state="disabled")

        if action_data and action_data.get("command") == "CONFIGURE_DIT":
            sub_folder = action_data.get("folder_name")
            algo = action_data.get("algo", "xxhash")
            prompt = f"L'agent DIT propose de configurer le transfert :\n\n"
            if sub_folder:
                prompt += f"• Créer le sous-dossier de destination : {sub_folder}\n"
            prompt += f"• Algorithme de vérification : {algo.upper()}\n\nAppliquer cette configuration ?"
            if messagebox.askyesno("Agent DIT", prompt):
                current_dst = self.var_dit_dst.get().strip()
                if current_dst and sub_folder:
                    self.var_dit_dst.set(os.path.join(current_dst, sub_folder))
                self.var_dit_algo.set(algo)

    def _dit_log(self, msg):
        self.txt_dit_log.config(state="normal")
        self.txt_dit_log.insert("end", msg + "\n")
        self.txt_dit_log.see("end")
        self.txt_dit_log.config(state="disabled")

    def _start_dit_copy(self):
        raw_src = self.var_dit_src.get().strip()
        dst1 = self.var_dit_dst.get().strip()
        dst2 = getattr(self, "var_dit_dst2", tk.StringVar()).get().strip()

        ok, resolved_src, err_kind, err_msg = check_directory_access(raw_src)
        if not ok:
            prompt_directory_access_fix(self, raw_src, err_kind, err_msg)
            return
        src = resolved_src
        if not dst1:
            messagebox.showwarning(APP_NAME, "Veuillez sélectionner au moins un dossier de destination principale.")
            return

        dest_dirs = [dst1]
        if dst2:
            dest_dirs.append(dst2)

        for d in dest_dirs:
            os.makedirs(d, exist_ok=True)

        self.btn_dit_start.config(state="disabled")
        self.btn_dit_stop.config(state="normal")
        self.pb_dit["value"] = 0
        self.txt_dit_log.config(state="normal")
        self.txt_dit_log.delete("1.0", "end")
        self.txt_dit_log.config(state="disabled")

        algo = self.var_dit_algo.get()
        mhl_opt = getattr(self, "var_dit_mhl", tk.BooleanVar(value=True)).get()

        self._dit_log(f"🚀 Début du transfert DIT ({'Miroir 3-2-1 double destination' if len(dest_dirs) > 1 else 'Destination simple'})")
        self._dit_log(f"   Source : {src}")
        for idx, d in enumerate(dest_dirs):
            self._dit_log(f"   Destination {idx+1} : {d}")
        self._dit_log(f"   Algorithme : {algo.upper()}")
        self._dit_log(f"   Manifeste ASC-MHL : {'Activé (.mhl)' if mhl_opt else 'Désactivé'}")
        self._dit_log("─" * 50)

        def on_progress(phase, current, total, filename, size):
            pct = int(current / total * 100) if total else 0
            icon = "📋" if "copy" in phase else "✅"
            label = "Copie" if "copy" in phase else "Vérification"
            self.after(0, lambda: self.pb_dit.configure(value=pct))
            self.after(0, lambda: self.lbl_dit_status.config(text=f"{label} {current}/{total} ({pct}%)"))
            self.after(0, lambda: self.lbl_dit_file.config(text=f"{icon} {filename}"))

        def on_finished(report):
            elapsed = report["elapsed"]
            mins = int(elapsed // 60)
            secs = int(elapsed % 60)

            self.after(0, lambda: self._dit_log("─" * 50))
            self.after(0, lambda: self._dit_log(f"✅ Transfert terminé en {mins}m {secs}s"))
            self.after(0, lambda: self._dit_log(f"   Fichiers copiés : {report['copied']}"))
            self.after(0, lambda: self._dit_log(f"   Vérifications OK : {report['verified']}"))

            if report.get("mhl_files"):
                self.after(0, lambda: self._dit_log(f"\n📜 Manifeste(s) MHL généré(s) :"))
                for mhl_p in report["mhl_files"]:
                    self.after(0, lambda p=mhl_p: self._dit_log(f"   • {p}"))

            if report["failed"]:
                self.after(0, lambda: self._dit_log(f"\n❌ ÉCHECS / ANOMALIES ({len(report['failed'])}) :"))
                for fname, reason in report["failed"]:
                    self.after(0, lambda f=fname, r=reason: self._dit_log(f"   • {f} — {r}"))
            else:
                self.after(0, lambda: self._dit_log("   🎉 Aucune erreur ! Intégrité parfaite et vérifiée."))

            self.after(0, lambda: self.pb_dit.configure(value=100))
            self.after(0, lambda: self.lbl_dit_status.config(text="Transfert terminé !"))
            self.after(0, lambda: self.btn_dit_start.config(state="normal"))
            self.after(0, lambda: self.btn_dit_stop.config(state="disabled"))

            # Auto-scan the primary destination into the catalogue
            if self.var_dit_autoscan.get() and report["copied"] > 0 and dest_dirs:
                self.after(500, lambda: self._auto_scan_dit(dest_dirs[0]))

        self._dit_job = DITCopyJob(src, dest_dirs, algorithm=algo,
                                    create_mhl=mhl_opt,
                                    progress_callback=on_progress,
                                    finished_callback=on_finished)
        self._dit_job.start()

    def _stop_dit_copy(self):
        if self._dit_job:
            self._dit_job.stop()
            self._dit_log("⏹️ Transfert interrompu par l'utilisateur.")
            self.btn_dit_start.config(state="normal")
            self.btn_dit_stop.config(state="disabled")

    def _auto_scan_dit(self, dest_path):
        self._dit_log(f"\n🔍 Scan automatique du disque : {dest_path}")
        if hasattr(self.app, "nb") and hasattr(self.app, "tab_stockage_main"):
            self.app.nb.select(self.app.tab_stockage_main)
        if hasattr(self.app, "nb_stockage") and hasattr(self.app, "tab_scan"):
            self.app.nb_stockage.select(self.app.tab_scan)
        # Pre-fill the scan path
        if hasattr(self.app, "var_path"):
            self.app.var_path.set(dest_path)
        elif hasattr(self, "var_path"):
            self.app.var_path.set(dest_path)
        self._dit_log("   → Allez dans l'onglet 'Disques Locaux' pour lancer le scan.")

    def _on_dit_drop(self, event):
        path = event.data
        if path.startswith('{') and path.endswith('}'):
            path = path[1:-1]
        if hasattr(self, "var_dit_src"):
            self.var_dit_src.set(path)
        if hasattr(self.app, "var_path"):
            self.app.var_path.set(path)
        self._dit_log(f"📁 Dossier sélectionné via glisser-déposer : {path}")

    def refresh(self):
        """Rafraîchissement de l'onglet si nécessaire."""
        pass
