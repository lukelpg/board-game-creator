from __future__ import annotations
from dataclasses import dataclass
from typing import List, Tuple, Dict
from .card  import Card
from .piece import Piece
from .token import Token
from .deck  import Deck

Obj = Card | Piece | Token | Deck
Point = Tuple[int, int]


@dataclass
class Placed:
    obj: Obj
    x: int
    y: int


@dataclass
class FreeBoard:
    """Pixel-coordinate board (no grid)."""
    width: int
    height: int
    placed: List[Placed]          # every object instance
    sections: List[Dict]          # same polygon sections as before

    # ------------------------------------------------------------------ #
    def objects_at(self, px: int, py: int) -> list[Placed]:
        """Return list of placed items whose bounding box covers (px,py)."""
        r = []
        for p in self.placed:
            if p.x <= px < p.x + 64 and p.y <= py < p.y + 64:
                r.append(p)
        return r

    # easy helpers
    def add(self, obj: Obj, px: int, py: int):
        self.placed.append(Placed(obj, px, py))

    def remove(self, placed: Placed):
        self.placed.remove(placed)
