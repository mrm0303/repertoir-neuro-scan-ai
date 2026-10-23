import json
import os
import urllib.request
from catalogue_app.ai_chat import load_ai_config
from catalogue_app.config import APP_DIR

class BaseAgent:
    """Classe de base pour tous les agents spécialisés de RNS.AI."""

    def __init__(self, agent_id, role, system_prompt=None, default_skills_file=None):
        self.agent_id = agent_id
        self.role = role
        self.system_prompt = system_prompt
        self.default_skills_file = default_skills_file
        
        # Chemins de persistance (mémoire isolée dans ~/CatalogueDisques/agent_memory)
        self.base_dir = os.path.dirname(__file__)
        self.memory_dir = os.path.join(APP_DIR, "agent_memory")
        os.makedirs(self.memory_dir, exist_ok=True)
        self.memory_file = os.path.join(self.memory_dir, f"memory_{self.agent_id}.json")
        self.skills_file = os.path.join(self.base_dir, f"skills_{self.agent_id}.md")
        
        self.load_skills()
        self.load_memory()

    def load_skills(self):
        """Charge les instructions métier depuis le fichier Markdown."""
        if os.path.exists(self.skills_file):
            try:
                with open(self.skills_file, "r", encoding="utf-8") as f:
                    self.skills_prompt = f.read().strip()
                    return
            except Exception:
                pass
        self.skills_prompt = self.system_prompt or f"Tu es le {self.role} de l'application Repertoir."

    def get_effective_prompt(self):
        return f"{self.skills_prompt}\n\nAgis toujours conformément à ton rôle."

    def load_memory(self):
        """Charge l'historique de conversation de l'agent."""
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, "r", encoding="utf-8") as f:
                    self.history = json.load(f)
                    return
            except Exception:
                pass
        self.reset_memory()

    def save_memory(self):
        """Sauvegarde l'historique sur disque."""
        with open(self.memory_file, "w", encoding="utf-8") as f:
            json.dump(self.history, f, indent=4)

    def reset_memory(self):
        self.history = [{"role": "system", "content": self.get_effective_prompt()}]
        self.save_memory()

    def process_message(self, user_message, context_data=None, stream_callback=None):
        cfg = load_ai_config()
        if not cfg.get("enabled_chat", True):
            return "L'IA est désactivée dans les paramètres."

        # Toujours s'assurer que le premier message reflète les skills à jour
        if self.history and self.history[0]["role"] == "system":
            self.history[0]["content"] = self.get_effective_prompt()

        if context_data:
            self.history.append({"role": "system", "content": f"[Contexte d'interface actuel] : {context_data}"})

        self.history.append({"role": "user", "content": user_message})

        # Truncate history to prevent OOM on local LLM (keep system + last 20 messages)
        MAX_HISTORY = 20
        if len(self.history) > MAX_HISTORY + 1:
            self.history = [self.history[0]] + self.history[-(MAX_HISTORY):]

        url = cfg.get("url", "http://localhost:1234/api/v1/chat").strip()
        model = cfg.get("model", "qwen/qwen3.5-9b").strip()
        headers = {"Content-Type": "application/json"}
        if cfg.get("api_key"):
            headers["Authorization"] = f"Bearer {cfg['api_key']}"

        # Mode 1 : Endpoint natif LM Studio (/api/v1/chat)
        if "/api/v1/chat" in url:
            context_parts = []
            for m in self.history[:-1]:
                if m["role"] == "assistant":
                    context_parts.append(f"Assistant: {m['content']}")
                elif m["role"] == "system":
                    context_parts.append(f"Système: {m['content']}")

            sys_prompt = self.get_effective_prompt()
            if context_parts:
                sys_prompt += "\n\nHistorique récent:\n" + "\n".join(context_parts[-6:])

            payload = {
                "model": model,
                "input": user_message,
                "system_prompt": sys_prompt
            }

            integrations = cfg.get("mcp_integrations") or cfg.get("integrations")
            if integrations:
                payload["integrations"] = integrations
            if cfg.get("context_length"):
                payload["context_length"] = int(cfg["context_length"])

            req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers)
            try:
                with urllib.request.urlopen(req, timeout=120) as response:
                    res = json.loads(response.read().decode("utf-8"))
                    outputs = res.get("output", [])
                    msg = ""
                    reasoning = ""
                    tool_calls = []
                    for out in outputs:
                        if out.get("type") == "message":
                            msg += out.get("content", "")
                        elif out.get("type") == "reasoning":
                            reasoning += out.get("content", "")
                        elif out.get("type") == "tool_call":
                            tool_name = out.get("tool", "outil")
                            args = json.dumps(out.get("arguments", {}), ensure_ascii=False)
                            tool_out = out.get("output", "")
                            tool_calls.append(f"🛠️ **[MCP Tool: {tool_name}]** `{args}`\n> {tool_out}")

                    text = msg.strip() or reasoning.strip()
                    if tool_calls:
                        text = "\n\n".join(tool_calls) + ("\n\n" + text if text else "")
                    answer = text.strip() or "Aucune réponse reçue du modèle."
                    if stream_callback and answer:
                        stream_callback(answer)
                    self.history.append({"role": "assistant", "content": answer})
                    self.save_memory()
                    return answer
            except Exception as e:
                return f"Erreur_IA: {e}\n(Vérifiez que LM Studio est bien lancé sur: {url})"

        # Mode 2 : Endpoint OpenAI (/v1/chat/completions)
        data = {
            "model": model,
            "messages": self.history,
            "temperature": 0.3,
            "max_tokens": 2500,
            "stream": stream_callback is not None
        }

        req = urllib.request.Request(url, data=json.dumps(data).encode("utf-8"), headers=headers)

        try:
            with urllib.request.urlopen(req, timeout=120) as response:
                if stream_callback:
                    full_text = ""
                    for line in response:
                        line = line.decode("utf-8").strip()
                        if line.startswith("data: "):
                            line = line[6:]
                            if line == "[DONE]":
                                break
                            try:
                                chunk = json.loads(line)
                                if "choices" in chunk and len(chunk["choices"]) > 0:
                                    delta = chunk["choices"][0].get("delta", {})
                                    tok = delta.get("content") or delta.get("reasoning_content", "")
                                    if tok:
                                        full_text += tok
                                        stream_callback(tok)
                            except:
                                pass
                    answer = full_text.strip()
                    self.history.append({"role": "assistant", "content": answer})
                    self.save_memory()
                    return answer
                else:
                    res = json.loads(response.read().decode("utf-8"))
                    if "choices" in res and len(res["choices"]) > 0:
                        choice = res["choices"][0]
                        msg = choice.get("message", {})
                        answer = msg.get("content", "").strip()
                        if not answer and msg.get("reasoning_content"):
                            answer = msg["reasoning_content"].strip()
                        self.history.append({"role": "assistant", "content": answer})
                        self.save_memory()
                        return answer or "Réponse vide reçue du modèle."
                    return f"Format de réponse inattendu: {json.dumps(res)}"
        except Exception as e:
            return f"Erreur_IA: {e}\n(Vérifiez que LM Studio est bien lancé sur: {url})"
