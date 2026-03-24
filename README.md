# ⟪ VisParser ⟫ — Bottom-Up Parser Visualizer

An interactive desktop application that visualizes bottom-up (shift-reduce) parsing algorithms. Built with Python and Tkinter, themed with ttkbootstrap.

Enter a context-free grammar, select a parser type, and watch the automaton, parsing table, and step-by-step string parsing come to life — complete with draggable state diagrams and animated parsing.

---

## Features

- **Four parser types** — LR(0), SLR(1), CLR(1), LALR(1)
- **State diagram** — Auto-generated canonical collection of items, fully **draggable** (rearrange states by clicking and dragging)
- **Parsing table** — ACTION/GOTO table with color-coded accept rows and conflict highlighting
- **Animated string parsing** — Step-by-step shift/reduce visualization with configurable delay
- **Dual stack views** — Switch between a detailed step table and a visual stack diagram
- **Input buffer visualization** — Lookahead arrow (▼) and crossed-out consumed tokens
- **FIRST & FOLLOW sets** — Computed and displayed for every non-terminal
- **Conflict detection** — Shift-reduce and reduce-reduce conflicts are flagged clearly
- **Modern dark theme** — ttkbootstrap `darkly` theme for a polished look

---

## Screenshots

> Run the application and click **Build Automaton** to see it in action.

---

## Project Structure

```
VisParser/
├── main.py                 # Entry point
├── core/
│   ├── grammar.py          # Grammar parsing & representation
│   ├── first_follow.py     # FIRST/FOLLOW set computation
│   └── parser_engine.py    # Generic shift-reduce parsing engine
├── parsers/
│   ├── lr_base.py          # Shared LR items, closure, goto, canonical collections
│   ├── lr0.py              # LR(0) table builder
│   ├── slr1.py             # SLR(1) table builder
│   ├── clr1.py             # CLR(1) table builder
│   └── lalr1.py            # LALR(1) table builder
└── gui/
    ├── app.py              # Main application window & orchestration
    ├── input_panel.py      # Grammar input, parser selector, FIRST/FOLLOW display
    ├── graph_panel.py      # State diagram (draggable) & parsing table
    └── output_panel.py     # String input, parsing animation, stack views
```

---

## Getting Started

### Prerequisites

- Python 3.10+

### Installation

```bash
pip install ttkbootstrap
```

### Run

```bash
python main.py
```

---

## Usage

1. **Enter a grammar** in the left panel (one rule per line, alternatives separated by `|`):
   ```
   E -> E + T | T
   T -> T * F | F
   F -> ( E ) | id
   ```
2. **Select a parser type** from the dropdown (LR(0), SLR(1), CLR(1), LALR(1))
3. Click **▶ Build Automaton** — the augmented grammar, FIRST/FOLLOW sets, state diagram, and parsing table appear in sequence
4. **Drag states** in the diagram to rearrange them for clarity
5. Enter an **input string** (space-separated tokens, e.g. `id + id * id`)
6. Click **▶ Start Parsing** — watch the animated step-by-step parse with buffer updates and stack visualization
7. Toggle between **Detailed Steps** (table) and **Visual Stack** (graphical) views

---

## Grammar Format

- One production per line: `LHS -> RHS`
- Alternatives on same line: `E -> E + T | T`
- Tokens are space-separated: `F -> ( E ) | id`
- Non-terminals are determined by which symbols appear on the left-hand side
- Epsilon productions: `A -> ε`

---

## License

This project is for educational purposes.
