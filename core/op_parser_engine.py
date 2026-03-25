"""
Operator Precedence parsing engine.
Stack-based shift-reduce parser driven by a precedence relation table.

Yields (stack_display, remaining_input, action_display) tuples
exactly like the LR parser_engine, so the same GUI animation works.
"""
from core.grammar import Grammar


def op_parse_string(prec_table, grammar: Grammar, input_string: str):
    """
    Parse *input_string* using operator-precedence relations.

    Parameters
    ----------
    prec_table : dict[(str, str), str]
        Precedence relations: '<', '=', '>'.
    grammar : Grammar
        The grammar (NOT augmented — the original operator grammar).
    input_string : str
        Space-separated tokens, e.g. "id + id * id".

    Yields
    ------
    (stack_display, remaining_input, action_display) tuples.
    """
    terminals = grammar.terminals | {"$"}
    tokens = input_string.strip().split() + ["$"]
    # The stack holds interleaved terminals and non-terminals.
    stack: list[str] = ["$"]
    pointer = 0

    max_steps = 200  # safety guard against infinite loops

    for _ in range(max_steps):
        remaining = " ".join(tokens[pointer:])

        # Find the topmost terminal on the stack
        top_terminal = _topmost_terminal(stack, terminals)
        current_token = tokens[pointer]

        stack_display = " ".join(stack)

        # Check for acceptance: stack is $ NT and input is $
        if top_terminal == "$" and current_token == "$":
            # Stack should be ["$", NonTerminal]
            if len(stack) == 2 and stack[1] not in terminals:
                yield (stack_display, remaining, "ACCEPT")
                return
            elif len(stack) == 1:
                yield (stack_display, remaining, "ERROR: empty stack, unexpected $")
                return
            else:
                # Force a reduction
                handle, success = _find_handle(stack, prec_table, terminals)
                if not success or not handle:
                    yield (stack_display, remaining,
                           "ERROR: cannot find handle for reduction at end of input")
                    return
                handle_str = " ".join(handle)
                lhs = _match_production(handle, grammar)
                if lhs is None:
                    yield (stack_display, remaining,
                           f"ERROR: no production matches handle '{handle_str}'")
                    return
                yield (stack_display, remaining, f"Reduce {handle_str} to {lhs}")
                for _ in range(len(handle)):
                    stack.pop()
                stack.append(lhs)
                continue

        # Look up the precedence relation
        rel = prec_table.get((top_terminal, current_token))

        if rel is None:
            yield (stack_display, remaining,
                   f"ERROR: no precedence relation between '{top_terminal}' and '{current_token}'")
            return

        if rel == "<" or rel == "=":
            # Shift
            action_str = f"Shift {current_token}"
            yield (stack_display, remaining, action_str)
            stack.append(current_token)
            pointer += 1

        elif rel == ">":
            # Reduce: find the handle
            handle, success = _find_handle(stack, prec_table, terminals)
            if not success or not handle:
                yield (stack_display, remaining,
                       "ERROR: cannot find handle for reduction")
                return

            handle_str = " ".join(handle)

            # Find which production matches this handle
            lhs = _match_production(handle, grammar)
            if lhs is None:
                yield (stack_display, remaining,
                       f"ERROR: no production matches handle '{handle_str}'")
                return

            yield (stack_display, remaining, f"Reduce {handle_str} to {lhs}")

            # Pop the handle from the stack
            for _ in range(len(handle)):
                stack.pop()

            # Push the LHS non-terminal
            stack.append(lhs)

        else:
            yield (stack_display, remaining,
                   f"ERROR: unknown relation '{rel}'")
            return

    # If we exceed max steps, something went wrong
    yield (" ".join(stack), " ".join(tokens[pointer:]),
           "ERROR: maximum parsing steps exceeded")


def _topmost_terminal(stack: list[str], terminals: set[str]) -> str:
    """Find the topmost terminal on the stack."""
    for i in range(len(stack) - 1, -1, -1):
        if stack[i] in terminals:
            return stack[i]
    return "$"


def _find_handle(stack: list[str], prec_table: dict,
                 terminals: set[str]) -> tuple[list[str], bool]:
    """
    Find the handle (rightmost sequence to reduce).
    Walk back from the top of the stack to find the '<' boundary.
    """
    # Find all terminal positions in the stack
    terminal_positions = []
    for i, sym in enumerate(stack):
        if sym in terminals:
            terminal_positions.append(i)

    if len(terminal_positions) < 1:
        return [], False

    # Walk backwards through terminal positions to find where '<' starts
    handle_start_pos = None

    for k in range(len(terminal_positions) - 1, 0, -1):
        cur_pos = terminal_positions[k]
        prev_pos = terminal_positions[k - 1]
        cur_sym = stack[cur_pos]
        prev_sym = stack[prev_pos]

        rel = prec_table.get((prev_sym, cur_sym))
        if rel == "<":
            # Handle starts at the symbol right after prev_pos
            handle_start_pos = prev_pos + 1
            break
        elif rel == "=" or rel == ">":
            continue

    if handle_start_pos is None:
        # Handle starts right after the first terminal ($)
        if terminal_positions:
            handle_start_pos = terminal_positions[0] + 1
        else:
            handle_start_pos = 1

    handle = stack[handle_start_pos:]
    if not handle:
        return [], False

    return handle, True


def _match_production(handle: list[str], grammar: Grammar) -> str | None:
    """
    Find a production A → α where α matches the handle.
    Terminals must match exactly; any non-terminal in handle
    can match any non-terminal in the production RHS.
    """
    for lhs, rhs in grammar.productions:
        if len(rhs) == len(handle):
            match = True
            for h, r in zip(handle, rhs):
                if h == r:
                    continue
                # Allow any NT to match any NT position
                if (h in grammar.non_terminals and
                        r in grammar.non_terminals):
                    continue
                match = False
                break
            if match:
                return lhs
    return None
