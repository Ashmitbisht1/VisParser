"""
FIRST and FOLLOW set computation for a context-free grammar.
"""
from core.grammar import Grammar


def compute_first(grammar: Grammar) -> dict:
    """
    Compute FIRST sets for every symbol in the grammar.
    Returns Dict[str, Set[str]].
    """
    first = {s: set() for s in grammar.symbols}
    # Terminals: FIRST(a) = {a}
    for t in grammar.terminals:
        first[t] = {t}

    changed = True
    while changed:
        changed = False
        for lhs, rhs in grammar.productions:
            before = len(first[lhs])

            if rhs == [Grammar.EPSILON]:
                first[lhs].add(Grammar.EPSILON)
            else:
                for symbol in rhs:
                    # Add FIRST(symbol) - {ε} to FIRST(lhs)
                    first[lhs] |= (first.get(symbol, set()) - {Grammar.EPSILON})
                    if Grammar.EPSILON not in first.get(symbol, set()):
                        break
                else:
                    # All symbols can derive ε
                    first[lhs].add(Grammar.EPSILON)

            if len(first[lhs]) > before:
                changed = True

    return first


def first_of_string(symbols: list, first: dict) -> set:
    """Compute FIRST of a string of grammar symbols."""
    result = set()
    for symbol in symbols:
        result |= (first.get(symbol, {symbol}) - {Grammar.EPSILON})
        if Grammar.EPSILON not in first.get(symbol, {symbol}):
            break
    else:
        result.add(Grammar.EPSILON)
    return result


def compute_follow(grammar: Grammar, first: dict) -> dict:
    """
    Compute FOLLOW sets for every non-terminal.
    Returns Dict[str, Set[str]].
    """
    follow = {nt: set() for nt in grammar.non_terminals}
    follow[grammar.start_symbol].add("$")

    changed = True
    while changed:
        changed = False
        for lhs, rhs in grammar.productions:
            for i, symbol in enumerate(rhs):
                if symbol not in grammar.non_terminals:
                    continue

                before = len(follow[symbol])

                # β = rhs[i+1:]
                beta = rhs[i + 1:]
                if beta:
                    first_beta = first_of_string(beta, first)
                    follow[symbol] |= (first_beta - {Grammar.EPSILON})

                    if Grammar.EPSILON in first_beta:
                        follow[symbol] |= follow[lhs]
                else:
                    # Symbol is at the end of the production
                    follow[symbol] |= follow[lhs]

                if len(follow[symbol]) > before:
                    changed = True

    return follow
