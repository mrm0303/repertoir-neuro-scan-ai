#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Système de Mise à Jour Automatique (GitHub 1-Clic) pour Repertoir Neuro Scan.AI.
Permet aux utilisateurs sur Mac de récupérer les dernières corrections et nouveautés
depuis GitHub sans jamais toucher à leur base de données personnelle (~/CatalogueDisques/catalogue.db).
"""

import os
import sys
import subprocess
from catalogue_app.config import APP_VERSION, APP_DIR
from catalogue_app.settings_manager import load_settings, save_settings

DEFAULT_GITHUB_REPO = "https://github.com/mrm0303/repertoir-neuro-scan-ai.git"


def get_repo_root():
    """Retourne le dossier racine de l'application."""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_configured_repo_url():
    """Récupère l'URL du dépôt GitHub depuis git remote ou settings.json."""
    root = get_repo_root()
    try:
        res = subprocess.run(
            ["git", "-C", root, "remote", "get-url", "origin"],
            capture_output=True, text=True, timeout=5
        )
        if res.returncode == 0 and res.stdout.strip():
            return res.stdout.strip()
    except Exception:
        pass

    settings = load_settings()
    return settings.get("github_repo_url", DEFAULT_GITHUB_REPO).strip()


def set_configured_repo_url(url):
    """Enregistre l'URL du dépôt GitHub dans settings.json et configure git remote origin."""
    url = (url or "").strip()
    settings = load_settings()
    settings["github_repo_url"] = url
    save_settings(settings)

    if not url:
        return True, "URL GitHub effacée."

    root = get_repo_root()
    try:
        if not os.path.isdir(os.path.join(root, ".git")):
            subprocess.run(["git", "-C", root, "init"], check=False, capture_output=True, timeout=10)
        res = subprocess.run(["git", "-C", root, "remote", "get-url", "origin"], capture_output=True, text=True)
        if res.returncode == 0:
            subprocess.run(["git", "-C", root, "remote", "set-url", "origin", url], check=True, capture_output=True, timeout=10)
        else:
            subprocess.run(["git", "-C", root, "remote", "add", "origin", url], check=True, capture_output=True, timeout=10)
        return True, f"Dépôt GitHub configuré : {url}"
    except Exception as e:
        return False, f"Erreur lors de la configuration Git : {e}"


def get_current_version_info():
    """Retourne un dictionnaire décrivant la version actuelle et le commit Git."""
    root = get_repo_root()
    commit = "local"
    date_str = ""
    branch = "main"
    try:
        r_hash = subprocess.run(["git", "-C", root, "rev-parse", "--short", "HEAD"], capture_output=True, text=True, timeout=5)
        if r_hash.returncode == 0 and r_hash.stdout.strip():
            commit = r_hash.stdout.strip()
        r_date = subprocess.run(["git", "-C", root, "log", "-1", "--format=%cd", "--date=short"], capture_output=True, text=True, timeout=5)
        if r_date.returncode == 0 and r_date.stdout.strip():
            date_str = r_date.stdout.strip()
        r_branch = subprocess.run(["git", "-C", root, "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True, timeout=5)
        if r_branch.returncode == 0 and r_branch.stdout.strip() and r_branch.stdout.strip() != "HEAD":
            branch = r_branch.stdout.strip()
    except Exception:
        pass

    return {
        "version": APP_VERSION,
        "commit": commit,
        "date": date_str,
        "branch": branch,
        "repo_url": get_configured_repo_url(),
    }


def _has_head(root):
    """Vrai si le dossier possède déjà un commit Git local (HEAD valide)."""
    try:
        res = subprocess.run(
            ["git", "-C", root, "rev-parse", "--verify", "-q", "HEAD"],
            capture_output=True, text=True, timeout=5
        )
        return res.returncode == 0
    except Exception:
        return False


def git_available():
    """Vérifie que Git est utilisable (sur Mac : Outils de ligne de commande Apple)."""
    import shutil
    if not shutil.which("git"):
        return False
    try:
        res = subprocess.run(["git", "--version"], capture_output=True, text=True, timeout=10)
        return res.returncode == 0
    except Exception:
        return False


def _detect_remote_branch(root, preferred_branch="main"):
    """Détecte la branche distante disponible sur origin (main ou master)."""
    for b in (preferred_branch, "main", "master"):
        res = subprocess.run(
            ["git", "-C", root, "rev-parse", "--verify", f"origin/{b}"],
            capture_output=True, text=True, timeout=5
        )
        if res.returncode == 0:
            return b
    return preferred_branch


def check_for_updates():
    """
    Vérifie sur GitHub si des mises à jour sont disponibles.
    Retourne un dict :
      {
        "status": "up_to_date" | "update_available" | "no_repo" | "error",
        "behind_count": int,
        "changelog": str,
        "message": str,
        "branch": str
      }
    """
    root = get_repo_root()
    repo_url = get_configured_repo_url()
    if not repo_url:
        return {
            "status": "no_repo",
            "behind_count": 0,
            "changelog": "",
            "message": "Aucun dépôt GitHub n'est encore configuré. Renseignez l'URL GitHub dans Paramètres > Mises à jour.",
            "branch": "main",
        }

    if not git_available():
        if sys.platform == "darwin":
            try:
                subprocess.Popen(["xcode-select", "--install"])
            except Exception:
                pass
        return {
            "status": "error",
            "behind_count": 0,
            "changelog": "",
            "message": ("Les mises à jour nécessitent les « Outils de ligne de commande » d'Apple.\n\n"
                        "Une fenêtre macOS propose de les installer : cliquez sur « Installer », "
                        "puis relancez la vérification des mises à jour."),
            "branch": "main",
        }

    # S'assurer que le remote origin est configuré
    set_configured_repo_url(repo_url)

    try:
        fetch_res = subprocess.run(
            ["git", "-C", root, "fetch", "origin", "--prune"],
            capture_output=True, text=True, timeout=20
        )
        if fetch_res.returncode != 0:
            err = (fetch_res.stderr or fetch_res.stdout or "Impossible de joindre GitHub").strip()
            return {
                "status": "error",
                "behind_count": 0,
                "changelog": "",
                "message": f"Impossible de vérifier les mises à jour sur GitHub :\n{err}",
                "branch": "main",
            }

        info = get_current_version_info()
        branch = _detect_remote_branch(root, info.get("branch", "main"))

        # Installation depuis un ZIP (pas encore d'historique Git local) :
        # on propose d'aligner l'installation sur la dernière version GitHub.
        if not _has_head(root):
            log_res = subprocess.run(
                ["git", "-C", root, "log", f"origin/{branch}", "--oneline", "-n", "8"],
                capture_output=True, text=True, timeout=5
            )
            return {
                "status": "update_available",
                "behind_count": 1,
                "changelog": (log_res.stdout or "").strip(),
                "message": "🎉 Première connexion à GitHub : la dernière version peut être installée.",
                "branch": branch,
            }

        cnt_res = subprocess.run(
            ["git", "-C", root, "rev-list", f"HEAD..origin/{branch}", "--count"],
            capture_output=True, text=True, timeout=5
        )
        behind = int(cnt_res.stdout.strip()) if (cnt_res.returncode == 0 and cnt_res.stdout.strip().isdigit()) else 0

        if behind <= 0:
            return {
                "status": "up_to_date",
                "behind_count": 0,
                "changelog": "",
                "message": f"Votre application est à jour (V{APP_VERSION} — commit {info['commit']}).",
                "branch": branch,
            }

        log_res = subprocess.run(
            ["git", "-C", root, "log", f"HEAD..origin/{branch}", "--oneline", "-n", "12"],
            capture_output=True, text=True, timeout=5
        )
        changelog = (log_res.stdout or "").strip()
        return {
            "status": "update_available",
            "behind_count": behind,
            "changelog": changelog,
            "message": f"🎉 {behind} nouvelle(s) mise(s) à jour disponible(s) sur GitHub !",
            "branch": branch,
        }
    except Exception as e:
        return {
            "status": "error",
            "behind_count": 0,
            "changelog": "",
            "message": f"Erreur lors de la vérification : {e}",
            "branch": "main",
        }


def apply_update(progress_cb=None):
    """
    Télécharge et applique la dernière mise à jour depuis GitHub.
    Ne touche JAMAIS à ~/CatalogueDisques/catalogue.db (la base de données personnelle de l'utilisateur).
    Retourne (success: bool, message: str).
    """
    root = get_repo_root()
    repo_url = get_configured_repo_url()
    if not repo_url:
        return False, "Aucun dépôt GitHub configuré."

    def _notify(msg):
        if progress_cb:
            try:
                progress_cb(msg)
            except Exception:
                pass

    try:
        _notify("Connexion à GitHub (git fetch)...")
        fetch_res = subprocess.run(
            ["git", "-C", root, "fetch", "origin"],
            capture_output=True, text=True, timeout=30
        )
        if fetch_res.returncode != 0:
            return False, f"Échec de connexion à GitHub :\n{(fetch_res.stderr or fetch_res.stdout).strip()}"

        info = get_current_version_info()
        branch = _detect_remote_branch(root, info.get("branch", "main"))

        _notify("Téléchargement et application des nouveaux fichiers...")
        if not _has_head(root):
            # Installation issue d'un ZIP : aucun travail local à préserver,
            # on aligne les fichiers du programme sur GitHub (la base de données
            # vit dans ~/CatalogueDisques et n'est pas concernée).
            res = subprocess.run(
                ["git", "-C", root, "checkout", "-f", "-B", branch, f"origin/{branch}"],
                capture_output=True, text=True, timeout=60
            )
            if res.returncode != 0:
                return False, f"Erreur lors de la mise à jour Git :\n{(res.stderr or res.stdout).strip()}"
        else:
            # Protection : ne jamais écraser du code modifié localement (machine de développement).
            dirty = subprocess.run(
                ["git", "-C", root, "status", "--porcelain", "--untracked-files=no"],
                capture_output=True, text=True, timeout=10
            ).stdout.strip()
            ahead = subprocess.run(
                ["git", "-C", root, "rev-list", f"origin/{branch}..HEAD", "--count"],
                capture_output=True, text=True, timeout=5
            ).stdout.strip()
            if dirty or (ahead.isdigit() and int(ahead) > 0):
                return False, (
                    "Des modifications locales du programme ont été détectées sur ce Mac.\n\n"
                    "Par sécurité, la mise à jour automatique ne les écrase pas.\n"
                    "(Sur le Mac de développement, utilisez « Publier_Mise_A_Jour_GitHub.command ».)"
                )
            res = subprocess.run(
                ["git", "-C", root, "merge", "--ff-only", f"origin/{branch}"],
                capture_output=True, text=True, timeout=60
            )
            if res.returncode != 0:
                return False, f"Erreur lors de la mise à jour Git :\n{(res.stderr or res.stdout).strip()}"

        # Mise à jour des dépendances Python si requirements.txt est présent
        req_file = os.path.join(root, "requirements.txt")
        if os.path.exists(req_file):
            _notify("Vérification des composants Python (requirements.txt)...")
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "-q", "-r", req_file],
                capture_output=True, text=True, timeout=120
            )

        new_info = get_current_version_info()
        return True, (
            f"✅ Mise à jour installée avec succès (V{new_info['version']} — commit {new_info['commit']}) !\n\n"
            f"🔒 Votre base de données personnelle ({APP_DIR}/catalogue.db) est intacte.\n\n"
            f"Voulez-vous redémarrer l'application maintenant pour appliquer les nouveautés ?"
        )
    except Exception as e:
        return False, f"Erreur lors de l'installation de la mise à jour : {e}"


def restart_application():
    """Relance proprement l'application après une mise à jour."""
    root = get_repo_root()
    entry_script = os.path.join(root, "catalogue_disques_v3.py")
    # Libérer le fichier lock avant de relancer
    lock_path = os.path.join(APP_DIR, ".catalogue.lock")
    try:
        if os.path.exists(lock_path):
            os.remove(lock_path)
    except Exception:
        pass
    subprocess.Popen([sys.executable, entry_script], cwd=root)
    os._exit(0)
