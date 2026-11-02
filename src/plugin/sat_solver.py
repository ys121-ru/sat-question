#!/usr/bin/env python3
"""
sat_solver.py

Parse a human-readable propositional formula, convert it to DIMACS CNF,
solve it with Glucose3 (via pysat), and return a JSON-serialisable dict.

Requires
--------
  pip install python-sat
"""

from __future__ import annotations

import json
import sys

from formula_to_dimacs import _parse, _is_cnf, _direct_cnf, _tseitin, to_dimacs
from pysat.solvers import Glucose3


def solve(formula: str) -> dict:
    """
    Solve a propositional formula given as a human-readable string.

    Returns a dict with keys:
      formula      – the input string (stripped)
      satisfiable  – True or False
      assignment   – dict mapping variable name → bool, or None when UNSAT
      dimacs       – the DIMACS CNF string that was fed to the solver
    """
    formula = formula.strip()
    ast     = _parse(formula)

    if _is_cnf(ast):
        var_map, clauses = _direct_cnf(ast)
    else:
        var_map, clauses = _tseitin(ast)

    id_to_name = {v: k for k, v in var_map.items()}
    dimacs_str = to_dimacs(formula)

    with Glucose3() as solver:
        for clause in clauses:
            solver.add_clause(clause)
        sat       = solver.solve()
        raw_model = solver.get_model() if sat else None

    assignment = None
    if raw_model is not None:
        assignment = {
            id_to_name[abs(lit)]: lit > 0
            for lit in raw_model
            if abs(lit) in id_to_name
        }

    return {
        "formula":     formula,
        "satisfiable": sat,
        "assignment":  assignment,
        "dimacs":      dimacs_str,
    }


def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)
    formula = " ".join(sys.argv[1:])
    print(json.dumps(solve(formula), indent=2))


if __name__ == "__main__":
    main()
