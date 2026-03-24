"""
LALR(1) parser – merges CLR(1) states with the same core.
"""
from core.grammar import Grammar
from core.first_follow import compute_first, compute_follow
from parsers.lr_base import (
    lr1_canonical_collection, LR1Item, core_of,
)


def build_lalr1_table(grammar: Grammar):
    """
    Build LALR(1) ACTION and GOTO tables by merging CLR(1) states
    that share the same core (prod_index, dot_pos pairs).

    Returns
    -------
    action_table : dict[int, dict[str, tuple]]
    goto_table   : dict[int, dict[str, int]]
    merged_states : list of frozenset[LR1Item]
    merged_transitions : dict[(int, str), int]
    conflicts    : list of str
    first_sets   : dict
    follow_sets  : dict
    """
    first_sets = compute_first(grammar)
    follow_sets = compute_follow(grammar, first_sets)

    clr_states, clr_transitions = lr1_canonical_collection(grammar, first_sets)

    # ---------------------------------------------------------------- #
    #  Merge states with the same core                                  #
    # ---------------------------------------------------------------- #
    core_map = {}          # core -> merge_index
    merge_mapping = {}     # old_index -> merge_index
    merged_states = []

    for i, state in enumerate(clr_states):
        c = core_of(state)
        if c in core_map:
            merge_idx = core_map[c]
            # Union the lookaheads
            merged_states[merge_idx] = _merge_item_sets(merged_states[merge_idx], state)
            merge_mapping[i] = merge_idx
        else:
            merge_idx = len(merged_states)
            core_map[c] = merge_idx
            merge_mapping[i] = merge_idx
            merged_states.append(state)

    # Remap transitions
    merged_transitions = {}
    for (old_state, symbol), old_target in clr_transitions.items():
        new_key = (merge_mapping[old_state], symbol)
        new_target = merge_mapping[old_target]
        merged_transitions[new_key] = new_target

    # ---------------------------------------------------------------- #
    #  Build tables from merged states                                  #
    # ---------------------------------------------------------------- #
    action_table = {}
    goto_table = {}
    conflicts = []

    for i in range(len(merged_states)):
        action_table[i] = {}
        goto_table[i] = {}

    for (state, symbol), target in merged_transitions.items():
        if symbol in grammar.terminals:
            _set_action(action_table, state, symbol, ("shift", target), conflicts, grammar)
        elif symbol in grammar.non_terminals:
            goto_table[state][symbol] = target

    for i, item_set in enumerate(merged_states):
        for item in item_set:
            lhs, rhs = grammar.productions[item.prod_index]

            if item.dot_pos >= len(rhs) or (rhs == [Grammar.EPSILON] and item.dot_pos == 0):
                if item.prod_index == 0:
                    _set_action(action_table, i, "$", ("accept",), conflicts, grammar)
                else:
                    _set_action(action_table, i, item.lookahead,
                                ("reduce", item.prod_index), conflicts, grammar)

    return action_table, goto_table, merged_states, merged_transitions, conflicts, first_sets, follow_sets


def _merge_item_sets(set_a: frozenset, set_b: frozenset) -> frozenset:
    """Merge two LR(1) item sets: unify lookaheads for items with the same core."""
    items = {}
    for item in set_a | set_b:
        key = (item.prod_index, item.dot_pos)
        if key not in items:
            items[key] = set()
        items[key].add(item.lookahead)

    merged = set()
    for (pi, dp), las in items.items():
        for la in las:
            merged.add(LR1Item(pi, dp, la))
    return frozenset(merged)


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
