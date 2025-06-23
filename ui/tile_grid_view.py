# ui/tile_grid_view.py
from __future__ import annotations
import pathlib, tkinter as tk
from typing import Dict, List
from PIL import Image, ImageTk

from game.tile import Tile, CELL
from ui.view.zoom import ZoomMixin           # zoom support

# ------------------------------------------------------------------ #
class TileGridView(ZoomMixin, tk.Canvas):
    """
    Rect- or hex-tile board that zooms (Ctrl-wheel), lets you place tiles,
    and toggles grid outlines with the “g” key.
    """

    # -------------------------------------------------------------- #
    def __init__(self, master, tileset: List[Tile],
                 cols: int, rows: int, img_dir: pathlib.Path,
                 shape: str = "hex", show_grid: bool = True):
        if cols is None or rows is None or cols < 1 or rows < 1:
            raise ValueError("cols and rows must be positive integers")

        super().__init__(master, width=cols * CELL, height=rows * CELL,
                         bg="white", highlightthickness=0)

        self.tileset = tileset
        self.cols, self.rows = cols, rows
        self.shape = shape.lower()          # "rect" or "hex"
        self.show_grid = show_grid

        self.grid: list[list[Tile | None]] = [[None]*cols for _ in range(rows)]
        self.img_dir = img_dir
        self._cache: Dict[str, ImageTk.PhotoImage] = {}

        self._bind_zoom()                   # Ctrl-wheel zoom
        self.bind("<Button-1>", self._click)
        self.bind_all("g", lambda _e: self.toggle_grid())  # show / hide lines
        self._redraw()

    # -------------------------------------------------------------- #
    #  Public helpers                                                #
    # -------------------------------------------------------------- #
    def place_tile(self, tile: Tile, col: int, row: int):
        if 0 <= col < self.cols and 0 <= row < self.rows:
            self.grid[row][col] = tile
            self._redraw()

    def toggle_grid(self):
        """Hide / show grid outlines (bound to the ‘g’ key)."""
        self.show_grid = not self.show_grid
        self._redraw()

    # -------------------------------------------------------------- #
    #  Mouse click                                                   #
    # -------------------------------------------------------------- #
    def _click(self, ev):
        if self.shape == "hex":
            col, row = self._hex_index(ev.x, ev.y)
        else:                                   # rect
            col, row = ev.x // CELL, ev.y // CELL

        sel = getattr(self.winfo_toplevel(), "selected_obj", None)
        if isinstance(sel, Tile):
            self.place_tile(sel.clone(), col, row)
            self.winfo_toplevel().selected_obj = None

    # -------------------------------------------------------------- #
    #  Drawing                                                       #
    # -------------------------------------------------------------- #
    def _redraw(self):
        self.delete("all")
        for r in range(self.rows):
            for c in range(self.cols):
                dx, dy = self._cell_origin(c, r)

                # draw outline only if enabled
                if self.show_grid:
                    if self.shape == "rect":
                        self.create_rectangle(dx, dy,
                                              dx + CELL, dy + CELL,
                                              outline="#cccccc")
                    else:                       # hex outline
                        self.create_polygon(self._hex_pts(dx, dy),
                                            outline="#cccccc", fill="")

                t = self.grid[r][c]
                if t:
                    self._sprite(dx, dy, t)

    # -------------- geometry helpers ------------------------------ #
    def _cell_origin(self, col: int, row: int) -> tuple[int, int]:
        if self.shape == "rect":
            return col * CELL, row * CELL
        # hex axial layout (point-top)
        dx = col * CELL * 0.75
        dy = row * CELL + (CELL // 2 if col % 2 else 0)
        return int(dx), int(dy)

    def _hex_pts(self, x: int, y: int):
        q = CELL // 4
        h = CELL // 2
        return (x + q,     y,
                x + q*3,   y,
                x + CELL,  y + h,
                x + q*3,   y + CELL,
                x + q,     y + CELL,
                x,         y + h)

    def _hex_index(self, px: int, py: int) -> tuple[int, int]:
        """
        Convert pixel (px,py) to (col,row) in a point-top axial hex grid
        that uses 0.75*CELL horizontal spacing.
        """
        col = int(px / (CELL * 0.75))
        col_x0 = col * CELL * 0.75
        row_offset = CELL // 2 if col % 2 else 0
        row = int((py - row_offset) / CELL)
        # clamp to bounds
        col = max(0, min(col, self.cols - 1))
        row = max(0, min(row, self.rows - 1))
        return col, row

    # -------------- sprite helpers ------------------------------- #
    def _sprite(self, x: int, y: int, t: Tile):
        if t.image_path:
            self.create_image(x, y, image=self._img(t.image_path), anchor="nw")
        else:
            pts = [(x + px, y + py) for px, py in t.points]
            self.create_polygon(*sum(pts, ()), outline=t.outline, fill=t.fill)

    def _img(self, path: str):
        if path in self._cache:
            return self._cache[path]

        try:
            im = Image.open(self.img_dir / path).resize((CELL, CELL),
                                                        Image.LANCZOS)
        except FileNotFoundError:
            # grey placeholder if file missing
            im = Image.new("RGBA", (CELL, CELL), "#bbbbbb")
        self._cache[path] = ImageTk.PhotoImage(im)
        return self._cache[path]

    # -------------------------------------------------------------- #
    #  Zoom-mixin callback                                           #
    # -------------------------------------------------------------- #
    def _zoom_changed(self, scale: float):
        global CELL
        CELL = int(64 * scale)
        self.config(width=self.cols * CELL, height=self.rows * CELL)
        self._redraw()
