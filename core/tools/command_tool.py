"""
VELES Core Command Tool.

Executes shell commands explicitly requested by the user
and approved by the VELES planner.

Obviously destructive commands are refused automatically.
Every command attempt is recorded through the VELES Core
Events subsystem.
"""

import subprocess

from ..events import log_event


DESTRUCTIVE_PATTERNS = [
    "rm -rf",
    "mkfs",
    " dd if=",
    "shutdown",
    "reboot",
    ":(){ :|:& };:",
    "chmod -r 777",
    "> /dev/sd",
    "fdisk",
    "drop database",
    "drop table",
]


def _looks_destructive(command: str):

    lowered = command.lower()

    for pattern in DESTRUCTIVE_PATTERNS:

        if pattern in lowered:
            return pattern

    return None


def run_command(context):

    context = context or {}

    plan = context.get("plan", {})
    question = context.get("question", "")

    command = (
        plan.get("command") or ""
    ).strip()

    if not command:

        return {
            "executed": False,
            "command": "",
            "output": "No executable command was identified."
        }

    risky_pattern = _looks_destructive(command)

    if risky_pattern:

        log_event(
            "command_refused",
            {
                "question": question,
                "command": command,
                "reason": (
                    "matched destructive pattern: "
                    f"{risky_pattern}"
                )
            }
        )

        return {
            "executed": False,
            "command": command,
            "output": (
                "This command appears risky "
                f"(contains '{risky_pattern}'). "
                "It was not executed."
            )
        }

    log_event(
        "command_started",
        {
            "question": question,
            "command": command
        }
    )

    try:

        result = subprocess.run(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=30
        )

        output = (
            result.stdout.strip()
            or result.stderr.strip()
            or "(no output)"
        )

        success = result.returncode == 0

        log_event(
            "command_finished",
            {
                "question": question,
                "command": command,
                "returncode": result.returncode,
                "success": success
            }
        )

        return {
            "executed": True,
            "command": command,
            "output": output,
            "success": success
        }

    except subprocess.TimeoutExpired:

        log_event(
            "command_timeout",
            {
                "question": question,
                "command": command
            }
        )

        return {
            "executed": False,
            "command": command,
            "output": "Command timed out after 30 seconds."
        }

    except Exception as exc:

        log_event(
            "command_error",
            {
                "question": question,
                "command": command,
                "error": str(exc)
            }
        )

        return {
            "executed": False,
            "command": command,
            "output": f"Command execution error: {exc}"
        }