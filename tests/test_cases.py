"""Iterate over tests/cases/ and assert each verifier result matches the expected verdict."""

import pytest
from conftest import load_cases
from task import verify


@pytest.mark.parametrize("fname,case", load_cases(), ids=[c for c, _ in load_cases()])
def test_case(fname: str, case: dict) -> None:
    result = verify(case["formula"], case["agent_answer"])
    expect = case["expect"]

    detail = "\n".join(
        f"  [{c['id']}] {'ok' if c['ok'] else 'FAIL'}  {c['detail']}"
        for c in result["constraints"]
    )
    assert result["verdict"] == expect["verdict"], (
        f"\n{fname}: expected verdict={expect['verdict']!r}, got {result['verdict']!r}\n{detail}"
    )
    assert result["score"] == expect["score"], (
        f"\n{fname}: expected score={expect['score']}, got {result['score']}\n{detail}"
    )
