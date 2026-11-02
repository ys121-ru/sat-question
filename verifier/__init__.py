"""The deterministic verifier: checks the agent's answer against the SAT solver."""

from contract import Task, Tool
from . import task as _task

TOOLS = {Tool.SUBMIT: _task}
TASKS = {Task.SAT_QUESTION: _task.verify_task}


def verify_input(tool: str, value) -> list[dict]:
    return TOOLS[Tool(tool)].verify_input(value)


def verify_output(tool: str, input_value, output_value, workspace: str) -> dict:
    return TOOLS[Tool(tool)].verify_output(input_value, output_value, workspace)


def verify_task(task: str, arguments, output, reference, workspace: str) -> dict:
    return TASKS[Task(task)](arguments, output, reference, workspace)
