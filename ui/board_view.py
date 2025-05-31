from __future__ import annotations
import tkinter as tk
from PIL import Image, ImageTk
from game.board import Board
from game.card  import Card
from game.piece import Piece
import pathlib

CELL = 64  # pixels

class BoardView(tk.Canvas):
    """Canvas that draws a board & its occupants."""

    def __init__(self, master, board: Board, images_dir: pathlib.Path,
                 on_place):
        w, h = board.WIDTH*CELL, board.HEIGHT*CELL
        super().__init__(master, width=w, height=h,
                         background="white", highlightthickness=0)
        self.board, self.imgdir, self.on_place = board, images_dir, on_place
        self._img_cache: dict[str, ImageTk.PhotoImage] = {}
        self._draw_grid()
        self.bind("<Button-1>", self._click)

    # ---------------- grid & redraw ------------------------------------ #
    def _draw_grid(self):
        self.delete("grid")      # clear previous
        for x in range(self.board.WIDTH+1):
            self.create_line(x*CELL, 0, x*CELL, self.board.HEIGHT*CELL, tags="grid")
        for y in range(self.board.HEIGHT+1):
            self.create_line(0, y*CELL, self.board.WIDTH*CELL, y*CELL, tags="grid")

    def refresh_board(self):
        self.config(width=self.board.WIDTH*CELL, height=self.board.HEIGHT*CELL)
        self.delete("piece")
        self._draw_grid()

    # ---------------- events ------------------------------------------- #
    def _click(self, ev):
        sel = getattr(self.winfo_toplevel(), "selected_obj", None)
        if not sel: return
        gx, gy = ev.x//CELL, ev.y//CELL
        if gx >= self.board.WIDTH or gy >= self.board.HEIGHT: return
        if self.board.place(gx, gy, sel):
            self._render(gx, gy, sel)
            self.on_place(gx, gy, sel)

    # ---------------- drawing occupants -------------------------------- #
    def _render(self, gx, gy, obj: Card | Piece):
        x0, y0 = gx*CELL, gy*CELL
        if obj.image_path:
            img = self._load_img(obj.image_path)
            self.create_image(x0, y0, image=img, anchor="nw", tags="piece")
        else:
            self.create_rectangle(x0, y0, x0+CELL, y0+CELL, fill="lightyellow",
                                  tags="piece")
            self.create_text(x0+CELL/2, y0+CELL/2, text=obj.name[:6], tags="piece")

    # ---------------- helpers ------------------------------------------ #
    def _load_img(self, name: str):
        if name not in self._img_cache:
            path = self.imgdir / name
            img = Image.open(path).resize((CELL, CELL), Image.LANCZOS)
            self._img_cache[name] = ImageTk.PhotoImage(img)
        return self._img_cache[name]
