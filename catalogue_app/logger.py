"""
Système de Journalisation Centralisé (Logging) pour Catalogue de Disques.
Écrit les logs dans ~/CatalogueDisques/logs/app.log avec rotation automatique.
"""

import os
import sys
import logging
from logging.handlers import RotatingFileHandler
from .config import APP_DIR

LOGS_DIR = os.path.join(APP_DIR, "logs")
os.makedirs(LOGS_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOGS_DIR, "app.log")

def setup_logger(name="catalogue_app"):
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    # Formatter avec date, niveau, module et message
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(module)s:%(lineno)d] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Handler fichier rotatif (10 Mo max, garde 5 sauvegardes)
    try:
        file_handler = RotatingFileHandler(
            LOG_FILE, maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8"
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.DEBUG)
        logger.addHandler(file_handler)
    except Exception as e:
        print(f"Avertissement : Impossible d'initialiser le fichier de log {LOG_FILE}: {e}")

    # Handler console (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)
    logger.addHandler(console_handler)

    return logger

log = setup_logger()
