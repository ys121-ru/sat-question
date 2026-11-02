"""Tool implementation: submit a yes/no answer for a SAT question."""

from __future__ import annotations

from pathlib import Path

from slimconfig import build_output

from contract import SubmitInput, SubmitOutput


def submit(inp: SubmitInput, workspace: Path) -> SubmitOutput:
    import sys, os
    sys.path.insert(0, os.path.dirname(__file__))
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "verifier"))

    from task import verify
    result = verify(inp.formula, inp.answer)
    return build_output(result, SubmitOutput)
