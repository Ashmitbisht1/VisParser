"""
Main application – root window with three resizable panes.
Orchestrates the pipeline: grammar → parser → table → string parsing.
Uses ttkbootstrap for a modern dark theme.
"""
import sys
import os
import tkinter as tk
from tkinter import ttk, messagebox
import ttkbootstrap as tb
from ttkbootstrap.constants import *

# Ensure project root is on sys.path so that imports work
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.grammar import Grammar
from core.first_follow import compute_first, compute_follow
from core.parser_engine import parse_string
from core.op_parser_engine import op_parse_string
from parsers.lr0 import build_lr0_table
from parsers.slr1 import build_slr1_table
from parsers.clr1 import build_clr1_table
from parsers.lalr1 import build_lalr1_table
from parsers.operator_precedence import build_op_table, validate_operator_grammar
from gui.input_panel import InputPanel
from gui.graph_panel import GraphPanel
from gui.output_panel import OutputPanel


ANIMATION_DELAY_MS = 700  # milliseconds between each parsing step


class ParserVisApp:
    """Main application controller."""

    def __init__(self):
        self.root = tb.Window(
            title="ParserVis – Bottom-Up Parser Visualizer",
            themename="darkly",
            size=(1440, 860),
            minsize=(1000, 650),
        )

        self._apply_custom_styles()
        self._build_layout()

        # State
        self._action_table = None
        self._goto_table = None
        self._grammar = None
        self._has_conflicts = False
        self._parser_type = None      # track which parser was built
        self._prec_table = None       # for OP parser

    # ------------------------------------------------------------------ #
    #  Custom styles (on top of ttkbootstrap theme)                       #
    # ------------------------------------------------------------------ #
    def _apply_custom_styles(self):
        style = ttk.Style()

        # Treeview: keep our custom row colours for the parsing tables
        style.configure("Treeview",
                         rowheight=24, font=("Consolas", 9))
        style.configure("Treeview.Heading",
                         font=("Segoe UI", 9, "bold"), padding=4)

    # ------------------------------------------------------------------ #
    #  Layout                                                             #
    # ------------------------------------------------------------------ #
    def _build_layout(self):
        # Header
        header = ttk.Frame(self.root)
        header.pack(fill="x", padx=12, pady=(10, 2))

        title_frame = ttk.Frame(header)
        title_frame.pack(side="left")
        ttk.Label(title_frame, text="⟪ ParserVis ⟫",
                  font=("Segoe UI", 18, "bold"),
                  bootstyle="info").pack(side="left")
        ttk.Label(title_frame, text="Bottom-Up Parser Visualizer",
                  font=("Segoe UI", 10), bootstyle="secondary").pack(
            side="left", padx=14, pady=(6, 0),
        )

        # Parser Selection (Segmented Control style)
        self.parser_var = tk.StringVar(value="SLR(1)")
        parser_frame = ttk.Frame(header)
        parser_frame.pack(side="right", padx=(0, 10))
        
        ttk.Label(parser_frame, text="Parser:", font=("Segoe UI", 10, "bold"),
                  bootstyle="secondary").pack(side="left", padx=(0, 10))
        
        parsers = ["LR(0)", "SLR(1)", "CLR(1)", "LALR(1)", "Operator Precedence"]
        for p in parsers:
            ttk.Radiobutton(
                parser_frame, 
                text=p, 
                variable=self.parser_var, 
                value=p,
                bootstyle="info-outline-toolbutton"
            ).pack(side="left", padx=2)

        # Separator
        ttk.Separator(self.root, bootstyle="secondary").pack(
            fill="x", padx=12, pady=(4, 0),
        )

        # Three-pane layout using PanedWindow
        self.paned = ttk.PanedWindow(self.root, orient="horizontal")
        self.paned.pack(fill="both", expand=True, padx=4, pady=4)

        self.input_panel = InputPanel(self.paned, on_build_callback=self._on_build)
        self.graph_panel = GraphPanel(self.paned)
        self.output_panel = OutputPanel(self.paned, on_parse_callback=self._on_parse)

        self.paned.add(self.input_panel, weight=1)
        self.paned.add(self.graph_panel, weight=4)
        self.paned.add(self.output_panel, weight=1)

        def _set_initial_sashes():
            w = self.paned.winfo_width()
            if w > 100:
                self.paned.sashpos(0, int(w * 0.22))
                self.paned.sashpos(1, int(w * 0.78))
            else:
                self.root.after(50, _set_initial_sashes)
        
        self.root.after(50, _set_initial_sashes)
    # ------------------------------------------------------------------ #
    #  Build pipeline                                                     #
    # ------------------------------------------------------------------ #
    # Delay (ms) between each build stage for a sequential reveal effect
    BUILD_STAGE_DELAY_MS = 400

    def _on_build(self, grammar_text: str):
        """Called when the user clicks Build."""
        parser_type = self.parser_var.get()
        self._parser_type = parser_type

        # ---- Operator Precedence branch (no augmentation) ----
        if parser_type == "Operator Precedence":
            self._on_build_op(grammar_text)
            return

        # ---- LR-family branch ----
        try:
            base_grammar = Grammar.from_text(grammar_text)
            grammar = base_grammar.augment()
            self._grammar = grammar
        except ValueError as e:
            messagebox.showerror("Grammar Error", str(e))
            return

        # Build table based on selected parser
        try:
            if parser_type == "LR(0)":
                action, goto, states, transitions, conflicts = build_lr0_table(grammar)
                first = compute_first(grammar)
                follow = compute_follow(grammar, first)
            elif parser_type == "SLR(1)":
                action, goto, states, transitions, conflicts, first, follow = build_slr1_table(grammar)
            elif parser_type == "CLR(1)":
                action, goto, states, transitions, conflicts, first, follow = build_clr1_table(grammar)
            elif parser_type == "LALR(1)":
                action, goto, states, transitions, conflicts, first, follow = build_lalr1_table(grammar)
            else:
                messagebox.showerror("Error", f"Unknown parser type: {parser_type}")
                return
        except Exception as e:
            messagebox.showerror("Build Error", str(e))
            return

        self._action_table = action
        self._goto_table = goto
        self._has_conflicts = bool(conflicts)
        self._prec_table = None

        # Clear old parse output immediately
        self.output_panel.clear()

        # Stage 1: Show augmented grammar
        self.input_panel.show_augmented(grammar)

        # Stage 2: Show FIRST/FOLLOW sets after a delay
        self.root.after(self.BUILD_STAGE_DELAY_MS, lambda:
            self.input_panel.show_first_follow(first, follow, grammar.non_terminals)
        )

        # Stage 3: Draw state diagram after another delay
        self.root.after(self.BUILD_STAGE_DELAY_MS * 2, lambda:
            self.graph_panel.draw_states(states, transitions, grammar)
        )

        # Stage 4: Show parsing table + conflict warning after another delay
        def _show_table_and_warnings():
            self.graph_panel.show_table(action, goto, grammar, conflicts)
            if conflicts:
                messagebox.showwarning(
                    "Conflicts Detected",
                    f"This grammar is NOT {parser_type}!\n\n" + "\n".join(conflicts)
                )

        self.root.after(self.BUILD_STAGE_DELAY_MS * 3, _show_table_and_warnings)

    # ------------------------------------------------------------------ #
    #  Operator Precedence build                                          #
    # ------------------------------------------------------------------ #
    def _on_build_op(self, grammar_text: str):
        """Build pipeline for Operator Precedence parser."""
        try:
            grammar = Grammar.from_text(grammar_text)
            self._grammar = grammar
        except ValueError as e:
            messagebox.showerror("Grammar Error", str(e))
            return

        # Validate operator grammar
        errors = validate_operator_grammar(grammar)
        if errors:
            messagebox.showerror(
                "Not an Operator Grammar",
                "This grammar is not a valid operator grammar:\n\n" + "\n".join(errors)
            )
            return

        try:
            prec_table, firstterm, lastterm, conflicts, build_errors = build_op_table(grammar)
        except Exception as e:
            messagebox.showerror("Build Error", str(e))
            return

        if build_errors:
            messagebox.showerror(
                "Build Error",
                "\n".join(build_errors)
            )
            return

        self._prec_table = prec_table
        self._action_table = None
        self._goto_table = None
        self._has_conflicts = bool(conflicts)

        # Clear old parse output
        self.output_panel.clear()

        # Stage 1: Show grammar (not augmented for OP)
        self.input_panel.show_augmented(grammar)

        # Stage 2: Show FIRSTTERM/LASTTERM
        self.root.after(self.BUILD_STAGE_DELAY_MS, lambda:
            self.input_panel.show_firstterm_lastterm(firstterm, lastterm, grammar.non_terminals)
        )

        # Stage 3: Show "no state diagram" message
        self.root.after(self.BUILD_STAGE_DELAY_MS * 2, lambda:
            self.graph_panel.show_no_diagram_message(
                "Operator Precedence parsing does not use a state diagram."
            )
        )

        # Stage 4: Show precedence table
        def _show_op_table():
            self.graph_panel.show_op_table(prec_table, grammar.terminals, conflicts)
            if conflicts:
                messagebox.showwarning(
                    "Conflicts Detected",
                    "Precedence relation conflicts:\n\n" + "\n".join(conflicts)
                )

        self.root.after(self.BUILD_STAGE_DELAY_MS * 3, _show_op_table)

    # ------------------------------------------------------------------ #
    #  String parsing                                                     #
    # ------------------------------------------------------------------ #
    def _on_parse(self, input_str: str):
        """Called when the user clicks Start Parsing."""
        if self._grammar is None:
            messagebox.showinfo("Info", "Please build the grammar first.")
            return

        # Check which parser was used
        if self._parser_type == "Operator Precedence":
            if self._prec_table is None:
                messagebox.showinfo("Info", "Please build the grammar first.")
                return
        else:
            if self._action_table is None:
                messagebox.showinfo("Info", "Please build the grammar first.")
                return

        if self._has_conflicts:
            messagebox.showerror(
                "Invalid Grammar",
                "Grammar is not valid for this parser type.\n"
                "Conflicts detected. Parsing will not proceed."
            )
            return

        self.output_panel.clear()
        self.output_panel.enable_parse_button(False)

        # Initialise the input buffer with all tokens
        tokens = input_str.strip().split()
        self.output_panel.init_buffer(tokens)

        # Run parse steps with animation
        if self._parser_type == "Operator Precedence":
            steps = list(op_parse_string(
                self._prec_table, self._grammar, input_str
            ))
        else:
            steps = list(parse_string(
                self._action_table, self._goto_table,
                self._grammar, input_str
            ))

        self._animate_steps(steps, 0, tokens)

    def _animate_steps(self, steps, index, original_tokens):
        """Animate parse steps one by one with a slower delay."""
        if index >= len(steps):
            self.output_panel.enable_parse_button(True)
            return

        stack, remaining, action = steps[index]

        # Update buffer with strikethrough
        self.output_panel.set_buffer(remaining)

        # Update step in detailed view
        self.output_panel.add_step(index + 1, stack, remaining, action)

        # Update visual stack
        if self._parser_type == "Operator Precedence":
            # OP stack display is just space-separated symbols (no interleaved states)
            symbol_stack = [s for s in stack.split() if s != "$"]
        else:
            symbol_stack = self._extract_symbols(stack)
        self.output_panel.update_visual_stack(symbol_stack)

        if action == "ACCEPT":
            self.output_panel.show_result(True)
            self.output_panel.enable_parse_button(True)
            return
        elif action.startswith("ERROR"):
            self.output_panel.show_result(False)
            self.output_panel.enable_parse_button(True)
            return

        # Schedule next step (slower)
        self.root.after(ANIMATION_DELAY_MS, self._animate_steps, steps, index + 1, original_tokens)

    @staticmethod
    def _extract_symbols(stack_display: str) -> list:
        """Extract symbol names from the interleaved 'state sym state sym ...' display."""
        parts = stack_display.split()
        symbols = []
        # Pattern: state0 sym1 state1 sym2 state2 ...
        # Symbols are at odd indices (1, 3, 5, ...)
        for i in range(1, len(parts), 2):
            symbols.append(parts[i])
        return symbols

    # ------------------------------------------------------------------ #
    #  Run                                                                #
    # ------------------------------------------------------------------ #
    def run(self):
        self.root.mainloop()
