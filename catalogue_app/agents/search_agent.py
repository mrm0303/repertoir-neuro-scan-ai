from .base_agent import BaseAgent
import json

SEARCH_PROMPT = """Tu es l'Agent Documentaliste et Assistant Monteur de RNS.AI.
Ton rôle :
1. Analyser la requête et le profil technique des rushes trouvés (formats, définitions 4K/HD, codecs ProRes/H264, caméras).
2. Conseiller l'utilisateur sur la pertinence de ses rushes pour le montage (ex: cohérence des cadences d'images, variété des plans).
3. Proposer de monter automatiquement les rushes dans une Timeline XML (Premiere Pro, DaVinci Resolve, Final Cut Pro) :
   - Soit dans l'ordre chronologique de tournage (idéal pour un ours de tournage / derushage) :
```action
{"command": "EXPORT_CHRONO_TIMELINE", "title": "Ours_Chronologique"}
```
   - Soit dans l'ordre d'affichage standard :
```action
{"command": "EXPORT_TIMELINE", "title": "Selection_Rushes"}
```

Sois direct, concis et oriente tes conseils vers l'efficacité en salle de montage.
"""

class SearchAgent(BaseAgent):
    def __init__(self):
        super().__init__(agent_id="search_assistant", role="Archiviste & Monteur", system_prompt=SEARCH_PROMPT)

    def analyze_search(self, query, results_count, tech_profile=None):
        context = f"Requête de recherche : '{query}'. Nombre de rushes trouvés : {results_count}.\n"
        if tech_profile:
            context += f"Profil technique des résultats :\n"
            if tech_profile.get("definitions"):
                context += f"- Définitions : {', '.join(f'{k}: {v}' for k, v in tech_profile['definitions'].items())}\n"
            if tech_profile.get("codecs"):
                context += f"- Codecs : {', '.join(f'{k}: {v}' for k, v in tech_profile['codecs'].items())}\n"
            if tech_profile.get("cameras"):
                context += f"- Caméras : {', '.join(f'{k}: {v}' for k, v in tech_profile['cameras'].items())}\n"
            if tech_profile.get("dates"):
                context += f"- Période couverte : {tech_profile['dates']}\n"

        if results_count == 0:
            msg = "Je n'ai rien trouvé pour cette recherche. Comment puis-je élargir ou corriger mes mots-clés ?"
        else:
            msg = f"Voici les {results_count} rushes trouvés. Analyse ce profil et propose-moi un plan de montage ou timeline."
        return self.process_message(msg, context_data=context)
