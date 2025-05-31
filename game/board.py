from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, List
from .card import Card

@dataclass
class Cell:
    x: int
    y: int
    card: Optional[Card] = None

class Board:
    """Simple 8×8 grid board."""
    WIDTH, HEIGHT = 8, 8

    def __init__(self):
        self.grid: List[List[Cell]] = [
            [Cell(x, y) for x in range(self.WIDTH)]
            for y in range(self.HEIGHT)
        ]

    # --------- placement --------------------------------------------------
    def place(self, x: int, y: int, card: Card) -> bool:
        cell = self.grid[y][x]
        if cell.card:
            return False
        cell.card = card
        return True

    def remove(self, x: int, y: int) -> Optional[Card]:
        cell = self.grid[y][x]
        card, cell.card = cell.card, None
        return card
