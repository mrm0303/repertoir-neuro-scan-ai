import os
import gzip
import re
import sqlite3
import xml.etree.ElementTree as ET
from urllib.parse import unquote, urlparse
from catalogue_app.utils import human_size, human_count

def extract_project_media_references(project_path):
    """
    Extrait la liste des noms de fichiers médias référencés dans un projet (Premiere, FCPXML, etc.)
    """
    media_filenames = set()
    if not os.path.exists(project_path):
        return []

    ext = os.path.splitext(project_path)[1].lower()

    # 1. Adobe Premiere Pro (.prproj) -> Fichier XML compressé en GZIP
    if ext == ".prproj":
        try:
            with gzip.open(project_path, 'rb') as f:
                content = f.read()
            # Chercher les chemins et noms de fichiers
            paths = re.findall(r'<ActualMediaFilePath>([^<]+)</ActualMediaFilePath>', content.decode('utf-8', errors='ignore'))
            for p in paths:
                fname = os.path.basename(p.replace('\\', '/'))
                if fname:
                    media_filenames.add(fname)
        except Exception:
            pass

    # 2. Final Cut Pro / Premiere XML (.xml, .fcpxml)
    elif ext in (".xml", ".fcpxml"):
        try:
            with open(project_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            # Chercher pathurl ou src
            urls = re.findall(r'<pathurl>([^<]+)</pathurl>', content) + re.findall(r'src="([^"]+)"', content)
            for u in urls:
                parsed = unquote(urlparse(u).path)
                fname = os.path.basename(parsed)
                if fname:
                    media_filenames.add(fname)
        except Exception:
            pass

    return list(media_filenames)

def locate_project_media(con, project_name, project_path="", online_volumes=None):
    """
    Recherche où se trouvent les médias d'un projet à travers l'ensemble des disques catalogués.
    Retourne un bilan détaillé : médias en ligne, médias hors ligne (disques à brancher), et statistiques.
    """
    if online_volumes is None:
        online_volumes = {}

    media_names = []
    if project_path and os.path.exists(project_path):
        media_names = extract_project_media_references(project_path)

    # Si pas d'extraction directe de fichiers, chercher les rushes associés au projet par nom de dossier / projet
    clean_proj_name = re.sub(r'[\._-](prproj|drp|fcpxml|fcpbundle|aep|veg)$', '', project_name, flags=re.I).strip()
    
    results_by_volume = {}
    total_found = 0
    total_size = 0
    missing_media = []

    if media_names:
        # Recherche exacte des noms de fichiers
        for fname in media_names:
            rows = con.execute("""
                SELECT f.id, f.name, f.rel_path, f.size, v.id as volume_id, v.name as volume_name, v.last_path
                FROM files f
                JOIN volumes v ON f.volume_id = v.id
                WHERE f.name = ?
                LIMIT 5
            """, (fname,)).fetchall()
            
            if rows:
                for r in rows:
                    vol_id = r["volume_id"]
                    vol_name = r["volume_name"]
                    is_online = vol_id in online_volumes
                    
                    if vol_name not in results_by_volume:
                        results_by_volume[vol_name] = {
                            "volume_name": vol_name,
                            "is_online": is_online,
                            "count": 0,
                            "size": 0,
                            "files": []
                        }
                    results_by_volume[vol_name]["count"] += 1
                    results_by_volume[vol_name]["size"] += (r["size"] or 0)
                    results_by_volume[vol_name]["files"].append(r["name"])
                    total_found += 1
                    total_size += (r["size"] or 0)
                    break
            else:
                missing_media.append(fname)
    else:
        # Recherche par affinité de dossier ou nom de projet
        rows = con.execute("""
            SELECT f.id, f.name, f.rel_path, f.size, v.id as volume_id, v.name as volume_name, v.last_path
            FROM files f
            JOIN volumes v ON f.volume_id = v.id
            WHERE (f.rel_path LIKE ? OR f.name LIKE ?)
            AND f.category IN ('video', 'audio', 'image')
            LIMIT 500
        """, (f"%{clean_proj_name}%", f"%{clean_proj_name}%")).fetchall()

        for r in rows:
            vol_id = r["volume_id"]
            vol_name = r["volume_name"]
            is_online = vol_id in online_volumes
            
            if vol_name not in results_by_volume:
                results_by_volume[vol_name] = {
                    "volume_name": vol_name,
                    "is_online": is_online,
                    "count": 0,
                    "size": 0,
                    "files": []
                }
            results_by_volume[vol_name]["count"] += 1
            results_by_volume[vol_name]["size"] += (r["size"] or 0)
            results_by_volume[vol_name]["files"].append(r["name"])
            total_found += 1
            total_size += (r["size"] or 0)

    # Création du rapport de localisation
    report = {
        "project": project_name,
        "total_media_found": total_found,
        "total_size_human": human_size(total_size),
        "missing_count": len(missing_media),
        "volumes_distribution": list(results_by_volume.values()),
        "drives_to_plug": [v["volume_name"] for v in results_by_volume.values() if not v["is_online"]]
    }
    
    return report
