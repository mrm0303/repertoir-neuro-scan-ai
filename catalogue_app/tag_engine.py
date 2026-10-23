import re
import sqlite3
from catalogue_app.db import add_manual_tag

# Liste de mots-clés thématiques forts à extraire des descriptions de vision IA
THEMATIC_SEEDS = [
    "nuit", "jour", "soir", "matin", "soleil", "coucher de soleil", "pluie", "neige",
    "désert", "sable", "mer", "plage", "océan", "eau", "vague", "forêt", "montagne", "nature",
    "ville", "urbain", "rue", "bâtiment", "architecture", "maison", "intérieur", "extérieur",
    "homme", "femme", "enfant", "personne", "foule", "portrait", "interview", "visage",
    "voiture", "véhicule", "moto", "avion", "bateau", "train", "drone",
    "animal", "chien", "chat", "cheval", "oiseau",
    "sombre", "lumineux", "contraste", "couleur", "noir et blanc", "ralenti", "macro"
]

def auto_tag_from_vision(con):
    """
    Parcourt les descriptions générées par l'IA de vision et attribue
    automatiquement des étiquettes de contenu aux fichiers correspondants.
    """
    rows = con.execute("SELECT file_id, vision_desc FROM ai_metadata").fetchall()
    total_tags_applied = 0
    
    for r in rows:
        fid = r["file_id"]
        desc = (r["vision_desc"] or "").lower()
        if not desc:
            continue
            
        tags_to_add = set()
        for seed in THEMATIC_SEEDS:
            # Vérifier la présence du mot clé dans la description
            if re.search(r'\b' + re.escape(seed) + r'\b', desc):
                tags_to_add.add(seed.capitalize())
                
        for tname in tags_to_add:
            add_manual_tag(con, [fid], tname, kind="contenu")
            total_tags_applied += 1
            
    con.commit()
    return total_tags_applied

def merge_tags(con, source_name, target_name):
    """
    Fusionne une étiquette source dans une étiquette cible.
    """
    s_row = con.execute("SELECT id FROM tags WHERE name = ?", (source_name.strip(),)).fetchone()
    t_row = con.execute("SELECT id FROM tags WHERE name = ?", (target_name.strip(),)).fetchone()
    
    if not s_row or not t_row:
        return False, "Une des deux étiquettes n'a pas été trouvée."
        
    s_id, t_id = s_row["id"], t_row["id"]
    if s_id == t_id:
        return False, "Les étiquettes sont identiques."
        
    # Déplacer les liaisons de s_id vers t_id (en ignorant les doublons)
    con.execute("""
        INSERT OR IGNORE INTO file_tags (file_id, tag_id)
        SELECT file_id, ? FROM file_tags WHERE tag_id = ?
    """, (t_id, s_id))
    
    con.execute("DELETE FROM file_tags WHERE tag_id = ?", (s_id,))
    con.execute("DELETE FROM tags WHERE id = ?", (s_id,))
    con.commit()
    return True, f"L'étiquette « {source_name} » a été fusionnée dans « {target_name} »."

def clean_orphan_tags(con):
    """
    Supprime les étiquettes qui ne sont plus rattachées à aucun fichier.
    """
    cur = con.execute("""
        DELETE FROM tags WHERE id NOT IN (SELECT DISTINCT tag_id FROM file_tags)
    """)
    deleted = cur.rowcount
    con.commit()
    return deleted
