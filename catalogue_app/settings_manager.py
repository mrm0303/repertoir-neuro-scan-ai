import os
import json
from .config import APP_DIR, VIDEO_EXT, IMAGE_EXT, AUDIO_EXT, PROJECT_EXT, DOC_EXT, ARCHIVE_EXT, LOGICIEL_EXT, EXT_3D, DEV_EXT, MEDIA_CATEGORIES

SETTINGS_FILE = os.path.join(APP_DIR, "settings.json")

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading settings: {e}")
    return {}

def save_settings(settings):
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=4)
    except Exception as e:
        print(f"Error saving settings: {e}")

def get_category_extensions():
    settings = load_settings()
    custom_cats = settings.get("categories", {})
    return {
        "projet": set(custom_cats.get("projet", PROJECT_EXT)),
        "video": set(custom_cats.get("video", VIDEO_EXT)),
        "image": set(custom_cats.get("image", IMAGE_EXT)),
        "audio": set(custom_cats.get("audio", AUDIO_EXT)),
        "document": set(custom_cats.get("document", DOC_EXT)),
        "archive": set(custom_cats.get("archive", ARCHIVE_EXT)),
        "logiciel": set(custom_cats.get("logiciel", LOGICIEL_EXT)),
        "3d": set(custom_cats.get("3d", EXT_3D)),
        "code": set(custom_cats.get("code", DEV_EXT))
    }

def get_global_categories():
    settings = load_settings()
    return settings.get("global_categories", ["B-Roll", "Interviews", "Vlogs", "Archives", "Rushes", "Masters"])

