"""
tests/test_verifier.py

The sat-question verdict: correct answers pass all constraints,
and each constraint fails on its own case with its own message.
"""

from __future__ import annotations

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "plugin"))

import verifier
from slimconfig import build_output
from contract import SubmitInput, SubmitOutput, Task


def _run(formula: str, answer: str) -> dict:
    inp = build_output({"formula": formula, "answer": answer}, SubmitInput)
    out = build_output({"verdict": "?", "score": 0.0, "constraints": []}, SubmitOutput)
    return verifier.verify_task(Task.SAT_QUESTION.value, inp, out, None, "/tmp")


def _failed_id(result: dict) -> str:
    for c in result["constraints"]:
        if not c["ok"]:
            return c["id"]
    return ""


# ── Correct answers pass ───────────────────────────────────────────────────────

def test_sat_formula_yes_passes():
    result = _run("(A ∨ ¬B) ∧ (¬A ∨ C)", "yes")
    assert result["valid"] and result["score"] == 1.0
    assert all(c["ok"] for c in result["constraints"])


def test_unsat_formula_no_passes():
    result = _run("A ∧ ¬A", "no")
    assert result["valid"] and result["score"] == 1.0


def test_implication_unsat_passes():
    result = _run("(A → B) ∧ A ∧ ¬B", "no")
    assert result["valid"] and result["score"] == 1.0


# ── Each constraint fails on its own case ─────────────────────────────────────

def test_bad_formula_fails_first():
    result = _run("(A ∨ ∧ B)", "yes")
    assert not result["valid"] and result["score"] == 0.0
    assert _failed_id(result) == "formula-valid"


def test_bad_answer_shape_fails_second():
    result = _run("A ∨ B", "maybe")
    assert not result["valid"] and result["score"] == 0.0
    assert _failed_id(result) == "answer-shape"


def test_wrong_sat_answer_fails_third():
    result = _run("A ∧ ¬A", "yes")   # UNSAT but agent says yes
    assert not result["valid"] and result["score"] == 0.0
    assert _failed_id(result) == "sat-correct"


def test_wrong_unsat_answer_fails_third():
    result = _run("A ∨ B", "no")     # SAT but agent says no
    assert not result["valid"] and result["score"] == 0.0
    assert _failed_id(result) == "sat-correct"


# ── Constraint order ──────────────────────────────────────────────────────────

def test_bad_formula_stops_before_answer_shape():
    result = _run("(A ∨ ∧ B)", "maybe")
    ids = [c["id"] for c in result["constraints"]]
    assert "answer-shape" not in ids

def test_bad_shape_stops_before_sat_correct():
    result = _run("A ∨ B", "maybe")
    ids = [c["id"] for c in result["constraints"]]
    assert "sat-correct" not in ids
