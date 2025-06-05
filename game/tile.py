# game/tile.py
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Tuple

ShapePts = List[Tuple[int, int]]     # local pixel points inside a CELL box
CELL = 64

@dataclass
class Tile:
    name: str
    shape: str                 # "rect" | "hex" | "poly"
    points: ShapePts           # outline scaled for CELL (64×64)
    outline: str = "#808080"
    fill: str = "#cccccc"
    image_path: str | None = None

    # helpers ----------------------------------------------------------
    def clone(self) -> "Tile":
        return Tile(self.name, self.shape, self.points[:],
                    self.outline, self.fill, self.image_path)

    # serialise --------------------------------------------------------
    def to_dict(self):
        return {
            "name": self.name,
            "shape": self.shape,
            "points": self.points,
            "outline": self.outline,
            "fill": self.fill,
            "image": self.image_path,
        }

    @classmethod
    def from_dict(cls, d):
        return cls(d["name"], d["shape"], d["points"],
                   d.get("outline", "#808080"),
                   d.get("fill", "#cccccc"),
                   d.get("image"))
