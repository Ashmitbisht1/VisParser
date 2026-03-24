"""
SLR(1) parser – reuses LR(0) automaton but places REDUCE
only on FOLLOW(A) terminals.
"""
from core.grammar import Grammar
from core.first_follow import compute_first, compute_follow
from parsers.lr_base import lr0_canonical_collection, LR0Item


def build_slr1_table(grammar: Grammar):
    """
    Build SLR(1) ACTION and GOTO tables.

    Returns
    -------
    action_table : dict[int, dict[str, tuple]]
    goto_table   : dict[int, dict[str, int]]
    states       : list of frozenset[LR0Item]
    transitions  : dict[(int, str), int]
    conflicts    : list of str
    first_sets   : dict
    follow_sets  : dict
    """
    first_sets = compute_first(grammar)
    follow_sets = compute_follow(grammar, first_sets)

    states, transitions = lr0_canonical_collection(grammar)
    action_table = {}
    goto_table = {}
    conflicts = []

    for i in range(len(states)):
        action_table[i] = {}
        goto_table[i] = {}

    # SHIFT and GOTO from transitions
    for (state, symbol), target in transitions.items():
        if symbol in grammar.terminals:
            _set_action(action_table, state, symbol, ("shift", target), conflicts, grammar)
        elif symbol in grammar.non_terminals:
            goto_table[state][symbol] = target

    # REDUCE only on FOLLOW(lhs)
    for i, item_set in enumerate(states):
        for item in item_set:
            lhs, rhs = grammar.productions[item.prod_index]

            if item.dot_pos >= len(rhs) or (rhs == [Grammar.EPSILON] and item.dot_pos == 0):
                if item.prod_index == 0:
                    _set_action(action_table, i, "$", ("accept",), conflicts, grammar)
                else:
                    for t in follow_sets.get(lhs, set()):
                        _set_action(action_table, i, t, ("reduce", item.prod_index), conflicts, grammar)

    return action_table, goto_table, states, transitions, conflicts, first_sets, follow_sets


def _set_action(action_table, state, symbol, action, conflicts, grammar):
    """Set an action entry with conflict detection."""
    existing = action_table[state].get(symbol)
    if existing is not None and existing != action:
        types = set()
        for a in [existing, action]:
            types.add(a[0])
        if "shift" in types and "reduce" in types:
            conflict_type = "Shift-Reduce"
        else:
            conflict_type = "Reduce-Reduce"

        conflict_msg = (
            f"{conflict_type} conflict in state {state} on symbol '{symbol}': "
            f"{_action_str(existing, grammar)} vs {_action_str(action, grammar)}"
        )
        conflicts.append(conflict_msg)
        if action[0] == "shift":
            action_table[state][symbol] = action
    else:
        action_table[state][symbol] = action


def _action_str(action, grammar):
    if action[0] == "shift":
        return f"Shift {action[1]}"
    elif action[0] == "reduce":
        return f"Reduce({grammar.production_str(action[1])})"
    elif action[0] == "accept":
        return "Accept"
    return str(action)
