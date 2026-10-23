import urllib.request
import json
import sqlite3
import os

from catalogue_app.config import APP_DIR

os.makedirs(APP_DIR, exist_ok=True)
CONFIG_FILE = os.path.join(APP_DIR, "ai_config.json")
_LEGACY_CONFIG_FILE = os.path.join(os.path.dirname(__file__), "ai_config.json")

# Migration transparente de l'ancien fichier local vers ~/CatalogueDisques/ai_config.json
if not os.path.exists(CONFIG_FILE) and os.path.exists(_LEGACY_CONFIG_FILE):
    try:
        import shutil
        shutil.copy2(_LEGACY_CONFIG_FILE, CONFIG_FILE)
    except Exception:
        pass

def load_ai_config():
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {
            "url": "http://localhost:1234/api/v1/chat",
            "model": "qwen/qwen3.5-9b",
            "api_key": "",
            "enabled_chat": True,
            "enabled_vision": True
        }

def save_ai_config(cfg):
    os.makedirs(APP_DIR, exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=4)

SYSTEM_PROMPT = """Tu es l'Assistant IA intégré au logiciel 'Repertoir', un gestionnaire de catalogue de disques durs hors-ligne.
Ton but est d'aider l'utilisateur à retrouver ses fichiers, comprendre son stockage, et répondre à ses questions.

Tu as accès à une base de données SQLite contenant le catalogue de l'utilisateur.
- Table `volumes` : id, name, file_count, total_size, last_path, priority, note
- Table `files` : id, volume_id, rel_path, name, ext, category, size, mtime, width, height, fps, codec, camera

RÈGLE D'OR POUR CHERCHER DANS LA BASE :
Si l'utilisateur te pose une question qui nécessite de lire la base de données (ex: "Quelles sont mes plus grosses vidéos ?"), tu NE DOIS PAS répondre directement.
Tu dois répondre UNIQUEMENT par une requête SQL valide commençant exactement par le préfixe "SQL: ".
Exemple:
SQL: SELECT name, size, (SELECT name FROM volumes WHERE id=files.volume_id) AS disque FROM files WHERE category='video' ORDER BY size DESC LIMIT 5;

L'application interceptera cette requête, l'exécutera, et te renverra les résultats bruts. Tu pourras alors formuler ta réponse finale en français naturel.
Si c'est une question générale ou si tu as déjà les résultats (donnés sous forme de [Système]), réponds normalement en français naturel et de manière concise. N'invente jamais de faux fichiers.
"""

def chat_with_llm(messages, max_tokens=2500, stream_callback=None):
    cfg = load_ai_config()
    if not cfg.get("enabled_chat", True):
        return "Assistant IA désactivé dans les paramètres."

    url = cfg.get("url", "http://localhost:1234/api/v1/chat").strip()
    model = cfg.get("model", "qwen/qwen3.5-9b").strip()
    
    headers = {"Content-Type": "application/json"}
    if cfg.get("api_key"):
        headers["Authorization"] = f"Bearer {cfg['api_key']}"

    # Mode 1 : Endpoint natif LM Studio (/api/v1/chat)
    if "/api/v1/chat" in url:
        # Extraire le dernier message utilisateur et le contexte
        user_input = ""
        context_parts = []
        for m in messages:
            if m["role"] == "user":
                user_input = m["content"]
            elif m["role"] == "assistant":
                context_parts.append(f"Assistant: {m['content']}")
            elif m["role"] == "system":
                context_parts.append(f"Système: {m['content']}")

        sys_prompt = SYSTEM_PROMPT
        if context_parts:
            sys_prompt += "\n\nHistorique récent:\n" + "\n".join(context_parts[-6:])

        payload = {
            "model": model,
            "input": user_input or "Bonjour",
            "system_prompt": sys_prompt
        }

        integrations = cfg.get("mcp_integrations") or cfg.get("integrations")
        if integrations:
            payload["integrations"] = integrations
        if cfg.get("context_length"):
            payload["context_length"] = int(cfg["context_length"])

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers
        )

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
                final_text = text.strip()
                if stream_callback and final_text:
                    stream_callback(final_text)
                return final_text or "Aucune réponse reçue du modèle."
        except Exception as e:
            return f"Erreur_IA: {e}\n(Vérifiez que LM Studio est bien lancé sur: {url})"

    # Mode 2 : Endpoint standard OpenAI (/v1/chat/completions)
    openai_messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for m in messages:
        openai_messages.append({"role": m["role"], "content": m["content"]})

    data = {
        "model": model,
        "messages": openai_messages,
        "temperature": 0.3,
        "max_tokens": max_tokens,
        "stream": stream_callback is not None
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode("utf-8"),
        headers=headers
    )

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
                                # Support reasoning_content & content
                                tok = delta.get("content") or delta.get("reasoning_content", "")
                                if tok:
                                    full_text += tok
                                    stream_callback(tok)
                        except:
                            pass
                return full_text.strip()
            else:
                res = json.loads(response.read().decode("utf-8"))
                if "choices" in res and len(res["choices"]) > 0:
                    choice = res["choices"][0]
                    msg = choice.get("message", {})
                    content = msg.get("content", "").strip()
                    # Fallback sur reasoning_content si content est vide (modèles Qwen/DeepSeek)
                    if not content and msg.get("reasoning_content"):
                        content = msg["reasoning_content"].strip()
                    return content or "Réponse vide reçue du modèle."
                return f"Format de réponse inattendu: {json.dumps(res)}"

    except Exception as e:
        return f"Erreur_IA: {e}\n(Vérifiez que LM Studio est bien lancé sur: {url})"