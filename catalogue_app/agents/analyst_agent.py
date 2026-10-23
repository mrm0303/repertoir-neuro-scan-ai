from .base_agent import BaseAgent
from catalogue_app.queries import stats
import json

ANALYST_PROMPT = """Tu es l'Agent Analyste & Directeur Technique Stockage de RNS.AI.
Ton rôle :
1. Analyser le parc de disques durs, la répartition des médias et la santé globale du stockage.
2. Alerter sur les déséquilibres, les disques saturés et les goulots d'étranglement de capacité.
3. Conseiller des mesures d'archivage ou de nettoyage concrètes.
4. Si un bilan écrit formel est pertinent, proposer d'exporter un rapport d'audit complet en Markdown via :
```action
{"command": "EXPORT_AUDIT_REPORT", "title": "Bilan_Stockage_Production"}
```
Adopte un ton direct, synthétique, expert et pragmatique de responsable technique de post-production.
"""

class AnalystAgent(BaseAgent):
    def __init__(self, db_connection):
        super().__init__(agent_id="dashboard_analyst", role="Data Analyst", system_prompt=ANALYST_PROMPT)
        self.con = db_connection

    def get_dashboard_context(self):
        try:
            v, fl, by_cat = stats(self.con)
            
            # Top volumes
            top_vols = []
            for r in self.con.execute("SELECT name, total_size, file_count FROM volumes ORDER BY total_size DESC LIMIT 5").fetchall():
                from catalogue_app.utils import human_size
                top_vols.append({"nom": r["name"], "taille": human_size(r["total_size"] or 0), "fichiers": r["file_count"]})
                
            from catalogue_app.utils import human_size
            context = {
                "total_volumes": v["n"] if v else 0,
                "total_files": fl["n"] if fl else 0,
                "total_size_humain": human_size(fl["s"] if fl else 0),
                "top_disques_plus_lourds": top_vols,
                "repartition_categories": [{"cat": r["category"], "count": r["n"], "taille": human_size(r["s"] or 0)} for r in by_cat]
            }
            return json.dumps(context, ensure_ascii=False, indent=2)
        except Exception as e:
            return f"Erreur de lecture des stats : {e}"

    def ask_insight(self, question="Fais-moi un résumé analytique court de mon stockage et donne-moi un conseil."):
        context = self.get_dashboard_context()
        return self.process_message(question, context_data=context)

