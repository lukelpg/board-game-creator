from __future__ import annotations
import PySimpleGUI as sg
from game.board import Board
from game.card import Card
from typing import Callable

CELL = 64  # pixels

class BoardView:
    """Draws the grid and handles drag-n-drop placement."""

    def __init__(self, board: Board, on_place: Callable[[int,int,Card],None]):
        self.board = board
        self.on_place = on_place
        self._build_layout()

    def layout(self):
        return self.graph

    # -------- internals --------------------------------------------------
    def _build_layout(self):
        w, h = Board.WIDTH * CELL, Board.HEIGHT * CELL
        self.graph = sg.Graph(
            canvas_size=(w, h),
            graph_bottom_left=(0, 0),
            graph_top_right=(w, h),
            background_color="white",
            enable_events=True,
            drag_submits=True,
            key="-GRAPH-",
        )
        self._draw_grid()

    def _draw_grid(self):
        for x in range(Board.WIDTH + 1):
            self.graph.draw_line((x*CELL, 0), (x*CELL, Board.HEIGHT*CELL))
        for y in range(Board.HEIGHT + 1):
            self.graph.draw_line((0, y*CELL), (Board.WIDTH*CELL, y*CELL))

    # -------- events -----------------------------------------------------
    def read_event(self, event, values, selected_card: Card | None):
        if event == "-GRAPH-" and selected_card:
            x, y = values["-GRAPH-"]
            gx, gy = int(x // CELL), int(y // CELL)
            if self.board.place(gx, gy, selected_card):
                self._render_card(gx, gy, selected_card)
                self.on_place(gx, gy, selected_card)

    def _render_card(self, gx, gy, card):
        tl = (gx*CELL, gy*CELL)
        br = ((gx+1)*CELL, (gy+1)*CELL)
        self.graph.draw_rectangle(tl, br, fill_color="lightyellow")
        self.graph.draw_text(card.name[:6], location=(tl[0]+CELL/2, tl[1]+CELL/2))
