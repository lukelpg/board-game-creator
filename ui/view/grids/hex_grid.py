"""Reusable helpers for axial point‑top hex geometry."""

from math import sqrt
from typing import Tuple

CELL = 64        # default – updated by views

SQRT3 = sqrt(3)

__all__ = ["cell_origin", "hex_points", "pixel_to_hex"]


def cell_origin(col:int, row:int) -> tuple[int,int]:
    dx = col * CELL * 0.75
    dy = row * CELL + (CELL // 2 if col % 2 else 0)
    return int(dx), int(dy)

def hex_points(x:int, y:int):
    q = CELL // 4; h = CELL // 2
    return (x + q,     y,
            x + q*3,   y,
            x + CELL,  y + h,
            x + q*3,   y + CELL,
            x + q,     y + CELL,
            x,         y + h)

def pixel_to_hex(px:int, py:int, cols:int, rows:int) -> Tuple[int,int]:
    col = int(px / (CELL * 0.75))
    row_offset = CELL // 2 if col % 2 else 0
    row = int((py - row_offset) / CELL)
    col = max(0, min(col, cols - 1))
    row = max(0, min(row,  rows - 1))
    return col, row
