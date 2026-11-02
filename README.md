# sat-question

A [NanoAgent](https://github.com/RUSH-LAB/nanoagent) plugin.
Given a propositional logic formula, the agent decides whether it is
satisfiable and answers **"yes"** or **"no"**.

---

## Formula syntax

| Operator | Accepted symbols |
|---|---|
| Negation | `¬` `~` `!` `not` |
| Conjunction | `∧` `&` `and` |
| Disjunction | `∨` `\|` `or` |
| Implication | `→` `->` `=>` |
| Biconditional | `↔` `<->` `<=>` |

Variables are any alphanumeric identifier starting with a letter: `A`, `x1`, `my_var`.

---

## Install

```bash
pip install mcp slimconfig python-sat
# or with uv:
uv sync
```

---

## Run the tests

```bash
pytest tests/
```

---

## Project structure

```
sat-question/
├── contract.py              # Tool/Task enums, Input/Output dataclasses
├── pyproject.toml
├── nanoagent.yaml
│
├── src/plugin/
│   ├── __init__.py
│   ├── __main__.py          # MCP stdio server
│   ├── formula_to_dimacs.py # Parser + CNF converter
│   ├── sat_solver.py        # solve(formula) → {satisfiable, assignment, …}
│   └── submit.py            # Tool implementation
│
├── verifier/
│   ├── __init__.py
│   └── task.py              # Three constraints → verdict
│
├── tests/
│   ├── cases/               # One .json file per test case
│   ├── conftest.py
│   ├── test_cases.py
│   └── test_verifier.py
│
├── ui/
│   ├── renderers.js
│   └── renderers.css
│
└── product/
    ├── product.yaml
    └── icon.svg
```

---

## Constraints

| # | id | Checks |
|---|---|---|
| 1 | `formula-valid` | Formula parses without error |
| 2 | `answer-shape` | Answer is exactly `"yes"` or `"no"` |
| 3 | `sat-correct` | Answer matches the Glucose3 solver |

---

## Adding a test case

```json
{
  "description": "A ∧ ¬A is UNSAT — agent says no",
  "formula": "A ∧ ¬A",
  "agent_answer": "no",
  "expect": { "verdict": "pass", "score": 1.0 }
}
```
