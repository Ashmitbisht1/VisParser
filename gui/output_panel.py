"""
Output panel – string input, dual stack views (Visual / Detailed),
input buffer with lookahead arrow & crossed-out consumed tokens,
accept/reject message.
"""
import tkinter as tk
from tkinter import ttk


class OutputPanel(ttk.Frame):
    """Right pane: string parsing with two switchable stack visualisations."""

    def __init__(self, parent, on_parse_callback, **kw):
        super().__init__(parent, **kw)
        self._on_parse = on_parse_callback
        self._all_tokens = []       # original token list (for cross-out display)
        self._consumed_count = 0    # how many tokens have been consumed so far
        self._current_view = "detailed"  # "detailed" or "visual"
        self._visual_stack_items = []    # current symbol stack for visual view
        self._build_widgets()

    # ================================================================== #
    #  Widget construction                                                #
    # ================================================================== #
    def _build_widgets(self):
        # ---- Title ----
        title = ttk.Label(self, text="◈  String Parser", font=("Segoe UI", 12, "bold"),
                          bootstyle="info")
        title.pack(padx=10, pady=(8, 2), anchor="w")

        # ---- Input entry ----
        input_frame = ttk.Frame(self)
        input_frame.pack(fill="x", padx=10, pady=4)
        ttk.Label(input_frame, text="Input string (space-separated tokens):",
                  font=("Segoe UI", 9), bootstyle="secondary").pack(anchor="w")

        self.string_entry = ttk.Entry(input_frame, font=("Consolas", 11))
        self.string_entry.pack(fill="x", pady=(4, 2))
        self.string_entry.insert(0, "id + id * id")

        self.parse_btn = ttk.Button(input_frame, text="▶  Start Parsing",
                                    command=self._on_parse_click,
                                    bootstyle="success")
        self.parse_btn.pack(fill="x", pady=(2, 4))

        # ---- Input Buffer (with lookahead arrow + crossed-out tokens) ----
        ttk.Label(self, text="Input Buffer:", font=("Segoe UI", 10, "bold")).pack(
            padx=10, pady=(6, 1), anchor="w",
        )
        self.buffer_canvas = tk.Canvas(
            self, height=36, bg="#2b3035", highlightthickness=0, bd=0,
        )
        self.buffer_canvas.pack(fill="x", padx=10, pady=(0, 4))

        # ---- View toggle buttons ----
        toggle_frame = ttk.Frame(self)
        toggle_frame.pack(fill="x", padx=10, pady=(4, 2))

        self.btn_detailed = ttk.Button(
            toggle_frame, text="📋 Detailed Steps",
            bootstyle="info",
            command=lambda: self._switch_view("detailed"),
        )
        self.btn_detailed.pack(side="left", fill="x", expand=True, padx=(0, 2))

        self.btn_visual = ttk.Button(
            toggle_frame, text="📦 Visual Stack",
            bootstyle="secondary-outline",
            command=lambda: self._switch_view("visual"),
        )
        self.btn_visual.pack(side="left", fill="x", expand=True, padx=(2, 0))

        # ---- Stack views container ----
        self.views_container = ttk.Frame(self)
        self.views_container.pack(fill="both", expand=True, padx=10, pady=4)

        # == Detailed Steps view (Treeview table) ==
        self.detailed_frame = ttk.Frame(self.views_container)

        self.tree = ttk.Treeview(
            self.detailed_frame,
            columns=("step", "stack", "input", "action"),
            show="headings", height=12,
        )
        self.tree.heading("step", text="#")
        self.tree.heading("stack", text="Stack")
        self.tree.heading("input", text="Input")
        self.tree.heading("action", text="Action")

        self.tree.column("step", width=32, anchor="center", minwidth=28)
        self.tree.column("stack", width=155, anchor="w", minwidth=80)
        self.tree.column("input", width=120, anchor="w", minwidth=60)
        self.tree.column("action", width=200, anchor="w", minwidth=100)

        self.tree.tag_configure("shift", foreground="#0d6efd")      # blue
        self.tree.tag_configure("reduce", foreground="#fd7e14")      # orange
        self.tree.tag_configure("accept", background="#00bc8c", foreground="#ffffff")
        self.tree.tag_configure("error", background="#e74c3c", foreground="#ffffff")
        self.tree.tag_configure("normal", foreground="#dee2e6")

        tree_scroll = ttk.Scrollbar(self.detailed_frame, orient="vertical", command=self.tree.yview)
        self.tree.config(yscrollcommand=tree_scroll.set)
        tree_scroll.pack(side="right", fill="y")
        self.tree.pack(fill="both", expand=True)

        # == Visual Stack view (Canvas) ==
        self.visual_frame = ttk.Frame(self.views_container)
        self.stack_canvas = tk.Canvas(
            self.visual_frame, bg="#2b3035", highlightthickness=0, bd=0,
        )
        self.stack_canvas.pack(fill="both", expand=True)

        # Show detailed by default
        self.detailed_frame.pack(fill="both", expand=True)

        # ---- Result label ----
        self.result_label = ttk.Label(
            self, text="", font=("Segoe UI", 12, "bold"),
            anchor="center",
        )
        self.result_label.pack(fill="x", padx=10, pady=(2, 8))

    # ================================================================== #
    #  View switching                                                     #
    # ================================================================== #
    def _switch_view(self, view_name):
        self._current_view = view_name
        # Update button appearance via bootstyle
        if view_name == "detailed":
            self.btn_detailed.configure(bootstyle="info")
            self.btn_visual.configure(bootstyle="secondary-outline")
            self.visual_frame.pack_forget()
            self.detailed_frame.pack(fill="both", expand=True)
        else:
            self.btn_visual.configure(bootstyle="info")
            self.btn_detailed.configure(bootstyle="secondary-outline")
            self.detailed_frame.pack_forget()
            self.visual_frame.pack(fill="both", expand=True)
            self._redraw_visual_stack()

    # ================================================================== #
    #  Input buffer with lookahead arrow & crossed-out tokens             #
    # ================================================================== #
    def init_buffer(self, tokens):
        """Initialise the buffer with the full token list + $."""
        self._all_tokens = list(tokens) + ["$"]
        self._consumed_count = 0
        self._draw_buffer()

    def advance_buffer(self, remaining_count):
        """Mark tokens as consumed based on how many remain."""
        self._consumed_count = len(self._all_tokens) - remaining_count
        self._draw_buffer()

    def _draw_buffer(self):
        """Redraw the input buffer canvas with crossed-out consumed tokens
        and a ▼ arrow on the current lookahead."""
        self.buffer_canvas.delete("all")
        x = 10
        y = 20
        font_normal = ("Consolas", 11)
        font_struck = ("Consolas", 11, "overstrike")
        lookahead_idx = self._consumed_count

        for i, tok in enumerate(self._all_tokens):
            if i < self._consumed_count:
                # Crossed-out (consumed)
                tid = self.buffer_canvas.create_text(
                    x, y, text=tok, anchor="w",
                    fill="#6c757d", font=font_struck,
                )
            elif i == lookahead_idx:
                # Current lookahead – highlighted
                tid = self.buffer_canvas.create_text(
                    x, y, text=tok, anchor="w",
                    fill="#ffc107", font=("Consolas", 11, "bold"),
                )
                # Arrow above
                bb = self.buffer_canvas.bbox(tid)
                if bb:
                    mid_x = (bb[0] + bb[2]) / 2
                    self.buffer_canvas.create_text(
                        mid_x, 4, text="▼", anchor="n",
                        fill="#ffc107", font=("Consolas", 8),
                    )
            else:
                tid = self.buffer_canvas.create_text(
                    x, y, text=tok, anchor="w",
                    fill="#dee2e6", font=font_normal,
                )

            bb = self.buffer_canvas.bbox(tid)
            if bb:
                x = bb[2] + 10

    # ================================================================== #
    #  Visual stack (push/pop cells)                                      #
    # ================================================================== #
    def update_visual_stack(self, symbol_stack):
        """Update the symbol stack list and redraw if visual view is active."""
        self._visual_stack_items = list(symbol_stack)
        if self._current_view == "visual":
            self._redraw_visual_stack()

    def _redraw_visual_stack(self):
        """Draw the symbol stack as a column of cells, bottom-up."""
        self.stack_canvas.delete("all")
        self.stack_canvas.update_idletasks()

        canvas_w = max(self.stack_canvas.winfo_width(), 200)
        canvas_h = max(self.stack_canvas.winfo_height(), 200)

        cell_w = min(140, canvas_w - 40)
        cell_h = 30
        gap = 2
        x_center = canvas_w // 2
        items = self._visual_stack_items

        if not items:
            self.stack_canvas.create_text(
                x_center, canvas_h // 2, text="(empty stack)",
                fill="#6c757d", font=("Segoe UI", 10, "italic"),
            )
            return

        # Draw bottom-up: first item at bottom
        start_y = canvas_h - 20  # bottom margin

        for i, symbol in enumerate(items):
            y = start_y - i * (cell_h + gap)
            x0 = x_center - cell_w // 2
            x1 = x_center + cell_w // 2

            # Colour: terminals vs non-terminals (simple heuristic: uppercase = NT)
            if symbol[0].isupper():
                fill_col = "#375a7f"
                border_col = "#0d6efd"
                text_col = "#6ea8fe"
            else:
                fill_col = "#2b3035"
                border_col = "#00bc8c"
                text_col = "#00bc8c"

            # Highlight top of stack
            if i == len(items) - 1:
                fill_col = "#495057"
                border_col = "#ffc107"
                text_col = "#ffc107"

            self.stack_canvas.create_rectangle(
                x0, y - cell_h, x1, y,
                fill=fill_col, outline=border_col, width=2,
            )
            self.stack_canvas.create_text(
                x_center, y - cell_h // 2, text=symbol,
                fill=text_col, font=("Consolas", 12, "bold"),
            )

        # "TOP ↑" label
        top_y = start_y - len(items) * (cell_h + gap)
        self.stack_canvas.create_text(
            x_center, top_y - 4, text="▲ TOP", anchor="s",
            fill="#6c757d", font=("Segoe UI", 8),
        )

    # ================================================================== #
    #  Public API                                                         #
    # ================================================================== #
    def _on_parse_click(self):
        input_str = self.string_entry.get().strip()
        if self._on_parse:
            self._on_parse(input_str)

    def clear(self):
        """Clear all parse output."""
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.buffer_canvas.delete("all")
        self.stack_canvas.delete("all")
        self._visual_stack_items = []
        self._all_tokens = []
        self._consumed_count = 0
        self.result_label.config(text="", bootstyle="default")

    def set_buffer(self, text):
        """Legacy-compatible: update buffer from remaining-text string."""
        # Count remaining tokens to update the buffer display
        remaining_tokens = text.strip().split() if text.strip() else []
        remaining_count = len(remaining_tokens)
        self.advance_buffer(remaining_count)

    def add_step(self, step_num, stack, input_str, action):
        """Add one row to the detailed stack trace table."""
        if action == "ACCEPT":
            tag = "accept"
        elif action.startswith("ERROR"):
            tag = "error"
        elif action.startswith("Shift"):
            tag = "shift"
        elif action.startswith("Reduce"):
            tag = "reduce"
        else:
            tag = "normal"

        self.tree.insert("", "end", values=(step_num, stack, input_str, action), tags=(tag,))
        # Auto-scroll and highlight current row
        children = self.tree.get_children()
        if children:
            last = children[-1]
            self.tree.see(last)
            self.tree.selection_set(last)

    def show_result(self, accepted: bool):
        """Display the final accept/reject message."""
        if accepted:
            self.result_label.config(
                text="✓  String ACCEPTED", bootstyle="success inverse",
            )
        else:
            self.result_label.config(
                text="✗  String REJECTED", bootstyle="danger inverse",
            )

    def enable_parse_button(self, enabled=True):
        self.parse_btn.config(state="normal" if enabled else "disabled")
