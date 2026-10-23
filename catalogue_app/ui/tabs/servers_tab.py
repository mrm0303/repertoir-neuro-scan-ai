import threading
import tkinter as tk
from tkinter import ttk, messagebox
import urllib3

from catalogue_app.ui.tabs.base_tab import BaseTab
import catalogue_app.remote_servers as remote_servers
from catalogue_app.remote_servers import get_configured_servers
import catalogue_app.nas_backup as nb
from catalogue_app.nas_backup import backup_database_to_nas


class ServersTab(BaseTab):
    def _build_ui(self):
        f = self

        top = ttk.LabelFrame(f, text="Serveurs distants et NAS (API Directe)", padding=10)
        top.pack(fill="x", padx=10, pady=10)

        ttk.Label(
            top,
            text="L'application se connecte directement aux serveurs (sans montage SMB) pour lister et cataloguer leurs disques.",
            foreground="#89b4fa"
        ).pack(anchor="w", pady=(0, 10))

        cols = ("nom", "type", "host", "user")
        heads = ("Nom du Serveur", "Type", "Adresse (IP / Host)", "Utilisateur")
        self.tv_servers = ttk.Treeview(top, columns=cols, show="headings", height=3)
        for c, h in zip(cols, heads):
            self.tv_servers.heading(c, text=h)
            self.tv_servers.column(c, width=150, anchor="w")
        self.tv_servers.pack(fill="x")

        btn_frame = ttk.Frame(top)
        btn_frame.pack(fill="x", pady=(10, 0))
        ttk.Button(btn_frame, text="Ajouter un serveur...").pack(side="left")
        ttk.Button(btn_frame, text="Modifier").pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Supprimer").pack(side="left")

        mid = ttk.LabelFrame(f, text="Disques partagés du serveur sélectionné", padding=10)
        mid.pack(fill="both", expand=True, padx=10, pady=5)

        dcols = ("dossier", "type")
        dheads = ("Dossier Partagé / Disque", "Type")
        self.tv_shares = ttk.Treeview(mid, columns=dcols, show="headings")
        for c, h in zip(dcols, dheads):
            self.tv_shares.heading(c, text=h)
            self.tv_shares.column(c, width=200, anchor="w")
        self.tv_shares.pack(side="left", fill="both", expand=True)

        dsb = ttk.Scrollbar(mid, orient="vertical", command=self.tv_shares.yview)
        dsb.pack(side="right", fill="y")
        self.tv_shares.configure(yscrollcommand=dsb.set)

        bot = ttk.Frame(f)
        bot.pack(fill="x", padx=10, pady=10)
        ttk.Button(bot, text="Scanner ce disque distant...").pack(side="right")

        self.btn_nas_backup = ttk.Button(
            bot,
            text="☁️ Backup Sécurisé du Catalogue vers ce NAS",
            command=self._do_nas_backup
        )
        self.btn_nas_backup.pack(side="left")

        # Populate servers
        try:
            self.servers = get_configured_servers()
            for i, s in enumerate(self.servers):
                self.tv_servers.insert("", "end", iid=str(i), values=(s.name, s.server_type, s.host, s.user))
        except Exception:
            self.servers = []

        self.tv_servers.bind("<<TreeviewSelect>>", self._on_server_select)

    def _on_server_select(self, event=None):
        self.tv_shares.delete(*self.tv_shares.get_children())
        sel = self.tv_servers.selection()
        if not sel:
            return
        idx = int(sel[0])
        srv = self.servers[idx]

        self.tv_shares.insert("", "end", values=("Connexion en cours...", ""))
        self.update_idletasks()

        def worker():
            try:
                disks = srv.list_disks()
                self.after(0, lambda d=disks: self._populate_shares(d))
            except Exception as e:
                err_msg = str(e)
                self.after(0, lambda err=err_msg: self._populate_shares([{"name": f"Erreur: {err}", "type": "error"}]))

        threading.Thread(target=worker, daemon=True).start()

    def _populate_shares(self, disks):
        self.tv_shares.delete(*self.tv_shares.get_children())
        for d in disks:
            self.tv_shares.insert("", "end", values=(d["name"], d["type"]))

    def _do_nas_backup(self):
        sel = self.tv_servers.selection()
        if not sel:
            messagebox.showinfo("Serveur", "Veuillez d'abord sélectionner un serveur NAS dans la liste en haut.")
            return
        idx = int(sel[0])
        srv = self.servers[idx]

        if srv.server_type != "QNAP":
            messagebox.showerror(
                "Non supporté",
                "Le backup direct n'est actuellement supporté que sur les serveurs QNAP via leur API HTTP."
            )
            return

        if not messagebox.askyesno(
            "Backup NAS",
            f"Voulez-vous envoyer une sauvegarde chiffrée du catalogue vers {srv.name} ?\nCeci sécurise tout votre travail d'indexation."
        ):
            return

        if hasattr(self.app, "status"):
            self.app.status.set("Connexion au NAS et upload de la base de données...")
        elif hasattr(self, "status"):
            self.app.status.set("Connexion au NAS et upload de la base de données...")

        self.btn_nas_backup.config(state="disabled")

        def worker():
            try:
                # Note: We would ideally pass srv.host, srv.user, srv.password to this function,
                # but nas_backup currently uses global vars. We'll update the global vars before calling.
                nb.NAS_HOST = srv.host
                nb.NAS_USER = srv.user
                nb.NAS_PASS = srv.password

                urllib3.disable_warnings()  # Disable insecure request warnings for self-signed NAS certs

                success, msg = backup_database_to_nas()

                self.after(
                    0,
                    lambda m=msg, s=success: messagebox.showinfo("Backup NAS", m)
                    if s
                    else messagebox.showerror("Backup NAS", m)
                )
            except Exception as e:
                err_msg = str(e)
                self.after(0, lambda err=err_msg: messagebox.showerror("Erreur", f"Erreur critique lors de la sauvegarde : {err}"))
            finally:
                self.after(0, lambda: self.btn_nas_backup.config(state="normal"))
                if hasattr(self.app, "status"):
                    self.after(0, lambda: self.app.status.set("Prêt."))
                elif hasattr(self, "status"):
                    self.after(0, lambda: self.app.status.set("Prêt."))

        threading.Thread(target=worker, daemon=True).start()

    def refresh(self):
        """Rafraîchit la liste des serveurs distants."""
        try:
            self.servers = get_configured_servers()
            self.tv_servers.delete(*self.tv_servers.get_children())
            for i, s in enumerate(self.servers):
                self.tv_servers.insert("", "end", iid=str(i), values=(s.name, s.server_type, s.host, s.user))
        except Exception:
            self.servers = []
