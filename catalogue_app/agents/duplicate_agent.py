from .base_agent import BaseAgent
import json

DUP_PROMPT = """Tu es l'Agent Nettoyeur & Archiviste de Sécurité de RNS.AI.
Ton rôle est d'analyser les doublons stricts et de recommander avec une prudence chirurgicale quelle copie déplacer vers la Corbeille.

Règles de sécurité absolues :
1. Ne recommande JAMAIS de supprimer un fichier situé dans un dossier de projet NLE, de montage ou de livraison finale (/Projets/, /Montage/, /Masters/, /Exports_Clients/).
2. Privilégie TOUJOURS la suppression dans les dossiers de téléchargement, temporaires, caches ou doublons sur disques de travail saturés (/Downloads/, /Temp/, /Vrac/).
3. Si une copie est sur un disque hors-ligne ou si le doute subsiste, propose de la conserver et explique pourquoi.

Pour proposer la mise à la corbeille sécurisée d'une copie en trop, inclus ce bloc exact à la fin de ta réponse :
```action
{
  "command": "TRASH_FILE",
  "path": "/chemin/complet/du/fichier.mp4",
  "reason": "Raison brève du choix"
}
```

Format de réponse attendu :
1. Une brève analyse comparative (1-2 phrases).
2. L'explication du choix de la copie à conserver et de celle à déplacer à la corbeille.
3. Le bloc action (si un choix évident se dégage).
"""

class DuplicateAgent(BaseAgent):
    def __init__(self):
        super().__init__(agent_id="duplicate_cleaner", role="Nettoyeur", system_prompt=DUP_PROMPT)

    def analyze_duplicates(self, duplicates_list):
        if not duplicates_list:
            return "Aucun doublon à analyser."
        
        context = "Voici un groupe de fichiers en double strict :\n"
        for i, f in enumerate(duplicates_list):
            statut = "Branché 🟢" if f.get('online', True) else "Débranché ⚪"
            context += f"{i+1}. Disque: {f.get('disque', '?')} [{statut}] | Chemin: {f.get('chemin', '?')} | Taille: {f.get('taille', '?')}\n"
            
        return self.process_message("Analyse ces copies et indique-moi avec certitude celle qu'on peut mettre à la corbeille en toute sécurité.", context_data=context)
