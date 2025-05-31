from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, List
from .card  import Card
from .piece import Piece

@dataclass
class Cell:
    x: int
    y: int
    occupant: Card | Piece | None = None

class Board:
    """Dynamic-size rectangular board."""
    def __init__(self, width: int = 8, height: int = 8):
        self.resize(width, height)

    # ---------------- public API --------------------------------------- #
    def place(self, x: int, y: int, thing: Card | Piece) -> bool:
        cell = self.grid[y][x]
        if cell.occupant:
            return False
        cell.occupant = thing
        return True

    def remove(self, x: int, y: int):
        cell = self.grid[y][x]
        thing, cell.occupant = cell.occupant, None
        return thing

    def resize(self, w: int, h: int):
        self.WIDTH, self.HEIGHT = w, h
        self.grid: List[List[Cell]] = [
            [Cell(x, y) for x in range(w)] for y in range(h)
        ]
