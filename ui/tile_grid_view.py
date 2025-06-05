from __future__ import annotations
import tkinter as tk, pathlib
from typing import Dict, List
from PIL import Image, ImageTk
from game.tile import Tile, CELL

class TileGridView(tk.Canvas):
    def __init__(self, master, tileset: List[Tile],
                 cols: int, rows: int, img_dir: pathlib.Path):
        super().__init__(master, width=cols*CELL, height=rows*CELL,
                         bg="white", highlightthickness=0)
        
        if cols is None or rows is None:
            raise ValueError("cols and rows must be integers > 0")
        
        self.tileset = tileset
        self.cols, self.rows = cols, rows
        self.grid: list[list[Tile|None]] = [[None]*cols for _ in range(rows)]
        self.img_dir = img_dir
        self._cache: Dict[str,ImageTk.PhotoImage] = {}
        self.bind("<Button-1>", self._click)
        self._redraw()

    # -------------------------------------------------------------- #
    def place_tile(self, tile: Tile, col:int, row:int):
        self.grid[row][col] = tile
        self._redraw()

    # -------------------------------------------------------------- #
    def _click(self, ev):
        col, row = ev.x//CELL, ev.y//CELL
        sel = getattr(self.winfo_toplevel(), "selected_obj", None)
        if isinstance(sel, Tile):
            self.grid[row][col] = sel.clone()
            self.winfo_toplevel().selected_obj = None
            self._redraw()

    # -------------------------------------------------------------- #
    def _redraw(self):
        self.delete("all")
        for r in range(self.rows):
            for c in range(self.cols):
                dx = c * CELL * 0.75
                dy = r * CELL + (CELL // 2 if c % 2 else 0) 
                self.create_rectangle(dx, dy, dx+CELL, dy+CELL, outline="#cccccc")
                t = self.grid[r][c]
                if t:
                    self._sprite(dx, dy, t)

    def _sprite(self, x, y, t: Tile):
        if t.image_path:
            self.create_image(x, y, image=self._img(t.image_path), anchor="nw")
        else:
            pts=[(x+px, y+py) for px,py in t.points]
            self.create_polygon(*sum(pts,()),
                                outline=t.outline, fill=t.fill)

    def _img(self, path:str):
        if path not in self._cache:
            im = Image.open(self.img_dir/path).resize((CELL,CELL), Image.LANCZOS)
            self._cache[path]=ImageTk.PhotoImage(im)
        return self._cache[path]
