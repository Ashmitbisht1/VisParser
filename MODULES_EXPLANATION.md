# ParserVis – Module & Component Explanation

This document provides a detailed breakdown of every module and key function in the `ParserVis` project, helping you understand how the application handles grammar parsing and visualization.

---

## 🏗️ Core Architecture Overview

ParserVis is split into three main packages:
1. **`core/`** – Data structures and algorithms for grammars (FIRST/FOLLOW sets, parsing simulation).
2. **`parsers/`** – Specific implementations of parsing table builders for LR(0), SLR(1), CLR(1), LALR(1), and Operator Precedence.
3. **`gui/`** – The user interface built using Tkinter and `ttkbootstrap` for managing user interactions, animations, and visualization components.

---

## 1. 🧩 `core/` Module

The `core/` module is the backbone of the application. It models formal grammars and simulates the actual shift-reduce parsing process.

### `core/grammar.py`
This module models the user input as a formal Context-Free Grammar (CFG).
- **`Grammar` class**: Represents the CFG. It tracks terminals, non-terminals, the start symbol, and a dictionary of productions.
  - `from_text(text)`: Parses user string input into a `Grammar` object. Detects nullable productions (epsilon).
  - `augment()`: Adds the augmented start symbol (`S' -> S`) necessary for LR parsing to detect the `ACCEPT` state.

### `core/first_follow.py`
Computes the FIRST and FOLLOW sets, which are critical for determining lookaheads in SLR(1), CLR(1), and LALR(1) parsers.
- **`compute_first(grammar)`**: Iteratively calculates the FIRST sets for all symbols (terminals compute to themselves, non-terminals trace down to their starting terminals).
- **`compute_follow(grammar, first_sets)`**: Uses the FIRST sets to calculate the FOLLOW sets. It guarantees the augmented start symbol gets `$` (end-of-file), and applies subset rules based on grammar productions.

### `core/parser_engine.py` & `core/op_parser_engine.py`
These files are the actual simulation engines that execute the shift-reduce parsing algorithm for a given input string.
- **`parse_string(action_table, goto_table, grammar, input_string)`**: The generic LR parsing loop. It initializes a stack with `State 0`, consumes tokens from the `input_string`, and uses the ACTION/GOTO tables to execute `shift`, `reduce`, or `accept`. It yields steps used by the UI for animation.
- **`op_parse_string(prec_table, grammar, input_string)`**: Similar to `parse_string` but tailored specifically for Operator Precedence parsing, utilizing relation matrices (`<`, `>`, `=`) to drive reductions.

---

## 2. ⚙️ `parsers/` Module

Contains the algorithms to generate parsing tables based on the canonical collection of items.

### `parsers/lr_base.py`
Provides the base utilities shared across all LR parsers.
- **`LR1Item` class**: Represents a production in process, e.g., `A -> α • β, lookahead`.
- **`closure(...)`**: Expands a set of items by including items for non-terminals immediately after the dot.
- **`goto(...)`**: Computes the transition from an item set to the next given a grammar symbol.
- **`canonical_collection(...)`**: Discovers all unique states (item sets) and transitions, returning the state diagram graph.

### `parsers/lr0.py`, `parsers/slr1.py`, `parsers/clr1.py`, `parsers/lalr1.py`
Each of these files is responsible for generating its respective parsing table.
- **`build_lr0_table(...)`**: Very basic, places reduces across all terminals. Highly susceptible to conflicts.
- **`build_slr1_table(...)`**: Uses the FOLLOW sets to place reduces more carefully than LR(0), avoiding some shift-reduce conflicts.
- **`build_clr1_table(...)`**: The most powerful standard parser. Computes specific lookaheads (first of what follows) inside items. Reduces are only placed for exact lookaheads.
- **`build_lalr1_table(...)`**: Merges states in CLR(1) that have identical cores but different lookaheads. Reduces table size but may introduce reduce-reduce conflicts.
- **Returns:** Action table, Goto table, List of states, List of transitions, List of conflicts.

### `parsers/operator_precedence.py`
Builds precedence relation matrices without requiring item sets.
- **`build_op_table(...)`**: Computes FIRSTTERM and LASTTERM to generate `<`, `>`, and `=` relations.
- **`validate_operator_grammar(...)`**: Verifies that the grammar contains no epsilon rules and no adjacent non-terminals.

---

## 3. 🖼️ `gui/` Module

Manages the visual presentation layer. It utilizes `ttkbootstrap` for styling.

### `gui/app.py`
The orchestrator. It manages the main application window and global state.
- **`ParserVisApp` class**: Owns the root window, connects UI events to core logic (like clicking "Build Automaton").
- **`_on_build(grammar_text)`**: Triggered by user input. Orchestrates table generation and schedules phased animations of the graph drawing.
- **`_on_parse(input_str)`**: Calls the engine, initiates the staged step-by-step animation of parsing string evaluation.

### `gui/input_panel.py`
The left pane where the user interacts.
- **`InputPanel` class**: Provides text input for the grammar and displays mathematical results (Augmented Grammar, FIRST/FOLLOW sets). Connects to external logic via callbacks.

### `gui/graph_panel.py`
The dynamic middle pane.
- **`GraphPanel` class**: Split into a Canvas for drawing the state diagram and a Treeview for drawing the parsing tables.
- **`draw_states(...)`**: Maps state structures to (x,y) coordinates on the canvas, drawing boxes and transition arrows.
- **`show_table(...)`**: Transforms the ACTION and GOTO rules into a clean grid view. Colors accept fields green and conflicts red.

### `gui/output_panel.py`
The right pane handling the string validation process.
- **`OutputPanel` class**: Handles user inputs to test specific strings.
- **`add_step(...)` & `update_visual_stack(...)`**: Pushes the current context of the stack to the UI. The visual stack is rendered using colored blocks.

---

### End Summary
With this separation, ParserVis maintains a pristine distinction between UI layout (GUI), compilation logic (Core), and parsing data structures (Parsers), making it an easy-to-reason-about architecture.
