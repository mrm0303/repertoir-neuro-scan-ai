import os
import shutil
import json
from .base_agent import BaseAgent

DIT_PROMPT = """Tu es l'Agent DIT (Digital Imaging Technician) de RNS.AI.
Ton rôle sur les tournages et en studio :
1. Analyser la structure des cartes de tournage ou dossiers sources (détection de caméra Sony, Canon, RED, ARRI, DJI).
2. Contrôler rigoureusement l'espace disque de destination avant tout transfert (s'assurer qu'il reste au moins 15% de marge de sécurité après copie).
3. Recommander une nomenclature de dossier de déchargement rigoureuse : RUSHES_YYYY-MM-DD_[CAMERA]_[CARTE] (ex: RUSHES_2024-05-12_SONY-A_CARD01).
4. Recommander l'algorithme d'intégrité (xxHash pour la vitesse de tournage, MD5 pour la compatibilité universelle d'archivage légal).

Si l'analyse est concluante, tu peux proposer de pré-remplir la configuration du transfert via :
```action
{
  "command": "CONFIGURE_DIT",
  "folder_name": "RUSHES_2024-05-12_SONY-A",
  "algo": "xxhash"
}
```

Adopte un ton direct, ultra-rigoureux et rassurant de technicien de tournage.
"""

class DITAgent(BaseAgent):
    def __init__(self):
        super().__init__(agent_id="dit_ingest", role="Technicien DIT & Ingestion", system_prompt=DIT_PROMPT)

    def analyze_source(self, source_path, dest_path=None):
        if not source_path or not os.path.exists(source_path):
            return "Veuillez d'abord sélectionner un dossier ou une carte SD source valide."

        # Detect camera signatures
        cam_detected = "Inconnue / Générique"
        if os.path.exists(os.path.join(source_path, "PRIVATE", "M4ROOT")):
            cam_detected = "Sony Alpha / FX (XAVC / S-Cinetone)"
        elif os.path.exists(os.path.join(source_path, "CONTENTS")):
            cam_detected = "Panasonic Broadcast (P2 / AVC-Intra)"
        elif any(f.endswith(".braw") for _, _, files in os.walk(source_path) for f in files[:20]):
            cam_detected = "Blackmagic Cinema (BRAW)"
        elif any(f.endswith(".r3d") for _, _, files in os.walk(source_path) for f in files[:20]):
            cam_detected = "RED Digital Cinema (R3D)"
        elif os.path.exists(os.path.join(source_path, "DCIM")):
            cam_detected = "Boîtier Hybride / Reflex / Drone (DCIM standard)"

        # Calculate source size
        total_bytes = 0
        file_count = 0
        for root, _, filenames in os.walk(source_path):
            for fn in filenames:
                file_count += 1
                try:
                    total_bytes += os.path.getsize(os.path.join(root, fn))
                except: pass

        from catalogue_app.utils import human_size
        context = {
            "source": source_path,
            "signature_camera": cam_detected,
            "fichiers_detectes": file_count,
            "taille_totale": human_size(total_bytes)
        }

        # Check destination free space
        if dest_path and os.path.exists(dest_path):
            try:
                usage = shutil.disk_usage(dest_path)
                context["disque_destination_libre"] = human_size(usage.free)
                context["espace_suffisant"] = usage.free > (total_bytes * 1.15)
            except Exception as e:
                context["erreur_verif_dest"] = str(e)

        return self.process_message("Analyse cette carte/dossier de tournage et propose la meilleure configuration de déchargement DIT.", context_data=json.dumps(context, ensure_ascii=False, indent=2))
