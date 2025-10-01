# src/llm_client.py
import os
import requests

# Ollama defaults: you already have it running on 127.0.0.1:11434 and a model (qwen2:0.5b)
OLLAMA_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
MODEL = os.getenv("GEN_MODEL", "qwen2:0.5b")  # change later if you want (e.g., "llama3.2:1b")

def chat(messages):
    """
    Call Ollama's /api/chat with a simple list of messages:
      messages = [
        {"role": "system", "content": "Short instructions"},
        {"role": "user", "content": "Your question"}
      ]
    Returns the assistant's text string.
    """
    url = f"{OLLAMA_URL}/api/chat"
    payload = {
        "model": MODEL,
        "messages": messages,
        "stream": False
    }
    # Make the request to local Ollama
    r = requests.post(url, json=payload, timeout=60)
    r.raise_for_status()
    data = r.json()
    # Ollama returns the assistant message here:
    return data["message"]["content"]
