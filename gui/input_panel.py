"""
Input panel – grammar entry, parser type selector,
augmented grammar + FIRST/FOLLOW display.
"""
import tkinter as tk
from tkinter import ttk


class InputPanel(ttk.Frame):
    """Left pane: grammar input and computed information display."""

    def __init__(self, parent, on_build_callback, **kw):
        super().__init__(parent, **kw)
        self._on_build = on_build_callback
        self._build_widgets()

    def _build_widgets(self):
        # Section title
        ttk.Label(self, text="◈  Grammar Input", font=("Segoe UI", 12, "bold"),
                  bootstyle="info").pack(padx=10, pady=(8, 4), anchor="w")

        # Grammar text widget
        ttk.Label(self, text="Enter grammar — one rule per line:",
                  font=("Segoe UI", 9), bootstyle="secondary").pack(
            padx=10, pady=(8, 2), anchor="w",
        )

        grammar_frame = ttk.Frame(self)
        grammar_frame.pack(fill="both", expand=True, padx=10, pady=2)

        self.grammar_text = tk.Text(
            grammar_frame, height=8, font=("Consolas", 10),
            bg="#2b3035", fg="#dee2e6", insertbackground="#0d6efd",
            relief="flat", wrap="word", borderwidth=0,
            selectbackground="#375a7f", selectforeground="#ffffff",
            padx=8, pady=6,
        )
        self.grammar_text.pack(fill="both", expand=True)

        # Insert sample grammar
        sample = "E -> E + T | T\nT -> T * F | F\nF -> ( E ) | id"
        self.grammar_text.insert("1.0", sample)

        # Build button – bootstyled
        self.build_btn = ttk.Button(self, text="▶  Build Automaton",
                                    command=self._on_build_click,
                                    bootstyle="success")
        self.build_btn.pack(padx=10, pady=8, fill="x")

        # ---- Augmented grammar ----
        self._section_header("Augmented Grammar")
        self.aug_text = tk.Text(
            self, height=5, font=("Consolas", 9),
            bg="#2b3035", fg="#adb5bd", relief="flat", state="disabled",
            wrap="word", borderwidth=0, padx=8, pady=4,
        )
        self.aug_text.pack(fill="both", expand=True, padx=10, pady=(0, 4))

        # ---- FIRST / FOLLOW ----
        self._section_header("FIRST / FOLLOW Sets")
        self.ff_text = tk.Text(
            self, height=5, font=("Consolas", 9),
            bg="#2b3035", fg="#adb5bd", relief="flat", state="disabled",
            wrap="word", borderwidth=0, padx=8, pady=4,
        )
        self.ff_text.pack(fill="both", expand=True, padx=10, pady=(0, 8))

    def _section_header(self, text):
        """Create a styled sub-section header."""
        hf = ttk.Frame(self)
        hf.pack(fill="x", padx=10, pady=(8, 2))
        ttk.Label(hf, text=text, font=("Segoe UI", 10, "bold")).pack(side="left")
        ttk.Separator(hf, bootstyle="secondary").pack(
            side="left", fill="x", expand=True, padx=(8, 0),
        )

    # ------------------------------------------------------------------ #
    #  Public helpers                                                     #
    # ------------------------------------------------------------------ #
    def _on_build_click(self):
        grammar_str = self.grammar_text.get("1.0", "end").strip()
        if self._on_build:
            self._on_build(grammar_str)

    def show_augmented(self, grammar):
        """Display the augmented grammar."""
        self.aug_text.config(state="normal")
        self.aug_text.delete("1.0", "end")
        for i, (lhs, rhs) in enumerate(grammar.productions):
            self.aug_text.insert("end", f"  {i}. {lhs} → {' '.join(rhs)}\n")
        self.aug_text.config(state="disabled")

    def show_first_follow(self, first_sets, follow_sets, non_terminals):
        """Display FIRST and FOLLOW sets."""
        self.ff_text.config(state="normal")
        self.ff_text.delete("1.0", "end")

        sorted_nts = sorted(non_terminals)

        self.ff_text.insert("end", "FIRST:\n")
        for nt in sorted_nts:
            vals = ", ".join(sorted(first_sets.get(nt, set())))
            self.ff_text.insert("end", f"  FIRST({nt}) = {{ {vals} }}\n")

        self.ff_text.insert("end", "\nFOLLOW:\n")
        for nt in sorted_nts:
            vals = ", ".join(sorted(follow_sets.get(nt, set())))
            self.ff_text.insert("end", f"  FOLLOW({nt}) = {{ {vals} }}\n")

        self.ff_text.config(state="disabled")

    def show_firstterm_lastterm(self, firstterm_sets, lastterm_sets, non_terminals):
        """Display FIRSTTERM and LASTTERM sets (for operator precedence)."""
        self.ff_text.config(state="normal")
        self.ff_text.delete("1.0", "end")

        sorted_nts = sorted(non_terminals)

        self.ff_text.insert("end", "FIRSTTERM:\n")
        for nt in sorted_nts:
            vals = ", ".join(sorted(firstterm_sets.get(nt, set())))
            self.ff_text.insert("end", f"  FIRSTTERM({nt}) = {{ {vals} }}\n")

        self.ff_text.insert("end", "\nLASTTERM:\n")
        for nt in sorted_nts:
            vals = ", ".join(sorted(lastterm_sets.get(nt, set())))
            self.ff_text.insert("end", f"  LASTTERM({nt}) = {{ {vals} }}\n")

        self.ff_text.config(state="disabled")

    def clear_info(self):
        """Clear augmented grammar and FIRST/FOLLOW displays."""
        for widget in (self.aug_text, self.ff_text):
            widget.config(state="normal")
            widget.delete("1.0", "end")
            widget.config(state="disabled")
