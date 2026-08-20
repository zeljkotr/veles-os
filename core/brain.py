from .planner import create_plan
from .executor import Executor
from .reporter import create_report

from .personality.personality import load_personality
from .memory.memory import get_memory_text
from .knowledge.search import get_knowledge_context

from services.intelligence.ollama_client import (
    call_ollama,
    extract_json
)


executor = Executor()


SYSTEM_RULES = """
STRICT VELES RULES:

LANGUAGE:

- Use English only.
- Never respond in Serbian.
- Never respond in Cyrillic.
- Technical terminology must remain in English.

STYLE:

- Respond as an experienced systems engineer.
- Be precise and practical.
- Avoid unnecessary introductions.
- Prefer concise, actionable answers.

LOCAL KNOWLEDGE:

- If LOCAL KNOWLEDGE is provided, use it as the primary source.
- Do not invent information that is not present in the available knowledge.
- Do not modify commands from documentation.
- When local documentation is used, identify the source document.

TECHNICAL RESPONSES:

- Put commands in code blocks.
- Explain procedures step by step when necessary.
- If uncertain, explicitly state that you are uncertain.
"""


def _detect_memorable_fact(
    question,
    answer
):

    prompt = f"""
Analyze the following conversation.

If there is a persistent fact worth remembering,
return only JSON:

{{"key":"...","value":"..."}}

If there is nothing worth remembering,
return:

{{}}

No additional text.

User:

{question}

VELES:

{answer}
"""

    raw = call_ollama(
        prompt,
        temperature=0.0,
        num_predict=80
    )

    parsed = extract_json(
        raw
    )

    if (
        parsed
        and parsed.get("key")
        and parsed.get("value")
    ):

        return parsed

    return None


def ask_veles(
    question
):

    plan = create_plan(
        question
    )

    print(
        "PLAN:",
        plan
    )

    if plan["action"] != "chat":

        tool_result = executor.execute(
            plan["action"],
            {
                "question": question,
                "plan": plan
            }
        )

        return {
            "answer": create_report(
                tool_result
            ),
            "suggested_memory": None
        }

    personality = load_personality()

    memory = get_memory_text()

    knowledge = get_knowledge_context(
        question
    )

    print(
        "\n========== LOCAL KNOWLEDGE =========="
    )

    print(
        knowledge
    )

    print(
        "=====================================\n"
    )

    prompt = f"""
{personality}

MEMORY:

{memory}

LOCAL KNOWLEDGE:

{knowledge}

{SYSTEM_RULES}

User:

{question}

VELES:
"""

    print(
        "VELES is thinking..."
    )

    raw_answer = call_ollama(
        prompt,
        temperature=0.2,
        num_predict=250
    )

    answer = raw_answer.strip()

    suggested_memory = _detect_memorable_fact(
        question,
        answer
    )

    return {
        "answer": answer,
        "suggested_memory": suggested_memory
    }