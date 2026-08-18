"""
VELES Core Planner.

Decision order:
1. Local rules
2. Ollama planner
"""

import re

from ..llm.ollama_client import call_ollama, extract_json


PLANNER_PROMPT_TEMPLATE = """
You are the planner for the VELES AI operations assistant.

Determine the user's requested action.

Available actions:

- chat:
  Questions, explanations, learning, or technical guidance.
  Do not execute commands.

- system_info:
  The user requests system information or system status.

- remember_fact:
  The user explicitly asks VELES to remember information.

- run_command:
  The user explicitly requests command execution.


Example:

User:
How do I restart a Linux service?

Response:

{{
"action": "chat",
"command": ""
}}


User:
Restart nginx.

Response:

{{
"action": "run_command",
"command": "systemctl restart nginx"
}}


Return only JSON:

{{
"action": "...",
"command": "..."
}}


Request:

"{question}"
"""


VALID_ACTIONS = (
    "chat",
    "system_info",
    "remember_fact",
    "run_command"
)


def local_intent_check(question):

    q = question.lower().strip()

    explanation_patterns = [
        r"^how ",
        r"^what ",
        r"^why ",
        r"^explain ",
        r"^describe ",
        r"^tell me "
    ]

    for pattern in explanation_patterns:

        if re.search(pattern, q):

            return {
                "action": "chat",
                "command": ""
            }

    system_words = [
        "check system",
        "system status",
        "system information",
        "cpu",
        "ram",
        "memory",
        "disk",
        "storage",
        "processes",
        "services"
    ]

    for word in system_words:

        if word in q:

            return {
                "action": "system_info",
                "command": ""
            }

    commands = [
        "restart ",
        "start ",
        "stop ",
        "shutdown ",
        "disable "
    ]

    for cmd in commands:

        if q.startswith(cmd):

            service = q.split(cmd, 1)[1].strip()

            if service:

                return {
                    "action": "run_command",
                    "command": f"systemctl restart {service}"
                }

    return None


def create_plan(question):

    local_plan = local_intent_check(question)

    if local_plan:

        return local_plan

    prompt = PLANNER_PROMPT_TEMPLATE.format(
        question=question
    )

    raw = call_ollama(
        prompt,
        temperature=0.0,
        num_predict=120
    )

    parsed = extract_json(raw)

    if not parsed or "action" not in parsed:

        return {
            "action": "chat",
            "command": ""
        }

    action = parsed.get(
        "action",
        "chat"
    )

    command = parsed.get(
        "command",
        ""
    ) or ""

    if action not in VALID_ACTIONS:

        return {
            "action": "chat",
            "command": ""
        }

    return {
        "action": action,
        "command": command
    }