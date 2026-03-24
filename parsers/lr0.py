"""
LR(0) parser – builds the LR(0) automaton and ACTION/GOTO tables.
"""
from core.grammar import Grammar
from parsers.lr_base import lr0_canonical_collection, LR0Item


def build_lr0_table(grammar: Grammar):
    """
    Build LR(0) ACTION and GOTO tables.

    In LR(0), reduce actions are placed for ALL terminals (no lookahead).

    Returns
    -------
    action_table : dict[int, dict[str, tuple]]
    goto_table   : dict[int, dict[str, int]]
    states       : list of frozenset[LR0Item]
    transitions  : dict[(int, str), int]
    conflicts    : list of str (conflict descriptions)
    """
    states, transitions = lr0_canonical_collection(grammar)
    action_table = {}
    goto_table = {}
    conflicts = []

    all_terminals = grammar.terminals | {"$"}

    for i, item_set in enumerate(states):
        action_table[i] = {}
        goto_table[i] = {}

    # Fill SHIFT and GOTO from transitions
    for (state, symbol), target in transitions.items():
        if symbol in grammar.terminals:
            _set_action(action_table, state, symbol, ("shift", target), conflicts, grammar)
        elif symbol in grammar.non_terminals:
            goto_table[state][symbol] = target

    # Fill REDUCE for completed items
    for i, item_set in enumerate(states):
        for item in item_set:
            lhs, rhs = grammar.productions[item.prod_index]

            # Check if dot is at the end
            if item.dot_pos >= len(rhs) or (rhs == [Grammar.EPSILON] and item.dot_pos == 0):
                if item.prod_index == 0:
                    # Accept
                    _set_action(action_table, i, "$", ("accept",), conflicts, grammar)
                else:
                    # LR(0): reduce on ALL terminals
                    for t in all_terminals:
                        _set_action(action_table, i, t, ("reduce", item.prod_index), conflicts, grammar)

    return action_table, goto_table, states, transitions, conflicts


def _set_action(action_table, state, symbol, action, conflicts, grammar):
    """Set an action entry, recording conflicts if one already exists."""
    existing = action_table[state].get(symbol)
    if existing is not None and existing != action:
        # Determine conflict type
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
        # Keep the first action (shift takes priority for display)
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
