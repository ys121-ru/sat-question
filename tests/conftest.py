"""tests/conftest.py — path setup and case loader."""

import json, os, sys

ROOT = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.join(ROOT, "src", "plugin"))
sys.path.insert(0, os.path.join(ROOT, "verifier"))
sys.path.insert(0, ROOT)

CASES_DIR = os.path.join(os.path.dirname(__file__), "cases")


def load_cases() -> list[tuple[str, dict]]:
    cases = []
    for fname in sorted(os.listdir(CASES_DIR)):
        if fname.endswith(".json"):
            with open(os.path.join(CASES_DIR, fname)) as f:
                cases.append((fname, json.load(f)))
    return cases
