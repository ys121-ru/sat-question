"""Verifier for the sat-question task and submit tool."""

from __future__ import annotations

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "plugin"))

from pathlib import Path

from contract import SubmitInput, SubmitOutput
from sat_solver import solve


def _constraint(cid: str, ok: bool, detail: str) -> dict:
    return {"id": cid, "ok": ok, "detail": detail}


def _verdict(passed: bool, constraints: list[dict]) -> dict:
    return {
        "valid":       passed,
        "verdict":     "pass" if passed else "fail",
        "score":       1.0 if passed else 0.0,
        "constraints": constraints,
    }


def verify_input(inp: SubmitInput) -> list[dict]:
    return []


def verify_output(inp: SubmitInput, out: SubmitOutput, workspace: Path) -> dict:
    """
    Constraints (in order):
      1. formula-valid   — the formula parses without error
      2. answer-shape    — answer is exactly "yes" or "no"
      3. sat-correct     — answer matches the solver's verdict
    """
    constraints = []

    # Constraint 1 — formula parses
    try:
        from formula_to_dimacs import _parse
        _parse(inp.formula)
        constraints.append(_constraint("formula-valid", True, "formula parsed OK"))
    except Exception as exc:
        constraints.append(_constraint("formula-valid", False, f"parse error: {exc}"))
        return _verdict(False, constraints)

    # Constraint 2 — answer shape
    normalised = inp.answer.strip().lower()
    if normalised not in ("yes", "no"):
        constraints.append(_constraint(
            "answer-shape", False,
            f"expected 'yes' or 'no', got {inp.answer!r}",
        ))
        return _verdict(False, constraints)
    constraints.append(_constraint("answer-shape", True, f"answer shape OK: {normalised!r}"))

    # Constraint 3 — correctness
    result   = solve(inp.formula)
    expected = "yes" if result["satisfiable"] else "no"
    if normalised == expected:
        constraints.append(_constraint(
            "sat-correct", True,
            f"answer {normalised!r} matches solver ({expected!r})",
        ))
        return _verdict(True, constraints)

    constraints.append(_constraint(
        "sat-correct", False,
        f"answer {normalised!r} is wrong — "
        f"solver says {'SAT' if result['satisfiable'] else 'UNSAT'} (expected {expected!r})",
    ))
    return _verdict(False, constraints)


def verify_task(arguments: SubmitInput, output: SubmitOutput,
                reference, workspace: str) -> dict:
    return verify_output(arguments, output, Path(workspace))


# Legacy helper for test_cases.py
def verify(formula: str, answer: str) -> dict:
    from slimconfig import build_output
    inp = build_output({"formula": formula, "answer": answer}, SubmitInput)
    out = build_output({"verdict": "?", "score": 0.0, "constraints": []}, SubmitOutput)
    return verify_output(inp, out, Path("/tmp"))
