#!/usr/bin/env python3
"""
Lanceur Principal de Catalogue de Disques V6.
Garantit l'instance unique (anti-collision) et initialise la journalisation.
"""

import os
import sys
from catalogue_app.config import APP_DIR
from catalogue_app.logger import log

def acquire_instance_lock():
    """Empêche le lancement de plusieurs instances simultanées pour protéger la base SQLite (Multiplateforme macOS, Windows, Linux)."""
    os.makedirs(APP_DIR, exist_ok=True)
    lock_path = os.path.join(APP_DIR, ".catalogue.lock")
    lock_fd = None

    try:
        if os.name == "nt":
            # Verrouillage Windows via msvcrt
            import msvcrt
            lock_fd = open(lock_path, "wb+")
            msvcrt.locking(lock_fd.fileno(), msvcrt.LK_NBLCK, 1)
            lock_fd.write(str(os.getpid()).encode())
            lock_fd.flush()
            return lock_fd
        else:
            # Verrouillage POSIX (macOS & Linux) via fcntl
            import fcntl
            lock_fd = open(lock_path, "w")
            fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            lock_fd.write(str(os.getpid()))
            lock_fd.flush()
            return lock_fd
    except (BlockingIOError, OSError, IOError):
        log.warning("Tentative de lancement d'une deuxième instance bloquée.")
        try:
            import tkinter as tk
            from tkinter import messagebox
            root = tk.Tk()
            root.withdraw()
            messagebox.showinfo(
                "Repertoir Neuro Scan.AI",
                "Une instance de l'application est déjà en cours d'exécution.\n\nVeuillez utiliser la fenêtre déjà ouverte."
            )
            root.destroy()
        except Exception:
            print("Une instance de Repertoir Neuro Scan.AI (RNS.AI) est déjà en cours d'exécution.")
        sys.exit(0)

if __name__ == "__main__":
    _lock = acquire_instance_lock()
    log.info("Démarrage de Repertoir Neuro Scan.AI (RNS.AI)...")
    import catalogue_app.main_window
    catalogue_app.main_window.main()
