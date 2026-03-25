"""
Operator Precedence parser – builds the precedence relation table
from an operator grammar.

An operator grammar has no ε-productions and no two adjacent
non-terminals in any production RHS.

Relations:
  a ≐ b   if …ab… or …aNb… appears in some production RHS
  a ⋖ b   if b ∈ FIRSTTERM(B) and …aB… appears in some RHS
  a ⋗ b   if a ∈ LASTTERM(A) and …Ab… appears in some RHS
"""
from core.grammar import Grammar


# ------------------------------------------------------------------ #
#  FIRSTTERM / LASTTERM                                               #
# ------------------------------------------------------------------ #
def compute_firstterm(grammar: Grammar) -> dict[str, set[str]]:
    """FIRSTTERM(A) = set of terminals that can appear as the first
    terminal in a string derived from A.

    Rules:
      1. A -> a...        =>  a ∈ FIRSTTERM(A)
      2. A -> B...        =>  FIRSTTERM(B) ⊆ FIRSTTERM(A)
      3. A -> Ba...       =>  a ∈ FIRSTTERM(A)  (NT then terminal)
    """
    ft: dict[str, set[str]] = {nt: set() for nt in grammar.non_terminals}

    changed = True
    while changed:
        changed = False
        for lhs, rhs in grammar.productions:
            before = len(ft[lhs])

            for i, sym in enumerate(rhs):
                if sym in grammar.terminals:
                    # Rule 1: terminal found — add it and stop
                    ft[lhs].add(sym)
                    break
                elif sym in grammar.non_terminals:
                    # Rule 2: add FIRSTTERM of this NT
                    ft[lhs] |= ft[sym]
                    # Rule 3: if next symbol is a terminal, add it too
                    if i + 1 < len(rhs) and rhs[i + 1] in grammar.terminals:
                        ft[lhs].add(rhs[i + 1])
                    # In operator grammars, NTs can't derive ε, so stop
                    break

            if len(ft[lhs]) > before:
                changed = True

    return ft


def compute_lastterm(grammar: Grammar) -> dict[str, set[str]]:
    """LASTTERM(A) = set of terminals that can appear as the last
    terminal in a string derived from A.

    Rules:
      1. A -> ...a        =>  a ∈ LASTTERM(A)
      2. A -> ...B        =>  LASTTERM(B) ⊆ LASTTERM(A)
      3. A -> ...aB       =>  a ∈ LASTTERM(A)  (terminal then NT)
    """
    lt: dict[str, set[str]] = {nt: set() for nt in grammar.non_terminals}

    changed = True
    while changed:
        changed = False
        for lhs, rhs in grammar.productions:
            before = len(lt[lhs])

            for i in range(len(rhs) - 1, -1, -1):
                sym = rhs[i]
                if sym in grammar.terminals:
                    # Rule 1: terminal found — add it and stop
                    lt[lhs].add(sym)
                    break
                elif sym in grammar.non_terminals:
                    # Rule 2: add LASTTERM of this NT
                    lt[lhs] |= lt[sym]
                    # Rule 3: if previous symbol is a terminal, add it too
                    if i - 1 >= 0 and rhs[i - 1] in grammar.terminals:
                        lt[lhs].add(rhs[i - 1])
                    # In operator grammars, NTs can't derive ε, so stop
                    break

            if len(lt[lhs]) > before:
                changed = True

    return lt


# ------------------------------------------------------------------ #
#  Validation                                                         #
# ------------------------------------------------------------------ #
def validate_operator_grammar(grammar: Grammar) -> list[str]:
    """Check that grammar is a valid operator grammar.
    Returns a list of error messages (empty = valid)."""
    errors: list[str] = []

    for lhs, rhs in grammar.productions:
        # No ε-productions
        if rhs == [Grammar.EPSILON]:
            errors.append(f"ε-production found: {lhs} → ε")
            continue

        # No two adjacent non-terminals
        for i in range(len(rhs) - 1):
            if rhs[i] in grammar.non_terminals and rhs[i + 1] in grammar.non_terminals:
                errors.append(
                    f"Adjacent non-terminals in: {lhs} → {' '.join(rhs)} "
                    f"({rhs[i]} and {rhs[i+1]})"
                )

    return errors


# ------------------------------------------------------------------ #
#  Precedence table                                                   #
# ------------------------------------------------------------------ #
def build_op_table(grammar: Grammar):
    """
    Build the operator precedence relation table.

    Parameters
    ----------
    grammar : Grammar
        Must be a valid operator grammar (call validate first or this will).

    Returns
    -------
    prec_table : dict[(str, str), str]
        Maps (terminal_a, terminal_b) → one of '<', '=', '>' or None.
    firstterm  : dict[str, set[str]]
    lastterm   : dict[str, set[str]]
    conflicts  : list[str]
    errors     : list[str]  (grammar validation errors, if any)
    """
    errors = validate_operator_grammar(grammar)
    if errors:
        return {}, {}, {}, [], errors

    firstterm = compute_firstterm(grammar)
    lastterm = compute_lastterm(grammar)

    prec_table: dict[tuple[str, str], str] = {}
    conflicts: list[str] = []
    terminals = sorted(grammar.terminals | {"$"})

    def _set_relation(a: str, b: str, rel: str):
        key = (a, b)
        existing = prec_table.get(key)
        if existing is not None and existing != rel:
            conflicts.append(
                f"Conflict between '{a}' and '{b}': "
                f"both '{existing}' and '{rel}'"
            )
        else:
            prec_table[key] = rel

    for lhs, rhs in grammar.productions:
        n = len(rhs)
        for i in range(n - 1):
            xi = rhs[i]
            xi1 = rhs[i + 1]

            # Case 1: xi and xi+1 are both terminals → xi ≐ xi+1
            if xi in grammar.terminals and xi1 in grammar.terminals:
                _set_relation(xi, xi1, "=")

            # Case 2: xi terminal, xi+1 non-terminal
            if xi in grammar.terminals and xi1 in grammar.non_terminals:
                # xi ⋖ b for all b in FIRSTTERM(xi+1)
                for b in firstterm[xi1]:
                    _set_relation(xi, b, "<")

            # Case 3: xi non-terminal, xi+1 terminal
            if xi in grammar.non_terminals and xi1 in grammar.terminals:
                # a ⋗ xi+1 for all a in LASTTERM(xi)
                for a in lastterm[xi]:
                    _set_relation(a, xi1, ">")

            # Case 4: xi terminal, xi+1 non-terminal, xi+2 terminal (i+2 < n)
            if i + 2 < n:
                xi2 = rhs[i + 2]
                if (xi in grammar.terminals and
                        xi1 in grammar.non_terminals and
                        xi2 in grammar.terminals):
                    _set_relation(xi, xi2, "=")

    # Add $ boundary relations:
    # $ ⋖ b for every terminal b in the grammar
    # a ⋗ $ for every terminal a in the grammar
    # This ensures the parser can handle all tokens at start/end of input
    for t in grammar.terminals:
        _set_relation("$", t, "<")
        _set_relation(t, "$", ">")

    return prec_table, firstterm, lastterm, conflicts, errors
