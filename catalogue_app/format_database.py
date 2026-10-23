"""
Base de données encyclopédique des Formats de Fichiers & Spécifications.
Inspiré et alimenté par les standards professionnels et FileFormat.Info.
Fournit la détection, la description détaillée et la fiche technique de chaque extension.
"""

import os
import json

_DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "formats.json")

try:
    with open(_DATA_PATH, "r", encoding="utf-8") as _f:
        _DATA = json.load(_f)
        FORMAT_CATALOG = _DATA.get("format_catalog", {})
        GIST_FORMATS = _DATA.get("gist_formats", {})
        BOX_REPRESENTATIONS = _DATA.get("box_representations", {})
except Exception as _exc:
    FORMAT_CATALOG = {}
    GIST_FORMATS = {}
    BOX_REPRESENTATIONS = {}

def get_format_info(filename_or_ext: str):
    ext = filename_or_ext.lower().strip()
    if "." in ext:
        ext = ext.rsplit(".", 1)[-1]

    caps = BOX_REPRESENTATIONS.get(ext, {})
    has_pdf = caps.get("pdf", False)
    has_thumb = caps.get("thumbnail", ext in (
        "jpg", "jpeg", "png", "mov", "mp4", "mxf", "braw", "r3d", "heic", "webp",
        "gif", "tif", "tiff", "psd", "ai", "svg", "eps", "bmp"
    ))
    has_txt = caps.get("text", ext in (
        "txt", "md", "csv", "xml", "json", "py", "sh", "sql", "html", "css", "js",
        "vtt", "srt", "yaml", "yml", "ini", "log", "c", "cpp", "h", "java", "ts"
    ))

    # 1. Base Audiovisuelle & Cinéma Prioritaire
    if ext in FORMAT_CATALOG:
        data = FORMAT_CATALOG[ext].copy()
        data["extension"] = f".{ext}"
        data["supports_pdf"] = has_pdf
        data["supports_thumbnail"] = has_thumb
        data["supports_text"] = has_txt
        if ext in GIST_FORMATS:
            data["tools"] = GIST_FORMATS[ext].get("tools", "")
            data["use_case"] = GIST_FORMATS[ext].get("use_case", "")
        return data

    # 2. Base Encyclopédique Gist (Guide Interactif)
    if ext in GIST_FORMATS:
        g = GIST_FORMATS[ext]
        return {
            "extension": f".{ext}",
            "name": f"{g['description']}",
            "category": g["section"],
            "software": g.get("tools") or "Standard Informatique",
            "description": f"{g['description']}. Usage recommandé : {g.get('use_case', 'Général')}.",
            "tools": g.get("tools", ""),
            "use_case": g.get("use_case", ""),
            "supports_pdf": has_pdf,
            "supports_thumbnail": has_thumb,
            "supports_text": has_txt,
            "ffi_url": f"https://www.fileformat.info/format/{ext}/index.htm"
        }

    # 3. Base Box Representation
    if ext in BOX_REPRESENTATIONS:
        b = BOX_REPRESENTATIONS[ext]
        return {
            "extension": f".{ext}",
            "name": b["name"],
            "category": b["category"],
            "software": "Standard Industrie / Box API",
            "description": f"Format reconnu par les plateformes de gestion de médias. Supporte : {'vignette, ' if has_thumb else ''}{'indexation texte, ' if has_txt else ''}{'export PDF' if has_pdf else ''}.",
            "supports_pdf": has_pdf,
            "supports_thumbnail": has_thumb,
            "supports_text": has_txt,
            "ffi_url": f"https://www.fileformat.info/format/{ext}/index.htm"
        }

    # 4. Fallback générique
    return {
        "extension": f".{ext}",
        "name": f"Fichier {ext.upper()}",
        "category": "Inconnu / Générique",
        "software": "Système d'exploitation",
        "description": f"Format de fichier avec extension .{ext}. Consultez FileFormat.info pour plus de détails.",
        "supports_pdf": False,
        "supports_thumbnail": False,
        "supports_text": False,
        "ffi_url": f"https://www.fileformat.info/format/{ext}/index.htm"
    }
