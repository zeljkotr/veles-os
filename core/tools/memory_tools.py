"""
VELES Core Memory Tools.

Explicit-memory tool triggered when the user directly asks VELES
to remember something.

The local intelligence service extracts a clean key/value pair,
which is then persisted through the VELES memory subsystem.
"""

from ..memory.memory import remember

from services.intelligence.ollama_client import (
    call_ollama,
    extract_json
)


def remember_fact(context):

    question = context.get("question", "").strip()

    if not question:

        return {
            "success": False,
            "error": "No question provided."
        }

    prompt = f"""
Extract the key persistent fact from the following user request.

Return STRICTLY valid JSON.
Do not include explanations, comments, markdown, or any additional text.

Required format:

{{
    "key": "short fact name",
    "value": "the actual fact"
}}

User request:

"{question}"
"""

    raw = call_ollama(
        prompt,
        temperature=0.0,
        num_predict=100
    )

    parsed = extract_json(raw)

    if parsed and parsed.get("key") and parsed.get("value"):

        key = str(parsed["key"]).strip()
        value = str(parsed["value"]).strip()

    else:

        # Fallback: preserve the complete user request
        # instead of silently losing the information.

        key = "fact"
        value = question

    remember(
        key,
        value
    )

    return {
        "key": key,
        "value": value
    }