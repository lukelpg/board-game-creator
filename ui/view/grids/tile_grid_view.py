from __future__ import annotations
import pathlib, tkinter as tk
from typing import Dict, List
from PIL import Image, ImageTk

from game.tile import Tile, CELL as GAME_CELL
from ..base import BaseCanvasView
from ..mixins import ContextMenuMixin
from .hex_grid import cell_origin as hex_origin, hex_points, pixel_to_hex

CELL = GAME_CELL     # will track zoom

class TileGridView(ContextMenuMixin, BaseCanvasView):
    """Rect‑ or hex‑tile board that zooms, allows placement, and optional grid."""

    def __init__(self, master, tileset: List[Tile], cols:int, rows:int,
                 img_dir: pathlib.Path, shape:str="hex", show_grid:bool=True):
        if cols<1 or rows<1: raise ValueError("cols/rows must be >0")
        self.tileset = tileset; self.cols,self.rows = cols,rows
        self.shape   = shape.lower(); self.show_grid=show_grid
        self.grid: list[list[Tile|None]] = [[None]*cols for _ in range(rows)]
        self.img_dir = img_dir; self._cache: Dict[str,ImageTk.PhotoImage] = {}
        super().__init__(master, cols*CELL, rows*CELL, palette=True, on_redraw=self._draw)

    # ----------------------------------------------------------- public #
    def place_tile(self, tile: Tile, col:int, row:int):
        if 0<=col<self.cols and 0<=row<self.rows:
            self.grid[row][col]=tile; self.redraw()

    # ----------------------------------------------------------- drawing #
    def _draw(self):
        for r in range(self.rows):
            for c in range(self.cols):
                dx,dy = self._cell_origin(c,r)
                if self.show_grid:
                    if self.shape=="rect":
                        self.create_rectangle(dx,dy, dx+CELL,dy+CELL, outline="#cccccc")
                    else:
                        self.create_polygon(hex_points(dx,dy), outline="#cccccc", fill="")
                t=self.grid[r][c]
                if t: self._sprite(dx,dy,t)

    def _sprite(self,x:int,y:int,t:Tile):
        if t.image_path:
            self.create_image(x,y, image=self._img(t.image_path), anchor="nw")
        else:
            pts=[(x+px,y+py) for px,py in t.points]
            self.create_polygon(*sum(pts,()), outline=t.outline, fill=t.fill)

    def _img(self,path:str):
        if path not in self._cache:
            try:
                im = Image.open(self.img_dir/path).resize((CELL,CELL), Image.LANCZOS)
            except FileNotFoundError:
                from PIL import ImageDraw
                im = Image.new("RGBA",(CELL,CELL),"#bbbbbb"); ImageDraw.Draw(im).text((4,4),"?")
            self._cache[path]=ImageTk.PhotoImage(im)
        return self._cache[path]

    # ----------------------------------------------------------- geometry #
    def _cell_origin(self,col:int,row:int):
        return (col*CELL, row*CELL) if self.shape=="rect" else hex_origin(col,row)

    # ----------------------------------------------------------- mouse ----
    def _on_left(self, ev):
        col,row = (ev.x//CELL, ev.y//CELL) if self.shape=="rect" else pixel_to_hex(ev.x,ev.y,self.cols,self.rows)
        sel = getattr(self.winfo_toplevel(), "selected_obj", None)
        if isinstance(sel, Tile):
            self.place_tile(sel.clone(), col,row)
            self.winfo_toplevel().selected_obj=None

    def _on_right(self, ev):
        col,row = (ev.x//CELL, ev.y//CELL) if self.shape=="rect" else pixel_to_hex(ev.x,ev.y,self.cols,self.rows)
        if not (0<=col<self.cols and 0<=row<self.rows): return
        tile = self.grid[row][col]
        if tile:
            self._popup_common(ev, tile, lambda: self._delete_tile(col,row))

    def _delete_tile(self,col,row):
        self.grid[row][col]=None

    # ----------------------------------------------------------- zoom ----
    def _zoom_changed(self, scale:float):
        global CELL; CELL=int(64*scale)
        self.config(width=self.cols*CELL, height=self.rows*CELL)
        self.redraw()
