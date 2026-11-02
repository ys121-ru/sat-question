"""Each tool's and task's typed input and output: declarations only."""

from dataclasses import dataclass
from enum import Enum
from typing import Annotated

from slimconfig import Output


class Tool(Enum):
    SUBMIT = "submit"


class Task(Enum):
    SAT_QUESTION = "sat-question"


@dataclass
class Constraint(Output):
    id:     Annotated[str,  "The constraint identifier"]
    ok:     Annotated[bool, "True if the constraint passed"]
    detail: Annotated[str,  "Human-readable explanation"]


@dataclass
class SubmitInput(Output):
    formula: Annotated[str, "The propositional formula to judge for satisfiability"]
    answer:  Annotated[str, 'The agent\'s answer: exactly "yes" (SAT) or "no" (UNSAT)']


@dataclass
class SubmitOutput(Output):
    verdict:     Annotated[str,              '"pass" if the answer is correct, "fail" otherwise']
    score:       Annotated[float,            "1.0 for pass, 0.0 for fail"]
    constraints: Annotated[list[Constraint], "Each constraint checked, in order"]


TOOLS = {
    Tool.SUBMIT: (SubmitInput, SubmitOutput),
}

TASKS = {
    Task.SAT_QUESTION: (SubmitInput, SubmitOutput),
}
