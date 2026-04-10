"""
Main application – root window with three resizable panes.
Orchestrates the pipeline: grammar → parser → table → string parsing.
Uses ttkbootstrap for a modern dark theme.
"""
import sys
import os
import webbrowser
import tkinter as tk
from tkinter import ttk, messagebox
import ttkbootstrap as tb
from ttkbootstrap.constants import *

# Ensure project root is on sys.path so that imports work
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.grammar import Grammar
from core.first_follow import compute_first, compute_follow
from core.parser_engine import parse_string
from parsers.lr0 import build_lr0_table
from parsers.slr1 import build_slr1_table
from parsers.clr1 import build_clr1_table
from parsers.lalr1 import build_lalr1_table
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
        parser_frame.pack(side="left", padx=(30, 10))
        
        ttk.Label(parser_frame, text="Parser:", font=("Segoe UI", 10, "bold"),
                  bootstyle="secondary").pack(side="left", padx=(0, 5))
        
        parsers = ["LR(0)", "SLR(1)", "CLR(1)", "LALR(1)"]
        for p in parsers:
            ttk.Radiobutton(
                parser_frame, 
                text=p, 
                variable=self.parser_var, 
                value=p,
                bootstyle="info-outline-toolbutton"
            ).pack(side="left", padx=2)

        # Study Theory Section
        study_frame = ttk.Frame(header)
        study_frame.pack(side="left", padx=(20, 10))
        
        ttk.Label(study_frame, text="Study Theory:", font=("Segoe UI", 10, "bold"),
                  bootstyle="secondary").pack(side="left", padx=(0, 5))
        
        study_links = {
            "LR(0)": "https://www.geeksforgeeks.org/lr-parser/",
            "SLR(1)": "https://www.geeksforgeeks.org/slr-parser-with-examples/",
            "CLR(1)": "https://www.geeksforgeeks.org/clr-parser-with-examples/",
            "LALR(1)": "https://www.geeksforgeeks.org/lalr-parser-in-compiler-design/",
        }
        
        for p in parsers:
            btn = ttk.Button(
                study_frame,
                text=p,
                bootstyle="success-outline-toolbutton",
                command=lambda url=study_links[p]: webbrowser.open_new_tab(url)
            )
            btn.pack(side="left", padx=2)

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
    #  String parsing                                                     #
    # ------------------------------------------------------------------ #
    def _on_parse(self, input_str: str):
        """Called when the user clicks Start Parsing."""
        if self._action_table is None or self._grammar is None:
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

        # Update visual stack: extract symbol stack from the interleaved display
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
