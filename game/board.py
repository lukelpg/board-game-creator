from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional
from enum import Enum

from .card  import Card
from .piece import Piece
from .token import Token
from .deck  import Deck


# ------------ section system ------------------------------------------ #
class SectionType(str, Enum):
    CARD  = "Card"
    PIECE = "Piece"
    TOKEN = "Token"
    DECK  = "Deck"


@dataclass
class Section:
    x0: int; y0: int
    x1: int; y1: int
    kind: SectionType


@dataclass
class Cell:
    x: int
    y: int
    occupant: Card | Piece | Token | Deck | None = None


class Board:
    """Rectangular board with typed sections and mutability."""

    def __init__(self, width: int = 8, height: int = 8):
        self.sections: List[Section] = []
        self.resize(width, height)

    # ------------------------------------------------------------------ #
    def resize(self, width: int, height: int):
        self.WIDTH, self.HEIGHT = width, height
        self.grid: List[List[Cell]] = [
            [Cell(x, y) for x in range(width)] for y in range(height)
        ]
        self.sections.clear()

    # ------------------------------------------------------------------ #
    def add_section(self, x0, y0, x1, y1, kind: SectionType):
        self.sections.append(Section(x0, y0, x1, y1, kind))

    # ------------------------------------------------------------------ #
    def _section_for(self, x, y):
        for s in self.sections:
            if s.x0 <= x <= s.x1 and s.y0 <= y <= s.y1:
                return s
        return None

    # ------------------------------------------------------------------ #
    def place(self, x: int, y: int,
              obj: Card | Piece | Token | Deck) -> bool:
        if not (0 <= x < self.WIDTH and 0 <= y < self.HEIGHT):
            return False

        sec = self._section_for(x, y)
        if sec:
            if sec.kind is SectionType.CARD  and not isinstance(obj, Card):   return False
            if sec.kind is SectionType.PIECE and not isinstance(obj, Piece):  return False
            if sec.kind is SectionType.TOKEN and not isinstance(obj, Token):  return False
            if sec.kind is SectionType.DECK  and not isinstance(obj, Deck):   return False

        cell = self.grid[y][x]
        if cell.occupant:
            return False

        cell.occupant = obj
        return True

    # ------------------------------------------------------------------ #
    def remove(self, x: int, y: int):
        cell = self.grid[y][x]
        obj, cell.occupant = cell.occupant, None
        return obj
