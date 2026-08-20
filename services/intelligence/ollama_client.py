"""
VELES Ollama Client

Centralized Ollama client for the VELES AI subsystem.

Ollama endpoint and model can be configured through environment
variables so VELES OS does not depend on host-specific settings.
"""

import json
import os
import re

import requests


OLLAMA_HOST = os.environ.get(
    "VELES_OLLAMA_HOST",
    "http://localhost:11434",
).rstrip("/")

OLLAMA_URL = f"{OLLAMA_HOST}/api/generate"

MODEL = os.environ.get(
    "VELES_OLLAMA_MODEL",
    "qwen2.5:7b",
)


def call_ollama(
    prompt: str,
    temperature: float = 0.2,
    num_predict: int = 200,
) -> str:
    """Send a prompt to the local VELES Ollama service."""

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": num_predict,
            },
        },
        timeout=(10, 600),
    )

    response.raise_for_status()

    return response.json()["response"]


def extract_json(text: str):
    """
    Extract the first JSON object from a model response.

    Returns None if no valid JSON object is found.
    """

    match = re.search(
        r"\{.*\}",
        text,
        re.DOTALL,
    )

    if not match:
        return None

    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return None