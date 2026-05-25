import requests
import json

OLLAMA_API_URL = "http://localhost:11434/api/generate"

def query_ollama(prompt: str, model: str = "llama3"):
    """
    Sends a prompt to the local Ollama server via HTTP API and returns the response.
    """
    try:
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False
        }
        response = requests.post(OLLAMA_API_URL, json=payload)
        response.raise_for_status()
        return response.json().get("response", "").strip()
    except requests.exceptions.RequestException as e:
        return f"[Ollama Error] Could not connect to Ollama API. Is it running? Error: {e}"
    except Exception as e:
        return f"[Ollama Error] {str(e)}"

def styled_reply(user_text: str, personality: str = "calm"):
    """
    Ask Ollama to generate a response in a specific personality style.
    """
    style_prompt = f"""
    You are MIA, an AI desktop assistant.
    Speak to the user in a {personality} style.

    User: "{user_text}"
    MIA:
    """
    return query_ollama(style_prompt)

def structured_plan(prompt: str) -> dict:
    """
    Ask Ollama for a STRICT JSON plan. Returns dict or empty dict on error.
    """
    raw = query_ollama(prompt)
    try:
        # Naive extraction of first JSON block
        start = raw.find("{")
        end = raw.rfind("}")
        if start != -1 and end != -1 and end > start:
            return json.loads(raw[start:end+1])
    except Exception:
        pass
    return {}
