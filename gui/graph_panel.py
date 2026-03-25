"""
Graph panel – state diagram (Canvas) + parsing table (Treeview).
Split vertically with a resizable sash between diagram and table.
States are draggable: click and drag any state box to reposition it,
and all connected arrows update in real-time.
"""
import math
import tkinter as tk
from tkinter import ttk
from parsers.lr_base import item_to_str, LR1Item


class GraphPanel(ttk.Frame):
    """Centre pane: state diagram and parsing table in a resizable vertical split."""

    CELL_W = 230
    CELL_H = 170

    def __init__(self, parent, **kw):
        super().__init__(parent, **kw)

        # --- Interaction state ---
        self._positions = {}        # state_index -> (cx, cy)  centre of box
        self._transitions = {}      # (src, symbol) -> dst
        self._states = []           # list of frozenset[Item]
        self._grammar = None
        self._drag_data = None      # {"idx": int, "start_x": int, "start_y": int}

        self._build_widgets()

    # ================================================================== #
    #  Widget construction                                                #
    # ================================================================== #
    def _build_widgets(self):
        # ---- Vertical PanedWindow so diagram ↕ table are resizable ----
        self.vpaned = ttk.PanedWindow(self, orient="vertical")
        self.vpaned.pack(fill="both", expand=True)

        # =================== TOP: State Diagram =================== #
        diagram_frame = ttk.Frame(self.vpaned)

        # Header bar with hint
        dh = ttk.Frame(diagram_frame)
        dh.pack(fill="x", padx=10, pady=(8, 0))
        ttk.Label(dh, text="◈  State Diagram", font=("Segoe UI", 11, "bold"),
                  bootstyle="info").pack(side="left")
        ttk.Label(dh, text="(drag states to rearrange)",
                  font=("Segoe UI", 8), bootstyle="secondary").pack(side="left", padx=8)

        # Canvas with scroll
        canvas_outer = ttk.Frame(diagram_frame)
        canvas_outer.pack(fill="both", expand=True, padx=8, pady=(4, 2))

        self.canvas = tk.Canvas(
            canvas_outer, bg="#2b3035", highlightthickness=0,
            bd=0, relief="flat",
        )
        self.h_scroll = ttk.Scrollbar(canvas_outer, orient="horizontal", command=self.canvas.xview)
        self.v_scroll = ttk.Scrollbar(canvas_outer, orient="vertical", command=self.canvas.yview)
        self.canvas.config(xscrollcommand=self.h_scroll.set, yscrollcommand=self.v_scroll.set)

        self.h_scroll.pack(side="bottom", fill="x")
        self.v_scroll.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        # Bind drag events
        self.canvas.bind("<ButtonPress-1>", self._on_press)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)

        # =================== BOTTOM: Parsing Table =================== #
        table_outer = ttk.Frame(self.vpaned)

        th = ttk.Frame(table_outer)
        th.pack(fill="x", padx=10, pady=(6, 0))
        ttk.Label(th, text="◈  Parsing Table", font=("Segoe UI", 11, "bold"),
                  bootstyle="info").pack(side="left")

        # Legend
        legend = ttk.Frame(th)
        legend.pack(side="right")
        ttk.Label(legend, text=" accept ", bootstyle="success inverse",
                  font=("Consolas", 8, "bold")).pack(side="left", padx=2)
        ttk.Label(legend, text=" conflict ", bootstyle="danger inverse",
                  font=("Consolas", 8, "bold")).pack(side="left", padx=2)

        self.table_frame = ttk.Frame(table_outer)
        self.table_frame.pack(fill="both", expand=True, padx=8, pady=(4, 8))

        self.tree = None

        # Add panes
        self.vpaned.add(diagram_frame, weight=2)
        self.vpaned.add(table_outer, weight=1)

    # ================================================================== #
    #  State diagram – drawing                                            #
    # ================================================================== #
    def draw_states(self, states, transitions, grammar):
        """Draw the canonical collection of items on the canvas."""
        self.canvas.delete("all")

        self._states = states
        self._transitions = dict(transitions)
        self._grammar = grammar

        n = len(states)
        if n == 0:
            return

        # Layout: grid
        cols = max(1, int(math.ceil(math.sqrt(n))))
        pad = 70

        self._positions = {}
        for i in range(n):
            row_idx = i // cols
            col_idx = i % cols
            cx = pad + col_idx * (self.CELL_W + pad) + self.CELL_W // 2
            cy = pad + row_idx * (self.CELL_H + pad) + self.CELL_H // 2
            self._positions[i] = (cx, cy)

        # Draw all state boxes
        for i in range(n):
            self._draw_state_box(i)

        # Draw all transitions
        self._draw_all_transitions()

        # Update scroll region
        self._update_scroll_region()

    def _draw_state_box(self, i):
        """Draw a single state box at its current position, tagged for dragging."""
        cx, cy = self._positions[i]
        cw, ch = self.CELL_W, self.CELL_H
        x0 = cx - cw // 2
        y0 = cy - ch // 2
        x1 = cx + cw // 2
        y1 = cy + ch // 2

        tag = f"state_{i}"

        # Shadow
        self.canvas.create_rectangle(
            x0 + 2, y0 + 2, x1 + 2, y1 + 2,
            fill="", outline="#1a1a2e", width=3, tags=(tag,),
        )
        # Main box
        self.canvas.create_rectangle(
            x0, y0, x1, y1,
            fill="#303030", outline="#495057", width=2, tags=(tag,),
        )
        # Top bar accent
        self.canvas.create_rectangle(
            x0, y0, x1, y0 + 22,
            fill="#375a7f", outline="#375a7f", width=1, tags=(tag,),
        )
        # State label
        self.canvas.create_text(
            x0 + 8, y0 + 5, text=f"I{i}", anchor="nw",
            fill="#ffffff", font=("Consolas", 11, "bold"), tags=(tag,),
        )
        # Items text
        sorted_items = sorted(self._states[i], key=lambda it: (it.prod_index, it.dot_pos))
        lines = [item_to_str(item, self._grammar) for item in sorted_items]
        items_text = "\n".join(lines[:7])
        if len(lines) > 7:
            items_text += f"\n… +{len(lines) - 7} more"
        self.canvas.create_text(
            x0 + 12, y0 + 28, text=items_text, anchor="nw",
            fill="#adb5bd", font=("Consolas", 8), width=cw - 24, tags=(tag,),
        )

    def _draw_all_transitions(self):
        """Draw all transition arrows (tagged as 'arrows' for easy redraw)."""
        self.canvas.delete("arrows")
        for (src, symbol), dst in self._transitions.items():
            sx, sy = self._positions[src]
            dx, dy = self._positions[dst]
            if src == dst:
                self._draw_self_loop(sx, sy, symbol)
            else:
                self._draw_arrow(sx, sy, dx, dy, symbol)

    def _draw_arrow(self, sx, sy, dx, dy, label):
        """Arrow between two state boxes with offset for readability."""
        cw, ch = self.CELL_W, self.CELL_H
        angle = math.atan2(dy - sy, dx - sx)
        # Offset perpendicular slightly to avoid overlap with reverse arrows
        perp_x = -math.sin(angle) * 6
        perp_y = math.cos(angle) * 6

        start_x = sx + (cw // 2) * math.cos(angle) + perp_x
        start_y = sy + (ch // 2) * math.sin(angle) + perp_y
        end_x = dx - (cw // 2) * math.cos(angle) + perp_x
        end_y = dy - (ch // 2) * math.sin(angle) + perp_y

        self.canvas.create_line(
            start_x, start_y, end_x, end_y,
            fill="#00bc8c", arrow="last", arrowshape=(10, 14, 5),
            width=1.5, smooth=True, tags=("arrows",),
        )
        mid_x = (start_x + end_x) / 2
        mid_y = (start_y + end_y) / 2

        # Label background pill
        tid = self.canvas.create_text(
            mid_x + perp_x, mid_y + perp_y - 8, text=f" {label} ",
            fill="#ffc107", font=("Consolas", 9, "bold"), tags=("arrows",),
        )
        bb = self.canvas.bbox(tid)
        if bb:
            self.canvas.create_rectangle(
                bb[0] - 2, bb[1] - 1, bb[2] + 2, bb[3] + 1,
                fill="#303030", outline="", width=0, tags=("arrows",),
            )
            self.canvas.tag_raise(tid)

    def _draw_self_loop(self, cx, cy, label):
        """Self-loop arc above a state."""
        r = 22
        x0 = cx - r
        y0 = cy - self.CELL_H // 2 - r * 2
        x1 = cx + r
        y1 = cy - self.CELL_H // 2
        self.canvas.create_arc(
            x0, y0, x1, y1, start=0, extent=300,
            outline="#00bc8c", style="arc", width=1.5, tags=("arrows",),
        )
        self.canvas.create_text(
            cx, y0 - 8, text=label,
            fill="#ffc107", font=("Consolas", 9, "bold"), tags=("arrows",),
        )

    def _update_scroll_region(self):
        """Recalculate canvas scroll region to fit all content."""
        bbox = self.canvas.bbox("all")
        if bbox:
            self.canvas.config(scrollregion=(
                bbox[0] - 40, bbox[1] - 40, bbox[2] + 40, bbox[3] + 40
            ))

    # ================================================================== #
    #  Drag-and-drop interaction                                          #
    # ================================================================== #
    def _hit_state(self, x, y):
        """Return the state index under the given canvas coordinates, or None."""
        for i, (cx, cy) in self._positions.items():
            hw = self.CELL_W // 2
            hh = self.CELL_H // 2
            if cx - hw <= x <= cx + hw and cy - hh <= y <= cy + hh:
                return i
        return None

    def _on_press(self, event):
        """Start dragging if the click is on a state box."""
        # Convert from widget coords to canvas coords (accounts for scroll)
        cx = self.canvas.canvasx(event.x)
        cy = self.canvas.canvasy(event.y)
        idx = self._hit_state(cx, cy)
        if idx is not None:
            self._drag_data = {"idx": idx, "last_x": cx, "last_y": cy}
            self.canvas.config(cursor="fleur")

    def _on_drag(self, event):
        """Move the dragged state box and redraw connected arrows."""
        if self._drag_data is None:
            return

        cx = self.canvas.canvasx(event.x)
        cy = self.canvas.canvasy(event.y)

        dx = cx - self._drag_data["last_x"]
        dy = cy - self._drag_data["last_y"]
        idx = self._drag_data["idx"]

        # Move all canvas items in this state's tag group
        tag = f"state_{idx}"
        self.canvas.move(tag, dx, dy)

        # Update stored position
        old_cx, old_cy = self._positions[idx]
        self._positions[idx] = (old_cx + dx, old_cy + dy)

        self._drag_data["last_x"] = cx
        self._drag_data["last_y"] = cy

        # Redraw all arrows (fast enough for typical grammars)
        self._draw_all_transitions()

    def _on_release(self, event):
        """End dragging and update scroll region."""
        if self._drag_data is not None:
            self._drag_data = None
            self.canvas.config(cursor="")
            self._update_scroll_region()

    # ================================================================== #
    #  Parsing table                                                      #
    # ================================================================== #
    def show_table(self, action_table, goto_table, grammar, conflicts):
        """Build and display the ACTION / GOTO parsing table."""
        for widget in self.table_frame.winfo_children():
            widget.destroy()

        terminals = sorted(grammar.terminals) + ["$"]
        non_terminals = sorted(grammar.non_terminals - {grammar.start_symbol})

        # ---- Column headers ----
        action_cols = terminals
        goto_cols = non_terminals
        all_col_names = ["State"] + action_cols + ["│"] + goto_cols
        col_ids = [f"c{i}" for i in range(len(all_col_names))]

        self.tree = ttk.Treeview(
            self.table_frame, columns=col_ids, show="headings", height=14,
        )

        # Heading label row
        for cid, col_name in zip(col_ids, all_col_names):
            self.tree.heading(cid, text=col_name)
            if col_name == "│":
                self.tree.column(cid, width=8, anchor="center", minwidth=8, stretch=False)
            elif col_name == "State":
                self.tree.column(cid, width=52, anchor="center", minwidth=42, stretch=False)
            else:
                self.tree.column(cid, width=56, anchor="center", minwidth=40)

        # Conflict positions
        conflict_positions = set()
        for msg in conflicts:
            try:
                parts = msg.split("in state ")[1]
                state_num = int(parts.split(" ")[0])
                sym = parts.split("'")[1]
                conflict_positions.add((state_num, sym))
            except (IndexError, ValueError):
                pass

        # Tags: colours that complement the darkly theme
        self.tree.tag_configure("conflict", background="#e74c3c", foreground="#ffffff")
        self.tree.tag_configure("accept", background="#00bc8c", foreground="#ffffff")
        self.tree.tag_configure("even", background="#303030", foreground="#dee2e6")
        self.tree.tag_configure("odd", background="#3a3a3a", foreground="#dee2e6")

        num_states = max(
            max(action_table.keys(), default=0),
            max(goto_table.keys(), default=0),
        ) + 1

        for state_idx in range(num_states):
            values = [f"I{state_idx}"]
            row_has_conflict = False
            row_has_accept = False

            for t in terminals:
                action = action_table.get(state_idx, {}).get(t)
                if action is None:
                    values.append("")
                elif action[0] == "shift":
                    values.append(f"s{action[1]}")
                elif action[0] == "reduce":
                    values.append(f"r{action[1]}")
                elif action[0] == "accept":
                    values.append("acc")
                    row_has_accept = True
                else:
                    values.append(str(action))

                if (state_idx, t) in conflict_positions:
                    row_has_conflict = True

            values.append("")  # separator column

            for nt in non_terminals:
                goto_val = goto_table.get(state_idx, {}).get(nt)
                values.append(str(goto_val) if goto_val is not None else "")

            if row_has_conflict:
                tag = "conflict"
            elif row_has_accept:
                tag = "accept"
            else:
                tag = "even" if state_idx % 2 == 0 else "odd"

            self.tree.insert("", "end", values=values, tags=(tag,))

        # Scrollbars
        sy = ttk.Scrollbar(self.table_frame, orient="vertical", command=self.tree.yview)
        sx = ttk.Scrollbar(self.table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.config(yscrollcommand=sy.set, xscrollcommand=sx.set)
        sy.pack(side="right", fill="y")
        sx.pack(side="bottom", fill="x")
        self.tree.pack(fill="both", expand=True)

        # Conflict banner
        if conflicts:
            conflict_text = "\n".join(conflicts)
            banner = tk.Label(
                self.table_frame,
                text=f"⚠  {conflict_text}",
                bg="#5a2020", fg="#e74c3c",
                font=("Segoe UI", 9), justify="left", wraplength=600, anchor="w",
                padx=10, pady=6,
            )
            banner.pack(fill="x", pady=(4, 0))

    # ================================================================== #
    #  Operator Precedence table                                           #
    # ================================================================== #
    def show_op_table(self, prec_table, terminals, conflicts):
        """Display the operator precedence relation matrix."""
        for widget in self.table_frame.winfo_children():
            widget.destroy()

        sorted_terms = sorted(t for t in terminals if t != "$") + ["$"]

        col_ids = ["c0"] + [f"c{i+1}" for i in range(len(sorted_terms))]
        all_col_names = [""] + sorted_terms

        self.tree = ttk.Treeview(
            self.table_frame, columns=col_ids, show="headings", height=14,
        )

        for cid, col_name in zip(col_ids, all_col_names):
            self.tree.heading(cid, text=col_name)
            if col_name == "":
                self.tree.column(cid, width=52, anchor="center", minwidth=42, stretch=False)
            else:
                self.tree.column(cid, width=56, anchor="center", minwidth=40)

        # Tags
        self.tree.tag_configure("conflict", background="#e74c3c", foreground="#ffffff")
        self.tree.tag_configure("even", background="#303030", foreground="#dee2e6")
        self.tree.tag_configure("odd", background="#3a3a3a", foreground="#dee2e6")

        for row_idx, row_term in enumerate(sorted_terms):
            values = [row_term]
            row_has_conflict = False

            for col_term in sorted_terms:
                rel = prec_table.get((row_term, col_term))
                if rel is None:
                    values.append("")
                elif rel == "<":
                    values.append("⋖")
                elif rel == ">":
                    values.append("⋗")
                elif rel == "=":
                    values.append("≐")
                else:
                    values.append(rel)

            tag = "even" if row_idx % 2 == 0 else "odd"
            self.tree.insert("", "end", values=values, tags=(tag,))

        # Scrollbars
        sy = ttk.Scrollbar(self.table_frame, orient="vertical", command=self.tree.yview)
        sx = ttk.Scrollbar(self.table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.config(yscrollcommand=sy.set, xscrollcommand=sx.set)
        sy.pack(side="right", fill="y")
        sx.pack(side="bottom", fill="x")
        self.tree.pack(fill="both", expand=True)

        if conflicts:
            conflict_text = "\n".join(conflicts)
            banner = tk.Label(
                self.table_frame,
                text=f"⚠  {conflict_text}",
                bg="#5a2020", fg="#e74c3c",
                font=("Segoe UI", 9), justify="left", wraplength=600, anchor="w",
                padx=10, pady=6,
            )
            banner.pack(fill="x", pady=(4, 0))

    def show_no_diagram_message(self, message="No state diagram for this parser type"):
        """Clear the diagram area and show a message."""
        self.canvas.delete("all")
        self._positions.clear()
        self._transitions.clear()
        self._states = []
        self._grammar = None
        self.canvas.update_idletasks()
        cw = max(self.canvas.winfo_width(), 400)
        ch = max(self.canvas.winfo_height(), 200)
        self.canvas.create_text(
            cw // 2, ch // 2, text=message,
            fill="#6c757d", font=("Segoe UI", 12, "italic"),
        )

    def clear(self):
        """Clear diagram and table."""
        self.canvas.delete("all")
        self._positions.clear()
        self._transitions.clear()
        self._states = []
        self._grammar = None
        for widget in self.table_frame.winfo_children():
            widget.destroy()

