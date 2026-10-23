#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Catalogue de disques — version 2
Inventaire hors ligne de vos rushes, projets et médias répartis sur de nombreux disques.

Nouveautés de la version 2
  - Chronomètre d'analyse : temps écoulé, temps restant estimé, vitesse, progression en %.
  - Analyse incrémentale : une ré-analyse ne recalcule que ce qui a changé (jusqu'à 20× plus rapide).
  - Plan de dédoublonnage : « je veux garder 2 copies maximum » → liste exacte des copies à retirer,
    récapitulée par disque.
  - Générateur d'étiquettes : chaque fichier reçoit automatiquement des mots-clés déduits de ses
    métadonnées (4K, Sony FX3, ProRes, 25p, ralenti, 2024, rushes, interview…), complétés par
    vos propres étiquettes manuelles.
  - Recherche insensible aux accents et aux variantes d'écriture de l'arabe.

Outils externes optionnels : exiftool (https://exiftool.org), ffprobe (FFmpeg).
"""

import csv
import json
import os
import queue
import re
import shutil
import sqlite3
import subprocess
import sys
import threading
import time
import unicodedata
from collections import defaultdict
from datetime import datetime

APP_NAME = "Repertoir Neuro Scan.AI"
APP_VERSION = "6.0"
APP_DIR = os.path.join(os.path.expanduser("~"), "CatalogueDisques")
DB_PATH = os.path.join(APP_DIR, "catalogue.db")
THUMBNAILS_DIR = os.path.join(APP_DIR, "thumbnails")
os.makedirs(THUMBNAILS_DIR, exist_ok=True)

FFPROBE_PATH = shutil.which("ffprobe")
FFPROBE = bool(FFPROBE_PATH)
FFMPEG_PATH = shutil.which("ffmpeg")
FFMPEG = bool(FFMPEG_PATH)
EXIFTOOL_PATH = shutil.which("exiftool")
EXIFTOOL = bool(EXIFTOOL_PATH)

# ---------------------------------------------------------------------------
# Classification des fichiers
# ---------------------------------------------------------------------------

# Extensions enrichies d'après FileFormat.Info, Box Representation API et les standards cinéma & broadcast
VIDEO_EXT = {
    "mp4", "mov", "mxf", "avi", "mkv", "m4v", "mts", "m2ts", "mpg", "mpeg",
    "wmv", "flv", "webm", "r3d", "braw", "ari", "dpx", "vob", "3gp", "3g2", "insv",
    "mod", "ts", "cine", "crm", "asf", "ogv", "m2v", "prores", "dnxhd", "dnxhr", "lrv", "qt", "swf"
}
IMAGE_EXT = {
    "jpg", "jpeg", "png", "tif", "tiff", "bmp", "gif", "webp", "heic", "heif",
    "psd", "psb", "ai", "eps", "svg", "exr", "hdr", "ico", "tga", "ppm", "pgm", "pbm",
    "pcx", "jp2", "j2k", "dng", "cr2", "cr3", "crw", "nef", "arw", "raf", "orf", "rw2", "pef", "srw", "x3f",
    "raw", "dcm", "dicm", "dicom", "svs", "ps"
}
AUDIO_EXT = {
    "wav", "mp3", "aif", "aiff", "aifc", "flac", "m4a", "aac", "ogg", "wma", "caf",
    "bwf", "opus", "mid", "midi", "alac", "dsd", "dsf", "dff", "ac3", "pcm", "mka", "amr", "au", "ra"
}
CAD_EXT = {"dwg", "dxf"}
EXT_3D = {"obj", "stl", "blend", "logicx", "band", "scriv", "c4d", "fbx", "dae", "3ds", "max", "ply", "mtl", "box3d", "usd", "usdz", "abc", "gltf", "glb"}
SPREADSHEET_EXT = {"xls", "xlsx", "xlsm", "csv", "tsv", "numbers", "ods", "gsheet"}
PRESENTATION_EXT = {"ppt", "pptx", "key", "odp", "otp", "gslide", "gslides"}

RAW_PHOTO_EXT = {"dng", "cr2", "cr3", "nef", "arw", "raf", "orf", "rw2", "pef", "srw", "x3f"}
RAW_VIDEO_EXT = {"r3d", "braw", "ari", "crm", "cine", "dpx"}

PROJECT_EXT = {
    "prproj": "Adobe Premiere Pro", "aep": "Adobe After Effects",
    "aepx": "Adobe After Effects", "aet": "Adobe After Effects (modèle)",
    "ppj": "Adobe Premiere (ancien)", "prel": "Adobe Premiere Elements",
    "aup": "Audacity", "sesx": "Adobe Audition", "indd": "Adobe InDesign",
    "drp": "DaVinci Resolve (projet)", "drb": "DaVinci Resolve (bibliothèque)",
    "drt": "DaVinci Resolve (timeline)", "dra": "DaVinci Resolve (archive)",
    "fcpxml": "Final Cut Pro / XML", "fcpbundle": "Final Cut Pro (bibliothèque)",
    "aaf": "Échange AAF (Avid)", "omf": "Échange OMF", "edl": "Liste de montage (EDL)",
    "otio": "OpenTimelineIO", "veg": "Vegas Pro", "kdenlive": "Kdenlive",
    "blend": "Blender", "logicx": "Logic Pro", "band": "GarageBand", "scriv": "Scrivener", "c4d": "Cinema 4D", "ale": "Avid Log Exchange",
}
DOC_EXT = {
    "pdf", "doc", "docx", "odt", "rtf", "txt", "md", "xls", "xlsx", "ods",
    "csv", "ppt", "pptx", "key", "pages", "numbers", "fdx", "celtx",
}
ARCHIVE_EXT = {"zip", "rar", "7z", "tar", "gz", "dmg", "iso", "sit"}
DISK_IMAGE_EXT = {"iso", "dmg", "img", "vhd", "vhdx", "vmdk", "toast", "bin", "cue", "qcow2", "cdr"}

SKIP_DIRS = {
    ".Trashes", ".Spotlight-V100", ".fseventsd", ".TemporaryItems",
    ".DocumentRevisions-V100", ".vol", ".apdisk", "System Volume Information",
    "$RECYCLE.BIN", "$Recycle.Bin", "RECYCLER", "found.000",
    "node_modules", ".git", ".svn", "__pycache__",
}
SKIP_FILES = {".DS_Store", "Thumbs.db", "desktop.ini", ".localized"}
MEDIA_CATEGORIES = {"video", "image", "audio"}

LOGICIEL_EXT = {"app", "exe", "dmg", "pkg", "deb", "rpm", "msi", "apk", "ipa", "plugin", "component", "vst", "vst3", "au", "aaxplugin"}
BUNDLE_EXT = {"app", "fcpbundle", "photoslibrary", "photolibrary", "lrdata", "xcodeproj", "rtfd", "logicx", "band", "plugin", "component", "vst", "vst3", "au", "aaxplugin", "kext"}
EXT_3D = {"obj", "stl", "blend", "logicx", "band", "scriv", "c4d", "fbx", "dae", "3ds", "max"}
DEV_EXT = {"py", "js", "html", "css", "cpp", "c", "h", "java", "json", "xml", "sql", "sh", "bat", "ps1"}

DUP_CATEGORIES = {
    "video": "🎬 Vidéo",
    "image": "📸 Image",
    "audio": "🎵 Audio",
    "disk_image": "💿 Images Disque (.iso, .dmg)",
    "logiciel": "💻 Logiciel (.app, .pkg...)",
    "archive": "📦 Archive (.zip, .rar...)",
    "document": "📄 Document (.pdf, .docx...)",
    "projet": "🎨 Projets (.prproj, .drp...)",
}

# Dossiers système à écarter par défaut. Analyser « / » ou « C:\ » sans cette liste
# fait entrer dans des zones qui gonflent artificiellement le total : sous macOS,
# /System/Volumes/Data est un miroir du disque entier, et /Volumes contient TOUS les
# disques externes branchés — d'où un disque de 500 Go qui en affiche 1,7 To.
SYSTEM_PREFIXES_POSIX = (
    "/system", "/private", "/usr", "/bin", "/sbin", "/cores", "/dev", "/net",
    "/proc", "/sys", "/run", "/boot", "/lib", "/lib64", "/snap", "/opt/homebrew",
    "/library/caches", "/network", 
    "/.vol", "/.fseventsd", "/.spotlight-v100", "/.mobilebackups",
    "/.documentrevisions-v100", "/.timemachine", 
)
SYSTEM_FIRST_PARTS_NT = {
    "windows", "program files", "program files (x86)", "programdata",
    "$recycle.bin", "system volume information", "recovery", "msocache",
    "perflogs", "$windows.~bt", "$windows.~ws", "onedrivetemp",
}


