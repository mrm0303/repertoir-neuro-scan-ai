import os
import re
import datetime
import unicodedata

# Extensions multimédias courantes pour la vidéo, photo, audio et sidecars
DEFAULT_MEDIA_EXTS = {
    ".mov", ".mp4", ".mxf", ".braw", ".r3d", ".crm", ".avi", ".mkv",
    ".arw", ".cr2", ".cr3", ".nef", ".dng", ".jpg", ".jpeg", ".png", ".tif", ".tiff",
    ".wav", ".mp3", ".aac", ".aif", ".aiff",
    ".xml", ".thm", ".lrv", ".xmp" # Sidecars
}

def sanitize_filename(name: str, keep_accents: bool = False) -> str:
    """Nettoie le nom de fichier pour une compatibilité totale montage/OS."""
    if not keep_accents:
        # Supprime les accents
        nfkd = unicodedata.normalize('NFKD', name)
        name = "".join([c for c in nfkd if not unicodedata.combining(c)])
    # Remplacement des espaces par des tirets bas
    name = re.sub(r'\s+', '_', name.strip())
    # Ne garde que les caractères alphanumériques, tirets et underscores
    name = re.sub(r'[^a-zA-Z0-9_\-\.]', '', name)
    return name

def extract_original_number(filename: str) -> str:
    """Extrait le dernier bloc de chiffres trouvé dans le nom sans extension."""
    stem, _ = os.path.splitext(filename)
    matches = re.findall(r'\d+', stem)
    if matches:
        return matches[-1]
    return ""

def scan_files_for_renaming(root_dir: str, recursive: bool = True, filter_media_only: bool = True):
    """
    Scanne un dossier et retourne la liste des fichiers à renommer,
    en conservant la hiérarchie relative.
    """
    if not os.path.isdir(root_dir):
        return []

    collected = []
    root_dir = os.path.abspath(root_dir)

    for current_root, dirs, files in os.walk(root_dir):
        # Ignorer les dossiers cachés
        dirs[:] = [d for d in dirs if not d.startswith('.')]

        for f in files:
            if f.startswith('.'):
                continue
            ext = os.path.splitext(f)[1].lower()
            if filter_media_only and ext not in DEFAULT_MEDIA_EXTS:
                continue

            full_path = os.path.join(current_root, f)
            rel_dir = os.path.relpath(current_root, root_dir)
            if rel_dir == ".":
                rel_dir = ""

            try:
                stat = os.stat(full_path)
                mtime = stat.st_mtime
                size = stat.st_size
            except OSError:
                mtime = 0
                size = 0

            collected.append({
                "filename": f,
                "full_path": full_path,
                "rel_dir": rel_dir,
                "ext": ext,
                "size": size,
                "mtime": mtime
            })

        if not recursive:
            break

    return collected

def preview_batch_rename(
    files: list,
    prefix: str,
    numbering_mode: str = "seq", # "seq", "orig", "keep"
    start_num: int = 1,
    padding: int = 3,
    sort_by: str = "date", # "date", "name"
    link_sidecars: bool = True,
    clean_nle: bool = True
):
    """
    Calcule la prévisualisation du renommage en respectant l'arborescence
    et la numérotation des rushes.
    """
    # 1. Trier les fichiers
    if sort_by == "date":
        sorted_files = sorted(files, key=lambda x: (x["mtime"], x["filename"].lower()))
    else:
        sorted_files = sorted(files, key=lambda x: (x["rel_dir"], x["filename"].lower()))

    # Groupement des sidecars par préfixe dans le même sous-dossier si activé
    # Ex: CLIP001.MOV et CLIP001.XML doivent partager le même numéro
    base_name_to_num = {}
    
    current_seq = start_num
    preview_list = []
    planned_destinations = set()

    for item in sorted_files:
        old_name = item["filename"]
        stem, orig_ext = os.path.splitext(old_name)
        rel_dir = item["rel_dir"]
        dir_key = os.path.join(rel_dir, stem)

        # Déterminer le numéro
        num_str = ""
        if numbering_mode == "orig":
            extracted = extract_original_number(old_name)
            if extracted:
                num_str = extracted.zfill(padding)
            else:
                num_str = str(current_seq).zfill(padding)
                current_seq += 1
        elif numbering_mode == "seq":
            if link_sidecars and dir_key in base_name_to_num:
                num_str = base_name_to_num[dir_key]
            else:
                num_str = str(current_seq).zfill(padding)
                if link_sidecars:
                    base_name_to_num[dir_key] = num_str
                current_seq += 1
        else: # "keep" (aucun numéro rajouté)
            num_str = ""

        # Construire le nouveau nom
        clean_prefix = sanitize_filename(prefix, keep_accents=not clean_nle) if prefix else ""
        
        parts = []
        if clean_prefix:
            parts.append(clean_prefix)
        if num_str:
            parts.append(num_str)

        if parts:
            new_stem = "_".join(parts)
            # Remplacement des doubles underscores
            new_stem = re.sub(r'_+', '_', new_stem).strip('_')
        else:
            new_stem = stem

        new_name = f"{new_stem}{orig_ext}"
        target_dir = os.path.dirname(item["full_path"])
        new_full_path = os.path.join(target_dir, new_name)

        # Vérifier le statut (inchangé, conflit, prêt)
        if old_name == new_name:
            status = "Inchangé"
        elif new_full_path in planned_destinations or (os.path.exists(new_full_path) and new_full_path != item["full_path"]):
            status = "⚠️ Conflit"
        else:
            status = "Prêt"

        planned_destinations.add(new_full_path)

        preview_list.append({
            "old_name": old_name,
            "new_name": new_name,
            "rel_dir": rel_dir if rel_dir else "(Racine)",
            "full_old_path": item["full_path"],
            "full_new_path": new_full_path,
            "size": item["size"],
            "mtime": item["mtime"],
            "status": status
        })

    return preview_list

def execute_batch_rename(preview_items: list, db_connection=None):
    """
    Exécute le renommage physique des fichiers sur le disque et met à jour
    la base de données du catalogue si les fichiers y sont référencés.
    Retourne (nb_succes, nb_erreurs, messages_erreurs).
    """
    success = 0
    errors = []

    # Vérifier d'abord s'il y a des conflits
    conflicts = [item for item in preview_items if item["status"] == "⚠️ Conflit"]
    if conflicts:
        return 0, len(conflicts), [f"Impossible de renommer : {len(conflicts)} conflits détectés."]

    items_to_rename = [item for item in preview_items if item["old_name"] != item["new_name"]]

    for item in items_to_rename:
        src = item["full_old_path"]
        dst = item["full_new_path"]

        if not os.path.exists(src):
            errors.append(f"Fichier source introuvable : {src}")
            continue

        try:
            os.rename(src, dst)
            success += 1

            # Mettre à jour la base de données SQLite si connectée
            if db_connection is not None:
                try:
                    old_basename = os.path.basename(src)
                    new_basename = os.path.basename(dst)
                    # Recherche du fichier par son ancien nom pour mettre à jour
                    row = db_connection.execute(
                        "SELECT id, rel_path FROM files WHERE name = ? ORDER BY id DESC LIMIT 1",
                        (old_basename,)
                    ).fetchone()

                    if row:
                        fid = row["id"]
                        old_rel = row["rel_path"]
                        new_rel = os.path.join(os.path.dirname(old_rel), new_basename)
                        if new_rel.startswith("./"):
                            new_rel = new_rel[2:]
                        name_lower = new_basename.lower()

                        db_connection.execute(
                            """UPDATE files 
                               SET name = ?, name_lower = ?, name_norm = ?, rel_path = ?
                               WHERE id = ?""",
                            (new_basename, name_lower, name_lower, new_rel, fid)
                        )
                        db_connection.commit()
                except Exception as db_err:
                    print(f"Avertissement DB rename : {db_err}")

        except Exception as e:
            errors.append(f"Erreur pour {item['old_name']} : {str(e)}")

    return success, len(errors), errors
