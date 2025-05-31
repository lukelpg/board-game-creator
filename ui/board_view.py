from __future__ import annotations
import tkinter as tk
from game.board import Board
from game.card  import Card

CELL = 64  # pixels

class BoardView(tk.Canvas):
    """Central board grid & placement logic."""

    def __init__(self, master, board: Board,
                 on_place, *args, **kwargs):
        w, h = Board.WIDTH*CELL, Board.HEIGHT*CELL
        super().__init__(master, width=w, height=h,
                         background="white", highlightthickness=0,
                         *args, **kwargs)
        self.board = board
        self.on_place = on_place
        self._draw_grid()
        self.bind("<Button-1>", self._click)

    # ------------------------------------------------------------------ #
    def _draw_grid(self):
        for x in range(Board.WIDTH+1):
            self.create_line(x*CELL, 0, x*CELL, Board.HEIGHT*CELL)
        for y in range(Board.HEIGHT+1):
            self.create_line(0, y*CELL, Board.WIDTH*CELL, y*CELL)

    # ------------------------------------------------------------------ #
    def _click(self, event):
        card = self.master.selected_card       # set by main_window
        if not card:
            return
        gx, gy = event.x//CELL, event.y//CELL
        if self.board.place(gx, gy, card):
            self._render_card(gx, gy, card)
            self.on_place(gx, gy, card)

    # ------------------------------------------------------------------ #
    def _render_card(self, gx, gy, card: Card):
        x0, y0 = gx*CELL, gy*CELL
        x1, y1 = x0+CELL, y0+CELL
        self.create_rectangle(x0, y0, x1, y1, fill="light yellow")
        self.create_text(x0+CELL/2, y0+CELL/2, text=card.name[:6])
