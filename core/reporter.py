"""
VELES Core Reporter.

Converts tool execution results into concise user-facing reports.
"""

from services.intelligence.ollama_client import call_ollama


def create_report(tool_result):

    if not tool_result.get("success"):

        return f"""
Tool execution failed:

{tool_result.get("error")}
""".strip()

    tool_name = tool_result.get("tool")
    data = tool_result.get("result")

    if tool_name == "remember_fact":

        return _create_memory_confirmation(data)

    if tool_name == "run_command":

        return _create_command_report(data)

    return _create_system_report(data)


def _create_memory_confirmation(data):

    return (
        f"Remembered: "
        f"{data['key']} = {data['value']}"
    )


def _create_command_report(data):

    if not data.get("executed"):

        return data.get(
            "output",
            "The command was not executed."
        )

    status = (
        "successfully"
        if data.get("success")
        else "with errors"
    )

    return f"""Command `{data['command']}` executed {status}.

Output:
{data['output']}"""


def _create_system_report(data):

    prompt = f"""
You are an experienced SRE engineer.

Analyze the following system information:

{data}

Create a concise professional system report.

Include:

- current system state
- CPU usage
- memory usage
- disk usage
- whether a problem exists
- recommendation if action is required

Use English only.
Use concise technical language.
"""

    return call_ollama(
        prompt,
        temperature=0.2,
        num_predict=200
    )