# backend/extraction/llm_client.py
# Single place to manage all LLM calls in ARGUS
# Switch provider by changing LLM_PROVIDER in .env

import os
import requests
from dotenv import load_dotenv

load_dotenv()

PROVIDER = os.getenv("LLM_PROVIDER", "groq")

PROVIDERS = {
    "groq": {
        "base_url": "https://api.groq.com/openai/v1/chat/completions",
        "api_key": os.getenv("GROQ_API_KEY"),
        "model": "llama-3.1-8b-instant"
    },
    "ollama": {
        "base_url": "http://localhost:11434/v1/chat/completions",
        "api_key": "ollama",
        "model": "llama3.2"
    }
}


def call_llm(prompt: str, system: str = None, max_tokens: int = 1000) -> str:
    """
    Single function for all LLM calls across ARGUS.
    Returns raw text response.
    """
    config = PROVIDERS.get(PROVIDER)
    if not config:
        raise ValueError(f"Unknown LLM provider: {PROVIDER}")

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    headers = {
        "Authorization": f"Bearer {config['api_key']}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": config["model"],
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": 0.1   # low temperature = consistent structured output
    }

    response = requests.post(config["base_url"], json=payload, headers=headers)
    response.raise_for_status()

    return response.json()["choices"][0]["message"]["content"].strip()


def call_llm_json(prompt: str, system: str = None) -> dict:
    """
    LLM call that expects and parses JSON response.
    Use this for claim extraction.
    """
    import json

    json_system = (system or "") + "\nRespond ONLY with valid JSON. No explanation, no markdown, no backticks."

    raw = call_llm(prompt, system=json_system, max_tokens=1000)

    # Clean up common LLM formatting mistakes
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"LLM returned invalid JSON: {e}\nRaw output: {raw}")
