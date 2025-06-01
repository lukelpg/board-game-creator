from __future__ import annotations
from dataclasses import dataclass
from typing import List, Tuple


Point = Tuple[int, int]      # (x, y) in the 0-64 editor coordinate space


@dataclass
class ShapeMixin:
    """Adds an optional free-form polygon outline to a token/piece."""

    points: List[Point] | None = None    # list of (x, y) vertices

    # ------------------------------------------------------------------ #
    def is_custom(self) -> bool:
        return bool(self.points)
