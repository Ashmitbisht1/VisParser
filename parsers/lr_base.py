"""
Shared LR item types, closure, goto, and canonical collection builders.
Provides both LR(0) items and LR(1) items (with lookahead).
"""
from dataclasses import dataclass, field
from typing import FrozenSet, Tuple
from core.grammar import Grammar


# ------------------------------------------------------------------ #
#  Item types                                                         #
# ------------------------------------------------------------------ #
@dataclass(frozen=True, eq=True)
class LR0Item:
    """An LR(0) item: production index + dot position."""
    prod_index: int
    dot_pos: int

    def __repr__(self):
        return f"Item({self.prod_index}, dot={self.dot_pos})"


@dataclass(frozen=True, eq=True)
class LR1Item:
    """An LR(1) item: production index + dot position + lookahead symbol."""
    prod_index: int
    dot_pos: int
    lookahead: str

    def __repr__(self):
        return f"LR1Item({self.prod_index}, dot={self.dot_pos}, la={self.lookahead})"


# ------------------------------------------------------------------ #
#  LR(0) closure & goto                                               #
# ------------------------------------------------------------------ #
def lr0_closure(items: set, grammar: Grammar) -> frozenset:
    """Compute the LR(0) closure of a set of LR0Items."""
    closure = set(items)
    worklist = list(items)

    while worklist:
        item = worklist.pop()
        lhs, rhs = grammar.productions[item.prod_index]

        if item.dot_pos < len(rhs):
            symbol = rhs[item.dot_pos]
            if symbol in grammar.non_terminals:
                for i, (plhs, prhs) in enumerate(grammar.productions):
                    if plhs == symbol:
                        new_item = LR0Item(i, 0)
                        if new_item not in closure:
                            closure.add(new_item)
                            worklist.append(new_item)

    return frozenset(closure)


def lr0_goto(items: frozenset, symbol: str, grammar: Grammar) -> frozenset:
    """Compute GOTO(items, symbol) for LR(0)."""
    moved = set()
    for item in items:
        lhs, rhs = grammar.productions[item.prod_index]
        if item.dot_pos < len(rhs) and rhs[item.dot_pos] == symbol:
            moved.add(LR0Item(item.prod_index, item.dot_pos + 1))
    return lr0_closure(moved, grammar)


def lr0_canonical_collection(grammar: Grammar):
    """
    Build the canonical collection of LR(0) item sets.

    Returns
    -------
    states : list of frozenset[LR0Item]
    transitions : dict[(int, str)] -> int   (state_index, symbol) -> state_index
    """
    start_item = LR0Item(0, 0)  # S' -> .S
    start_state = lr0_closure({start_item}, grammar)

    states = [start_state]
    state_map = {start_state: 0}
    transitions = {}
    worklist = [0]

    while worklist:
        idx = worklist.pop()
        item_set = states[idx]

        # Collect symbols after dot
        symbols = set()
        for item in item_set:
            lhs, rhs = grammar.productions[item.prod_index]
            if item.dot_pos < len(rhs) and rhs[item.dot_pos] != Grammar.EPSILON:
                symbols.add(rhs[item.dot_pos])

        for sym in symbols:
            goto_set = lr0_goto(item_set, sym, grammar)
            if not goto_set:
                continue

            if goto_set not in state_map:
                state_map[goto_set] = len(states)
                states.append(goto_set)
                worklist.append(len(states) - 1)

            transitions[(idx, sym)] = state_map[goto_set]

    return states, transitions


# ------------------------------------------------------------------ #
#  LR(1) closure & goto                                               #
# ------------------------------------------------------------------ #
def lr1_closure(items: set, grammar: Grammar, first: dict) -> frozenset:
    """Compute the LR(1) closure of a set of LR1Items."""
    from core.first_follow import first_of_string

    closure = set(items)
    worklist = list(items)

    while worklist:
        item = worklist.pop()
        lhs, rhs = grammar.productions[item.prod_index]

        if item.dot_pos < len(rhs):
            symbol = rhs[item.dot_pos]
            if symbol in grammar.non_terminals:
                # β = rhs after dot+1, then lookahead
                beta = list(rhs[item.dot_pos + 1:]) + [item.lookahead]
                first_beta = first_of_string(beta, first)

                for i, (plhs, prhs) in enumerate(grammar.productions):
                    if plhs == symbol:
                        for la in first_beta:
                            if la != Grammar.EPSILON:
                                new_item = LR1Item(i, 0, la)
                                if new_item not in closure:
                                    closure.add(new_item)
                                    worklist.append(new_item)

    return frozenset(closure)


def lr1_goto(items: frozenset, symbol: str, grammar: Grammar, first: dict) -> frozenset:
    """Compute GOTO(items, symbol) for LR(1)."""
    moved = set()
    for item in items:
        lhs, rhs = grammar.productions[item.prod_index]
        if item.dot_pos < len(rhs) and rhs[item.dot_pos] == symbol:
            moved.add(LR1Item(item.prod_index, item.dot_pos + 1, item.lookahead))
    return lr1_closure(moved, grammar, first)


def lr1_canonical_collection(grammar: Grammar, first: dict):
    """
    Build the canonical collection of LR(1) item sets.

    Returns
    -------
    states : list of frozenset[LR1Item]
    transitions : dict[(int, str)] -> int
    """
    start_item = LR1Item(0, 0, "$")
    start_state = lr1_closure({start_item}, grammar, first)

    states = [start_state]
    state_map = {start_state: 0}
    transitions = {}
    worklist = [0]

    while worklist:
        idx = worklist.pop()
        item_set = states[idx]

        symbols = set()
        for item in item_set:
            lhs, rhs = grammar.productions[item.prod_index]
            if item.dot_pos < len(rhs) and rhs[item.dot_pos] != Grammar.EPSILON:
                symbols.add(rhs[item.dot_pos])

        for sym in symbols:
            goto_set = lr1_goto(item_set, sym, grammar, first)
            if not goto_set:
                continue

            if goto_set not in state_map:
                state_map[goto_set] = len(states)
                states.append(goto_set)
                worklist.append(len(states) - 1)

            transitions[(idx, sym)] = state_map[goto_set]

    return states, transitions


# ------------------------------------------------------------------ #
#  Item display helpers                                               #
# ------------------------------------------------------------------ #
def item_to_str(item, grammar: Grammar) -> str:
    """Return a human-readable string for an LR(0) or LR(1) item."""
    lhs, rhs = grammar.productions[item.prod_index]
    rhs_with_dot = list(rhs)
    rhs_with_dot.insert(item.dot_pos, "·")
    base = f"{lhs} -> {' '.join(rhs_with_dot)}"
    if isinstance(item, LR1Item):
        base += f", {item.lookahead}"
    return base


def core_of(item_set: frozenset) -> frozenset:
    """Extract the core (prod_index, dot_pos) from an LR(1) item set."""
    return frozenset((item.prod_index, item.dot_pos) for item in item_set)
