from __future__ import annotations
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import pathlib, itertools
from typing import Dict

from game.card   import Card
from game.piece  import Piece
from game.token  import Token
from game.deck   import Deck
from game.board  import Board, SectionType


CELL   = 64
RADIUS = 10


class BoardView(tk.Canvas):
    """Grid canvas: left-click places, right-click removes / draws."""

    def __init__(self, master, board: Board,
                 images_dir: pathlib.Path,
                 on_place):
        w, h = board.WIDTH * CELL, board.HEIGHT * CELL
        super().__init__(master, width=w, height=h,
                         background="white", highlightthickness=0)
        self.board, self.imgdir, self.on_place = board, images_dir, on_place
        self._img_cache: Dict[str, ImageTk.PhotoImage] = {}

        self.mode       = "place"    # or "section"
        self.sec_start  = None

        self._redraw_all()

        self.bind("<Button-1>",       self._left_click)
        self.bind("<B1-Motion>",      self._drag)
        self.bind("<ButtonRelease-1>",self._release)
        self.bind("<Button-3>",       self._right_click)

    # ================= drawing ========================================= #
    def _redraw_all(self):
        self.delete("all")
        self._draw_grid()
        self._draw_sections()
        for row in self.board.grid:
            for cell in row:
                if cell.occupant:
                    self._draw_object(cell.x, cell.y, cell.occupant)

    def _draw_grid(self):
        for x in range(self.board.WIDTH + 1):
            self.create_line(x*CELL, 0, x*CELL, self.board.HEIGHT*CELL)
        for y in range(self.board.HEIGHT + 1):
            self.create_line(0, y*CELL, self.board.WIDTH*CELL, y*CELL)

    def _draw_sections(self):
        colours = {SectionType.CARD:"blue", SectionType.PIECE:"green",
                   SectionType.TOKEN:"orange", SectionType.DECK:"purple"}
        for s in self.board.sections:
            x0,y0 = s.x0*CELL, s.y0*CELL
            x1,y1 = (s.x1+1)*CELL, (s.y1+1)*CELL
            self.create_rectangle(x0,y0,x1,y1, dash=(4,2),
                                  outline=colours[s.kind])

    # ================= events ========================================== #
    def _left_click(self, ev):
        gx, gy = ev.x // CELL, ev.y // CELL
        if self.mode == "place":
            sel = getattr(self.winfo_toplevel(), "selected_obj", None)
            if sel and self.board.place(gx, gy, sel):
                self._draw_object(gx, gy, sel)
                self.on_place(gx, gy, sel)
        else:
            self.sec_start = (gx, gy)

    def _drag(self, ev):
        if self.mode != "section" or not self.sec_start:
            return
        self._redraw_all()
        x0,y0 = self.sec_start
        x1,y1 = ev.x//CELL, ev.y//CELL
        self.create_rectangle(x0*CELL, y0*CELL,
                              (x1+1)*CELL, (y1+1)*CELL,
                              dash=(2,2), outline="red")

    def _release(self, ev):
        if self.mode != "section" or not self.sec_start: return
        x0,y0 = self.sec_start; x1,y1 = ev.x//CELL, ev.y//CELL
        x0,x1 = sorted((x0,x1)); y0,y1 = sorted((y0,y1))
        from tkinter import simpledialog
        kind = simpledialog.askstring("Section Type",
                                      "Card / Piece / Token / Deck") or ""
        kind = kind.capitalize()
        if kind in ("Card","Piece","Token","Deck"):
            self.board.add_section(x0,y0,x1,y1, SectionType(kind))
        self.mode, self.sec_start = "place", None
        self._redraw_all()

    # ---------- NEW: right-click remove / draw ------------------------- #
    def _right_click(self, ev):
        gx, gy = ev.x // CELL, ev.y // CELL
        if not (0 <= gx < self.board.WIDTH and 0 <= gy < self.board.HEIGHT):
            return
        cell = self.board.grid[gy][gx]
        if not cell.occupant:
            return

        if isinstance(cell.occupant, Deck):
            deck = cell.occupant
            if deck.cards:
                card = deck.draw()
                messagebox.showinfo("Drew Card",
                                    f"{card.name}\n\n{card.description.strip()}")
            if not deck.cards:               # pile empty ➜ remove deck
                self.board.remove(gx, gy)
        else:
            self.board.remove(gx, gy)        # remove any other object

        self._redraw_all()

    # ================= shape/object drawing ============================ #
    def _draw_object(self, gx, gy, obj):
        x0, y0 = gx*CELL, gy*CELL

        if isinstance(obj, Deck):
            self.create_rectangle(x0+8, y0+8, x0+CELL-8, y0+CELL-8,
                                  fill="plum", outline="black")
            self.create_text(x0+CELL/2, y0+CELL/2, text="Deck", fill="white")
            return

        if getattr(obj, "image_path", None):
            img = self._img(obj.image_path); self.create_image(x0, y0, image=img, anchor="nw")
        elif getattr(obj, "points", None):
            pts = list(itertools.chain.from_iterable((x0+px, y0+py) for px,py in obj.points))
            self.create_polygon(pts, fill="khaki", outline="black")
        elif isinstance(obj, Card):
            self._round_rect(x0,y0,x0+CELL,y0+CELL,RADIUS, fill="white", outline="black")
        elif isinstance(obj, Token):
            self.create_oval(x0+6,y0+6,x0+CELL-6,y0+CELL-6, fill="khaki", outline="black")
        else:
            self.create_rectangle(x0,y0,x0+CELL,y0+CELL, fill="lightyellow")

        self.create_text(x0+CELL/2, y0+CELL/2, text=obj.name[:6])

    # ---------------- utils ------------------------------------------- #
    def _img(self, name):
        if name not in self._img_cache:
            img = Image.open(self.imgdir / name).resize((CELL, CELL), Image.LANCZOS)
            self._img_cache[name] = ImageTk.PhotoImage(img)
        return self._img_cache[name]

    def _round_rect(self,x1,y1,x2,y2,r,**kw):
        pts=[x1+r,y1,x2-r,y1,x2,y1,x2,y1+r,x2,y2-r,x2,y2,x2-r,y2,x1+r,y2,
             x1,y2,x1,y2-r,x1,y1+r,x1,y1]
        return self.create_polygon(pts, smooth=True, **kw)

    # ---------------- public ------------------------------------------ #
    def enter_section_mode(self):
        self.mode = "section"
