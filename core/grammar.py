"""
Grammar representation and augmented grammar construction.
Parses multi-line grammar text and stores productions.
"""


class Grammar:
    """
    Represents a context-free grammar.

    Productions are stored as a list of (lhs, rhs) tuples where:
      - lhs is a non-terminal string
      - rhs is a list of symbol strings

    Example input text:
        E -> E + T | T
        T -> T * F | F
        F -> ( E ) | id
    """

    EPSILON = "ε"

    def __init__(self, productions=None, start_symbol=None):
        self.productions: list[tuple[str, list[str]]] = productions or []
        self.start_symbol: str | None = start_symbol
        self._terminals: set[str] | None = None
        self._non_terminals: set[str] | None = None

    # ------------------------------------------------------------------ #
    #  Parsing from text                                                  #
    # ------------------------------------------------------------------ #
    @classmethod
    def from_text(cls, text: str) -> "Grammar":
        """Parse a multi-line grammar string and return a Grammar object."""
        productions = []
        start_symbol = None

        for line in text.strip().splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            if "->" not in line:
                raise ValueError(f"Invalid production (missing ->): {line}")

            lhs, rhs_text = line.split("->", 1)
            lhs = lhs.strip()

            if start_symbol is None:
                start_symbol = lhs

            # Split alternatives on '|'
            alternatives = rhs_text.split("|")
            for alt in alternatives:
                symbols = alt.strip().split()
                if not symbols:
                    symbols = [cls.EPSILON]
                productions.append((lhs, symbols))

        if not productions:
            raise ValueError("No productions found in grammar text.")

        return cls(productions, start_symbol)

    # ------------------------------------------------------------------ #
    #  Augmented grammar                                                  #
    # ------------------------------------------------------------------ #
    def augment(self) -> "Grammar":
        """Return a new grammar with an augmented start production S' -> S."""
        if self.start_symbol is None:
            raise ValueError("Cannot augment a grammar with no start symbol.")
        aug_start: str = self.start_symbol + "'"
        # Ensure uniqueness
        while aug_start in self.non_terminals:
            aug_start += "'"

        new_prods = [(aug_start, [self.start_symbol])] + list(self.productions)
        return Grammar(new_prods, aug_start)

    # ------------------------------------------------------------------ #
    #  Symbol sets                                                        #
    # ------------------------------------------------------------------ #
    @property
    def non_terminals(self) -> set[str]:
        if self._non_terminals is None:
            self._non_terminals = {lhs for lhs, _ in self.productions}
        return self._non_terminals

    @property
    def terminals(self) -> set[str]:
        if self._terminals is None:
            all_symbols: set[str] = set()
            for _, rhs in self.productions:
                for s in rhs:
                    if s != self.EPSILON:
                        all_symbols.add(s)
            self._terminals = all_symbols - self.non_terminals
        return self._terminals

    @property
    def symbols(self) -> set:
        return self.terminals | self.non_terminals

    # ------------------------------------------------------------------ #
    #  Helpers                                                            #
    # ------------------------------------------------------------------ #
    def productions_for(self, non_terminal: str):
        """Return all productions whose LHS is the given non-terminal."""
        return [(lhs, rhs) for lhs, rhs in self.productions if lhs == non_terminal]

    def production_str(self, index: int) -> str:
        """Human-readable string for production at given index."""
        lhs, rhs = self.productions[index]
        return f"{lhs} -> {' '.join(rhs)}"

    def __repr__(self):
        lines = []
        for lhs, rhs in self.productions:
            lines.append(f"  {lhs} -> {' '.join(rhs)}")
        return "Grammar(\n" + "\n".join(lines) + "\n)"
