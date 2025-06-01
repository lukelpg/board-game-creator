from __future__ import annotations
import tkinter as tk
from typing import List, Tuple

Point = Tuple[int, int]        # (x, y) within 64×64 canvas


class ShapeCanvas(tk.Canvas):
    """Left-click to add vertices; Right-click to finish & clear selection."""

    def __init__(self, master):
        super().__init__(master, width=64, height=64,
                         background="white", highlightthickness=1, relief="sunken")
        self.points: List[Point] = []
        self.bind("<Button-1>", self._add_point)
        self.bind("<Button-3>", self._finish)

    # ---------------- drawing ------------------------------------------ #
    def _add_point(self, e):
        self.points.append((e.x, e.y))
        self._redraw()

    def _finish(self, _):
        # Right-click clears points (useful for re-drawing)
        self.points.clear()
        self._redraw()

    def _redraw(self):
        self.delete("all")
        if len(self.points) >= 2:
            self.create_polygon(*self._flatten(self.points),
                                fill="lightblue", outline="black")
        for x, y in self.points:
            self.create_oval(x-2, y-2, x+2, y+2, fill="black")

    @staticmethod
    def _flatten(pts: List[Point]):
        return [coord for pt in pts for coord in pt]
