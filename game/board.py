from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional, Tuple
from enum import Enum

from .card  import Card
from .piece import Piece
from .token import Token
from .deck  import Deck


Point = Tuple[int, int] 


# ---------- section system ------------------------------------------- #
class SectionType(str, Enum):
    CARD  = "Card"
    PIECE = "Piece"
    TOKEN = "Token"
    DECK  = "Deck"
    ANY   = "Any"


@dataclass
class Section:
    name:   str
    kind:   SectionType
    points: List[Point]          # ordered polygon vertices
    outline: str = "#808080"
    fill:    str = ""            # empty = transparent

# ---------- cell holds **stack** ------------------------------------- #
@dataclass
class Cell:
    x: int
    y: int
    stack: List[Card | Piece | Token | Deck]

    def top(self):
        return self.stack[-1] if self.stack else None


# ---------- board ---------------------------------------------------- #
class Board:
    """Rectangular grid where each cell is an **ordered stack**."""

    def __init__(self, width=8, height=8):
        self.sections: List[Section] = []
        self.resize(width, height)

    # ------------------------------------------------------------- #
    def resize(self, w: int, h: int):
        self.WIDTH, self.HEIGHT = w, h
        self.grid: List[List[Cell]] = [
            [Cell(x, y, []) for x in range(w)] for y in range(h)
        ]
        self.sections.clear()

    # ------------------------------------------------------------- #
    def add_section(self, name, kind: SectionType,
                    points: List[Point],
                    outline="#808080", fill=""):
        self.sections.append(Section(name, kind, points, outline, fill))

    @staticmethod
    def _pnpoly(pts: List[Point], x: int, y: int) -> bool:
        inside = False
        n = len(pts)
        for i, (xi, yi) in enumerate(pts):
            xj, yj = pts[(i + 1) % n]
            if ((yi > y) != (yj > y)) and \
               (x < (xj - xi) * (y - yi) / (yj - yi + 1e-9) + xi):
                inside = not inside
        return inside

    # replace _section_for with:
    def _section_for(self, gx, gy):
        for s in self.sections:
            if self._pnpoly(s.points, gx + .5, gy + .5):
                return s

    # ------------------------------------------------------------- #
    def can_accept(self, x: int, y: int, obj) -> bool:
        if not (0 <= x < self.WIDTH and 0 <= y < self.HEIGHT):
            return False
        sec = self._section_for(x, y)
        if not sec or sec.kind is SectionType.ANY:
            return True
        if sec.kind is SectionType.CARD  and isinstance(obj, Card ): return True
        if sec.kind is SectionType.PIECE and isinstance(obj, Piece): return True
        if sec.kind is SectionType.TOKEN and isinstance(obj, Token): return True
        if sec.kind is SectionType.DECK  and isinstance(obj, Deck ): return True
        return False

    # ------------------------------------------------------------- #
    def place(self, x: int, y: int, obj) -> bool:
        if self.can_accept(x, y, obj):
            self.grid[y][x].stack.append(obj)
            return True
        return False

    def remove_top(self, x: int, y: int):
        st = self.grid[y][x].stack
        return st.pop() if st else None

    def clear_cell(self, x: int, y: int):
        st = self.grid[y][x].stack
        obj, self.grid[y][x].stack = st[:], []
        return obj
