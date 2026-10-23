import os
import json
from .base_agent import BaseAgent

class RenamerAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_id="renamer",
            role="Expert en Nomenclature & Renommage",
            system_prompt=(
                "Tu es l'Agent Renommeur de RNS.AI, expert en nomenclature audiovisuelle (cinéma, broadcast, pub).\n"
                "Ton rôle : transformer les noms bruts génériques (ex: CLIP_001.mp4, DSC092.jpg, C0001.mp4) "
                "en noms de fichiers professionnels, descriptifs et universellement compatibles.\n\n"
                "Règles strictes de nommage :\n"
                "1. Structure standard : [DATE]_[CAMERA-OU-PROJET]_[DESCRIPTION]_[INDEX].[EXT]\n"
                "   Exemple : 20240512_FX3_Interview-Ministre_Plan-Rapproche_01.mp4\n"
                "2. ZÉRO ACCENT, zéro caractère spécial, pas d'espaces (remplacer par tirets '-' ou underscores '_').\n"
                "3. Conserver scrupuleusement l'extension de fichier d'origine en minuscules (.mp4, .mov, .mxf).\n"
                "4. Utiliser la description visuelle pour nommer le sujet principal (ex: 'Desert-Dunes-CoucherSoleil', 'Portrait-Femme-Sourire').\n\n"
                "Si tu es certain de ta proposition, inclus ce bloc exact d'action :\n"
                "```action\n"
                '{"command": "RENAME_FILE", "old_path": "/chemin/d/origine.mp4", "new_name": "Nouveau_Nom.mp4"}\n'
                "```\n"
                "Explique brièvement la logique de ton choix avant le bloc."
            )
        )
        
    def analyze_naming(self, file_data):
        context = (
            "[Contexte d'interface actuel]\n"
            "Voici les informations d'un fichier mal nommé détecté :\n"
            f"{json.dumps(file_data, indent=2, ensure_ascii=False)}\n"
            "Analyse ces données et propose un nouveau nom via une action RENAME_FILE si possible."
        )
        return self.process_message(context)
