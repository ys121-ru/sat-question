#!/usr/bin/env python3
"""
formula_to_dimacs.py

Convert a human-readable propositional logic formula to DIMACS CNF.

Supported syntax
----------------
  Variables    : any letter/digit/underscore sequence starting with a letter
                 e.g.  A  B  x1  my_var
  Negation     : ¬A   ~A   !A
  Disjunction  : A ∨ B   A | B   A or B
  Conjunction  : A ∧ B   A & B   A and B
  Implication  : A → B   A -> B   A => B    (right-associative)
  Biconditional: A ↔ B   A <-> B  A <=> B
  Grouping     : ( A ∨ ¬B ) ∧ C

Strategy
--------
If the formula is already in Conjunctive Normal Form (a conjunction of
disjunctions of literals), its clauses are extracted directly — no auxiliary
variables are introduced.

Otherwise the Tseitin transformation is used: each sub-formula gets a fresh
auxiliary variable and a small set of clauses that define it.  The overall
variable count grows linearly with formula size, and the clause set is
equisatisfiable with the original formula.

Output
------
Standard DIMACS CNF with comment lines documenting the variable mapping and
the original formula.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from typing import Any


# ── AST nodes ─────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class Var:
    name: str

@dataclass(frozen=True)
class Not:
    child: Any

@dataclass(frozen=True)
class And:
    left: Any
    right: Any

@dataclass(frozen=True)
class Or:
    left: Any
    right: Any

@dataclass(frozen=True)
class Implies:
    left: Any
    right: Any

@dataclass(frozen=True)
class Iff:
    left: Any
    right: Any


# ── Lexer ──────────────────────────────────────────────────────────────────────

_TOKEN = re.compile(
    r"""\s*(?:
        (?P<iff>    ↔  | <-> | <=>        )  |
        (?P<impl>   →  | ->  | =>         )  |
        (?P<or>     ∨  | \|  | \bor\b | \bOR\b  )  |
        (?P<and>    ∧  | &   | \band\b | \bAND\b )  |
        (?P<not>    ¬  | ~   | ! | \bnot\b | \bNOT\b )  |
        (?P<lparen> \(                    )  |
        (?P<rparen> \)                    )  |
        (?P<var>    [A-Za-z][A-Za-z0-9_]*)  |
        (?P<bad>    \S                    )
    )""",
    re.VERBOSE,
)


def _tokenize(text: str) -> list[tuple[str, str]]:
    tokens = []
    for m in _TOKEN.finditer(text):
        kind = m.lastgroup
        val  = m.group().strip()
        if kind == "bad":
            raise SyntaxError(f"Unexpected character: {val!r}")
        tokens.append((kind, val))
    return tokens


# ── Recursive-descent parser ───────────────────────────────────────────────────
#
#  Grammar (operators listed lowest → highest precedence):
#    expr   ::= iff
#    iff    ::= impl  ( IFF  impl  )*        (left-associative)
#    impl   ::= disj  ( IMPL disj  )*        (right-associative)
#    disj   ::= conj  ( OR   conj  )*        (left-associative)
#    conj   ::= neg   ( AND  neg   )*        (left-associative)
#    neg    ::= NOT neg  |  atom
#    atom   ::= VAR  |  LPAREN expr RPAREN

class _Parser:
    def __init__(self, tokens: list[tuple[str, str]]) -> None:
        self._tokens = tokens
        self._pos    = 0

    def _peek(self) -> tuple[str, str]:
        return self._tokens[self._pos] if self._pos < len(self._tokens) else ("eof", "")

    def _consume(self, kind: str | None = None) -> tuple[str, str]:
        tok = self._peek()
        if kind and tok[0] != kind:
            raise SyntaxError(f"Expected {kind!r}, got {tok!r}")
        self._pos += 1
        return tok

    def parse(self) -> Any:
        node = self._expr()
        if self._peek()[0] != "eof":
            raise SyntaxError(f"Unexpected token after expression: {self._peek()!r}")
        return node

    def _expr(self) -> Any:
        return self._iff()

    def _iff(self) -> Any:
        left = self._impl()
        while self._peek()[0] == "iff":
            self._consume("iff")
            left = Iff(left, self._impl())
        return left

    def _impl(self) -> Any:
        left = self._disj()
        if self._peek()[0] == "impl":
            self._consume("impl")
            return Implies(left, self._impl())   # right-associative
        return left

    def _disj(self) -> Any:
        left = self._conj()
        while self._peek()[0] == "or":
            self._consume("or")
            left = Or(left, self._conj())
        return left

    def _conj(self) -> Any:
        left = self._neg()
        while self._peek()[0] == "and":
            self._consume("and")
            left = And(left, self._neg())
        return left

    def _neg(self) -> Any:
        if self._peek()[0] == "not":
            self._consume("not")
            return Not(self._neg())
        return self._atom()

    def _atom(self) -> Any:
        kind, val = self._peek()
        if kind == "var":
            self._consume("var")
            return Var(val)
        if kind == "lparen":
            self._consume("lparen")
            node = self._expr()
            self._consume("rparen")
            return node
        raise SyntaxError(f"Expected a variable or '(', got {self._peek()!r}")


def _parse(text: str) -> Any:
    return _Parser(_tokenize(text)).parse()


# ── CNF detection ──────────────────────────────────────────────────────────────

def _is_literal(node: Any) -> bool:
    return (
        isinstance(node, Var)
        or (isinstance(node, Not) and isinstance(node.child, Var))
    )

def _is_clause(node: Any) -> bool:
    return _is_literal(node) or (
        isinstance(node, Or) and _is_clause(node.left) and _is_clause(node.right)
    )

def _is_cnf(node: Any) -> bool:
    return _is_clause(node) or (
        isinstance(node, And) and _is_cnf(node.left) and _is_cnf(node.right)
    )


# ── Direct CNF extraction (no auxiliary variables) ─────────────────────────────

def _collect_vars_from_cnf(node: Any, var_map: dict[str, int]) -> None:
    """Walk a CNF AST and register every variable name in var_map."""
    if isinstance(node, (Var,)):
        if node.name not in var_map:
            var_map[node.name] = len(var_map) + 1
    elif isinstance(node, Not):
        _collect_vars_from_cnf(node.child, var_map)
    else:
        _collect_vars_from_cnf(node.left, var_map)
        _collect_vars_from_cnf(node.right, var_map)


def _clause_to_lits(node: Any, var_map: dict[str, int]) -> list[int]:
    """Flatten an OR-tree of literals into a list of DIMACS integers."""
    if isinstance(node, Var):
        return [var_map[node.name]]
    if isinstance(node, Not):
        return [-var_map[node.child.name]]
    if isinstance(node, Or):
        return _clause_to_lits(node.left, var_map) + _clause_to_lits(node.right, var_map)
    raise ValueError(f"Not a literal or clause: {node}")


def _extract_clauses(node: Any, var_map: dict[str, int]) -> list[list[int]]:
    """Collect all clauses from an AND-tree."""
    if _is_clause(node):
        return [_clause_to_lits(node, var_map)]
    # isinstance(node, And)
    return _extract_clauses(node.left, var_map) + _extract_clauses(node.right, var_map)


def _direct_cnf(ast: Any) -> tuple[dict[str, int], list[list[int]]]:
    var_map: dict[str, int] = {}
    _collect_vars_from_cnf(ast, var_map)
    clauses = _extract_clauses(ast, var_map)
    return var_map, clauses


# ── Tseitin transformation ─────────────────────────────────────────────────────
#
#  For each compound sub-formula F, introduce a fresh variable t_F and add
#  clauses that encode  t_F ↔ F.  Assert the root t_root by a unit clause.
#
#  Clause definitions (t is the fresh var for the sub-formula):
#
#    t ↔ ¬A          →  [¬t, ¬A]  [t, A]
#    t ↔ (A ∨ B)     →  [¬t, A, B]  [t, ¬A]  [t, ¬B]
#    t ↔ (A ∧ B)     →  [¬t, A]  [¬t, B]  [t, ¬A, ¬B]
#    t ↔ (A → B)     →  [¬t, ¬A, B]  [t, A]  [t, ¬B]
#    t ↔ (A ↔ B)     →  [¬t, ¬A, B]  [¬t, A, ¬B]  [t, A, B]  [t, ¬A, ¬B]

def _tseitin(ast: Any) -> tuple[dict[str, int], list[list[int]]]:
    var_map:   dict[str, int] = {}
    clauses:   list[list[int]] = []
    next_id  = [0]   # mutated in closure

    # ── First pass: register user variables in encounter order ──────────────
    def _collect(node: Any) -> None:
        if isinstance(node, Var):
            if node.name not in var_map:
                var_map[node.name] = 0          # placeholder
        elif isinstance(node, Not):
            _collect(node.child)
        elif isinstance(node, (And, Or, Implies, Iff)):
            _collect(node.left)
            _collect(node.right)

    _collect(ast)
    for i, name in enumerate(var_map, start=1):
        var_map[name] = i
    next_id[0] = len(var_map) + 1              # auxiliary IDs start here

    def _alloc() -> int:
        idx = next_id[0]
        next_id[0] += 1
        return idx

    # ── Recursive Tseitin walk — returns the literal for this node ──────────
    def _walk(node: Any) -> int:
        if isinstance(node, Var):
            return var_map[node.name]

        if isinstance(node, Not):
            c = _walk(node.child)
            # Literal-level negation: no auxiliary needed
            if isinstance(node.child, Var):
                return -c
            t = _alloc()
            clauses.append([-t, -c])            # t → ¬c
            clauses.append([ t,  c])            # ¬c → t
            return t

        if isinstance(node, Or):
            a, b = _walk(node.left), _walk(node.right)
            t = _alloc()
            clauses.append([-t,  a,  b])        # t → (a ∨ b)
            clauses.append([ t, -a])            # a → t
            clauses.append([ t, -b])            # b → t
            return t

        if isinstance(node, And):
            a, b = _walk(node.left), _walk(node.right)
            t = _alloc()
            clauses.append([-t,  a])            # t → a
            clauses.append([-t,  b])            # t → b
            clauses.append([ t, -a, -b])        # (a ∧ b) → t
            return t

        if isinstance(node, Implies):
            # A → B  ≡  ¬A ∨ B
            a, b = _walk(node.left), _walk(node.right)
            t = _alloc()
            clauses.append([-t, -a,  b])        # t → (¬a ∨ b)
            clauses.append([ t,  a])            # ¬a → t
            clauses.append([ t, -b])            # b → t
            return t

        if isinstance(node, Iff):
            # A ↔ B  ≡  (¬A ∨ B) ∧ (A ∨ ¬B)
            a, b = _walk(node.left), _walk(node.right)
            t = _alloc()
            clauses.append([-t, -a,  b])        # t → (¬a ∨ b)
            clauses.append([-t,  a, -b])        # t → (a ∨ ¬b)
            clauses.append([ t,  a,  b])        # ¬t → (a ∨ b)
            clauses.append([ t, -a, -b])        # ¬t → (¬a ∨ ¬b)
            return t

        raise TypeError(f"Unknown AST node: {type(node)}")

    root = _walk(ast)
    clauses.append([root])                      # assert the whole formula is true
    return var_map, clauses


# ── DIMACS output ──────────────────────────────────────────────────────────────

def to_dimacs(formula: str) -> str:
    """
    Convert *formula* (a string) to a DIMACS CNF string.

    Returns a multi-line string ready to be written to a .cnf file or fed
    directly to any DIMACS-compatible SAT solver.
    """
    ast = _parse(formula.strip())

    if _is_cnf(ast):
        method   = "direct (formula is already in CNF)"
        var_map, clauses = _direct_cnf(ast)
    else:
        method   = "Tseitin transformation (equisatisfiable)"
        var_map, clauses = _tseitin(ast)

    num_vars    = max((abs(lit) for cl in clauses for lit in cl), default=0)
    num_clauses = len(clauses)

    lines: list[str] = [
        f"c Generated by formula_to_dimacs.py",
        f"c Formula : {formula.strip()}",
        f"c Method  : {method}",
        f"c",
        f"c Variable mapping (name → DIMACS integer):",
    ]
    for name, vid in sorted(var_map.items(), key=lambda kv: kv[1]):
        lines.append(f"c   {vid:>3}  =  {name}")
    lines.append(f"c")
    lines.append(f"p cnf {num_vars} {num_clauses}")
    for clause in clauses:
        lines.append(" ".join(map(str, clause)) + " 0")

    return "\n".join(lines)


# ── CLI ────────────────────────────────────────────────────────────────────────

def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__)
        print("Usage:")
        print("  python formula_to_dimacs.py \"(A ∨ ¬B) ∧ (¬A ∨ C)\"")
        print("  python formula_to_dimacs.py --test")
        sys.exit(0)

    if sys.argv[1] == "--test":
        _run_tests()
        return

    formula = " ".join(sys.argv[1:])
    print(to_dimacs(formula))


# ── Self-tests ─────────────────────────────────────────────────────────────────

def _run_tests() -> None:
    cases = [
        # (description, formula, expected properties)
        (
            "Already-CNF: (A ∨ ¬B) ∧ (¬A ∨ C)",
            "(A ∨ ¬B) ∧ (¬A ∨ C)",
            {"method": "direct", "num_vars": 3, "num_clauses": 2},
        ),
        (
            "Single variable",
            "A",
            {"method": "direct", "num_vars": 1, "num_clauses": 1},
        ),
        (
            "Simple negation",
            "¬A",
            {"method": "direct", "num_vars": 1, "num_clauses": 1},
        ),
        (
            "Implication (needs Tseitin)",
            "A → B",
            {"method": "tseitin"},
        ),
        (
            "Biconditional (needs Tseitin)",
            "A ↔ B",
            {"method": "tseitin"},
        ),
        (
            "Nested: (A → B) ∧ (B → C)",
            "(A → B) ∧ (B → C)",
            {"method": "tseitin"},
        ),
        (
            "ASCII operators: (A | !B) & (!A | C)",
            "(A | !B) & (!A | C)",
            {"method": "direct", "num_vars": 3, "num_clauses": 2},
        ),
        (
            "Word operators: (A or B) and (not A or C)",
            "(A or B) and (not A or C)",
            {"method": "direct", "num_vars": 3, "num_clauses": 2},
        ),
        (
            "Three-literal clause: A ∨ B ∨ C",
            "A ∨ B ∨ C",
            {"method": "direct", "num_vars": 3, "num_clauses": 1},
        ),
        (
            "UNSAT: A ∧ ¬A",
            "A ∧ ¬A",
            {"method": "direct", "num_vars": 1, "num_clauses": 2},
        ),
    ]

    passed = 0
    for desc, formula, props in cases:
        try:
            result = to_dimacs(formula)
            lines  = result.splitlines()
            p_line = next(l for l in lines if l.startswith("p cnf"))
            _, _, nv, nc = p_line.split()

            ok = True
            if "num_vars"    in props and int(nv) != props["num_vars"]:
                print(f"FAIL  {desc}")
                print(f"      expected num_vars={props['num_vars']}, got {nv}")
                ok = False
            if "num_clauses" in props and int(nc) != props["num_clauses"]:
                print(f"FAIL  {desc}")
                print(f"      expected num_clauses={props['num_clauses']}, got {nc}")
                ok = False
            if "method" in props:
                method_line = next((l for l in lines if "Method" in l), "")
                if props["method"] not in method_line.lower():
                    print(f"FAIL  {desc}")
                    print(f"      expected method to contain {props['method']!r}: {method_line}")
                    ok = False
            if ok:
                print(f"ok    {desc}")
                passed += 1
        except Exception as exc:
            print(f"ERROR {desc}: {exc}")

    print(f"\n{passed}/{len(cases)} tests passed.")


if __name__ == "__main__":
    main()
