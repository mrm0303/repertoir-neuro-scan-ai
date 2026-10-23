from .base_agent import BaseAgent
import json

PROJ_PROMPT = """Tu es l'Agent Chef de Projet & Assistant de Post-Production de RNS.AI.
Ton rôle :
1. Analyser l'état des projets (Premiere Pro, DaVinci Resolve, Final Cut Pro, etc.).
2. Si un projet spécifique est sélectionné avec ses rushes associés, indiquer clairement si tous les disques nécessaires sont branchés ou quels disques externes doivent être sortis des tiroirs pour pouvoir monter sans médias hors-ligne ("Media Offline").
3. Proposer de générer une "Fiche d'intervention Monteur" (mémo des disques à brancher et état des rushes) via l'action :
```action
{"command": "EXPORT_PROJECT_MEMO", "project": "Nom_Du_Projet"}
```
4. Si un projet est très ancien et volumineux, tu peux proposer de l'archiver via l'action :
```action
{"command": "ARCHIVE_PROJECT", "path": "/chemin/du/projet"}
```
Sois très direct, professionnel et orienté vers l'efficacité en studio de montage.
"""

class ProjectAgent(BaseAgent):
    def __init__(self):
        super().__init__(agent_id="project_manager", role="Chef de Projet", system_prompt=PROJ_PROMPT)

    def analyze_projects(self, projects_list, selected_project_report=None):
        if selected_project_report:
            pname = selected_project_report.get("project", "Projet")
            found = selected_project_report.get("total_media_found", 0)
            size = selected_project_report.get("total_size_human", "0 Mo")
            to_plug = selected_project_report.get("drives_to_plug", [])
            online = selected_project_report.get("drives_online", [])
            
            context = f"L'utilisateur a sélectionné le projet : '{pname}'.\n"
            context += f"- Rushes trouvés dans le catalogue : {found} ({size})\n"
            if to_plug:
                context += f"- Disques à brancher (HORS-LIGNE) : {', '.join(to_plug)}\n"
            if online:
                context += f"- Disques déjà branchés (EN LIGNE) : {', '.join(online)}\n"
            if not to_plug:
                context += "- Tous les disques contenant les rushes sont déjà branchés !\n"
            context += "Donne un conseil court sur l'état de ce projet et propose si besoin de générer la fiche monteur (EXPORT_PROJECT_MEMO)."
            return self.process_message("Analyse ce projet spécifique et dis-moi s'il est prêt à être monté.", context_data=context)
            
        if not projects_list:
            return "Aucun projet affiché pour le moment."
        
        context = "Voici les projets actuellement affichés :\n"
        for i, p in enumerate(projects_list):
            context += f"{i+1}. Nom: {p.get('nom', '?')} | Logiciel: {p.get('logiciel', '?')} | Disque: {p.get('disque', '?')} | Modifié: {p.get('modifie', '?')}\n"
            
        return self.process_message("Fais-moi un petit point sur ces projets.", context_data=context)
