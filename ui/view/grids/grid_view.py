"""Square‑grid board with stacks, adapted from the old *BoardView* but now built
on **BaseCanvasView** plus mix‑ins."""

from __future__ import annotations
import itertools, json, pathlib, tkinter as tk
from tkinter import messagebox
from typing import Dict, Tuple
from PIL import Image, ImageTk

from game.board  import Board, SectionType
from game.deck   import Deck
from game.card   import Card
from ..mixins import SectionMixin, ContextMenuMixin
from ..base import BaseCanvasView

CELL   = 64         # zoom‑scaled in _zoom_changed
OFFSET = 8
RADIUS = 10
PREVIEW_SCALE = 0.4

class GridView(SectionMixin, ContextMenuMixin, BaseCanvasView):
    def __init__(self, master, board: Board, img_dir: pathlib.Path):
        self.board   = board
        self.img_dir = img_dir
        super().__init__(master, board.WIDTH*CELL, board.HEIGHT*CELL,
                         palette=True, on_redraw=self._draw_all)

        # caches
        self._cache: Dict[str, ImageTk.PhotoImage] = {}
        self._preview_cache: Dict[str, ImageTk.PhotoImage] = {}

        # drag state
        self.drag_src: Tuple[int,int] | None = None

        # --- extra bindings (space cycling already in base) ----------- #
        self.bind("<B1-Motion>",       self._drag)
        # section‑mixin setup
        self._init_section_mixin(CELL, self.mode.get)  # type: ignore[arg-type]

    # ========================================================= drawing #
    def _draw_all(self):
        self._grid(); self._sections()
        for row in self.board.grid:
            for cell in row:
                for i, obj in enumerate(cell.stack):
                    self._draw_obj(cell.x, cell.y, obj, i*OFFSET)

    def _grid(self):
        for x in range(self.board.WIDTH + 1):
            self.create_line(x*CELL, 0, x*CELL, self.board.HEIGHT*CELL)
        for y in range(self.board.HEIGHT + 1):
            self.create_line(0, y*CELL, self.board.WIDTH*CELL, y*CELL)

    def _sections(self):
        colours = {SectionType.CARD:"blue", SectionType.PIECE:"green",
                   SectionType.TOKEN:"orange", SectionType.DECK:"purple",
                   SectionType.ANY:"gray"}
        for s in self.board.sections:
            pts = [(gx*CELL, gy*CELL) for gx,gy in s.points]
            self.create_polygon(*itertools.chain.from_iterable(pts),
                                outline=colours[s.kind], fill="",
                                dash=(4,2), width=2)

    def _draw_obj(self, gx:int, gy:int, obj, offset:int=0):
        x0,y0 = gx*CELL+offset, gy*CELL+offset
        if isinstance(obj, Deck):
            self.create_rectangle(x0+8,y0+8,x0+CELL-8,y0+CELL-8,
                                  fill="plum", outline="black")
            self.create_text(x0+CELL/2, y0+CELL/2, text=(obj.name or "Deck")[:8], fill="white")
            return
        if getattr(obj, "image_path", None):
            self.create_image(x0,y0, image=self._img(obj.image_path), anchor="nw")
        elif getattr(obj, "points", None):
            pts = [(x0+px, y0+py) for px,py in obj.points]
            self.create_polygon(*itertools.chain.from_iterable(pts), fill="khaki", outline="black")
        elif isinstance(obj, Card):
            self._rounded_rect(x0,y0)
        else:
            self.create_rectangle(x0,y0,x0+CELL,y0+CELL, fill="lightyellow", outline="black")
        self.create_text(x0+CELL/2,y0+CELL/2, text=obj.name[:6])

    def _rounded_rect(self,x:int,y:int):
        r=RADIUS;pts=[x+r,y, x+CELL-r,y, x+CELL,y, x+CELL,y+r, x+CELL,y+CELL-r,
                      x+CELL,y+CELL, x+CELL-r,y+CELL, x+r,y+CELL, x,y+CELL,
                      x,y+CELL-r, x,y+r, x,y]
        self.create_polygon(pts, smooth=True, fill="white", outline="black")

    def _img(self,name:str):
        if name not in self._cache:
            im = Image.open(self.img_dir/name).resize((CELL,CELL), Image.LANCZOS)
            self._cache[name]=ImageTk.PhotoImage(im)
        return self._cache[name]

    # ========================================================= mouse ----
    def _on_left(self, ev):
        gx,gy = ev.x//CELL, ev.y//CELL
        if not (0<=gx<self.board.WIDTH and 0<=gy<self.board.HEIGHT):
            return
        tool = self.mode.get()
        if tool == "erase":
            if self.board.remove_top(gx,gy): self.redraw()
            return
        if tool == "move":
            if self.board.grid[gy][gx].stack: self.drag_src = (gx,gy)
            return
        if tool == "place":
            sel = getattr(self.winfo_toplevel(), "selected_obj", None)
            if not sel: return
            placed = self.board.place(gx,gy, sel.clone() if isinstance(sel,Deck) else sel)
            if placed: self.redraw(); self._broadcast_place(sel,gx,gy)

    def _drag(self, ev):
        if self.mode.get()!="move" or not self.drag_src: return
        gx1,gy1 = ev.x//CELL, ev.y//CELL
        if not (0<=gx1<self.board.WIDTH and 0<=gy1<self.board.HEIGHT): return
        gx0,gy0 = self.drag_src
        if (gx1,gy1)!=(gx0,gy0):
            obj = self.board.remove_top(gx0,gy0)
            if obj and self.board.place(gx1,gy1,obj):
                self.drag_src = (gx1,gy1); self.redraw()

    def _on_drop(self, _):
        self.drag_src = None

    def _on_right(self, ev):
        gx,gy = ev.x//CELL, ev.y//CELL
        if not (0<=gx<self.board.WIDTH and 0<=gy<self.board.HEIGHT): return
        cell = self.board.grid[gy][gx]
        if not cell.stack: return
        top = cell.stack[-1]
        self._popup_common(ev, top, lambda: self.board.remove_top(gx,gy))

    # ------------------------------------------------ section‑mixin hooks --
    def _section_bounds_to_points(self,x0,y0,x1,y1):
        gx0,gy0 = x0//CELL, y0//CELL
        gx1,gy1 = x1//CELL, y1//CELL
        return [(gx0,gy0),(gx1+1,gy0),(gx1+1,gy1+1),(gx0,gy1+1)]

    def _add_section(self,name,kind,pts,outline,fill):
        self.board.add_section(name, SectionType(kind), pts, outline, fill)

    # ------------------------------------------------ misc --------------
    def _broadcast_place(self, sel, gx, gy):
        root = self.winfo_toplevel(); out_q = getattr(root,"out_q",None)
        if out_q:
            out_q.put(json.dumps({"act":"place","board":"Board","name":sel.name,"x":gx,"y":gy}))

    def _zoom_changed(self, scale:float):
        global CELL; CELL = int(64*scale)
        self.config(width=self.board.WIDTH*CELL, height=self.board.HEIGHT*CELL)
        self.redraw()
