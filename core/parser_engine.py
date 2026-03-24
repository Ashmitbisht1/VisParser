"""
Generic stack-based shift-reduce parsing engine.
Works with any ACTION/GOTO table produced by the parser builders.
"""


def parse_string(action_table, goto_table, grammar, input_string: str):
    """
    Parse *input_string* using the given ACTION/GOTO tables and grammar.

    Parameters
    ----------
    action_table : dict
        action_table[state][terminal] = ("shift", next_state)
                                       | ("reduce", prod_index)
                                       | ("accept",)
    goto_table : dict
        goto_table[state][non_terminal] = next_state
    grammar : Grammar
        The augmented grammar used to build the tables.
    input_string : str
        Space-separated tokens, e.g. "id + id * id".

    Yields
    ------
    (stack_display, remaining_input, action_display) tuples for each step.
    The final tuple has action_display set to "ACCEPT" or "ERROR: ...".
    """
    tokens = input_string.strip().split() + ["$"]
    stack = [0]  # state stack
    symbol_stack = []  # symbol stack (for display)
    pointer = 0

    while True:
        state = stack[-1]
        current_token = tokens[pointer]

        # Build display strings
        stack_display = _format_stack(stack, symbol_stack)
        remaining = " ".join(tokens[pointer:])

        # Look up action
        action = action_table.get(state, {}).get(current_token)

        if action is None:
            yield (stack_display, remaining, f"ERROR: no action for state {state}, token '{current_token}'")
            return

        if action[0] == "shift":
            next_state = action[1]
            action_str = f"Shift {current_token}, go to state {next_state}"
            yield (stack_display, remaining, action_str)
            symbol_stack.append(current_token)
            stack.append(next_state)
            pointer += 1

        elif action[0] == "reduce":
            prod_index = action[1]
            lhs, rhs = grammar.productions[prod_index]
            rhs_len = len(rhs) if rhs != [grammar.EPSILON] else 0
            action_str = f"Reduce by {lhs} -> {' '.join(rhs)}"
            yield (stack_display, remaining, action_str)

            # Pop |rhs| symbols
            for _ in range(rhs_len):
                stack.pop()
                symbol_stack.pop()

            # Push lhs
            top_state = stack[-1]
            goto_state = goto_table.get(top_state, {}).get(lhs)
            if goto_state is None:
                yield (_format_stack(stack, symbol_stack), remaining,
                       f"ERROR: no goto for state {top_state}, non-terminal '{lhs}'")
                return

            symbol_stack.append(lhs)
            stack.append(goto_state)

        elif action[0] == "accept":
            yield (stack_display, remaining, "ACCEPT")
            return

        else:
            yield (stack_display, remaining, f"ERROR: unknown action {action}")
            return


def _format_stack(state_stack, symbol_stack):
    """Format the interleaved state/symbol stack for display."""
    parts = [str(state_stack[0])]
    for sym, st in zip(symbol_stack, state_stack[1:]):
        parts.append(str(sym))
        parts.append(str(st))
    return " ".join(parts)
