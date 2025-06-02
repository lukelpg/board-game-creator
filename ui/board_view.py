from __future__ import annotations
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import itertools, pathlib
from typing import Dict

from game.board  import Board, SectionType
from game.card   import Card
from game.piece  import Piece
from game.token  import Token
from game.deck   import Deck


CELL   = 64
OFFSET = 8     # pixel offset between stacked items
RADIUS = 10


class BoardView(tk.Canvas):
    """Left-click: place; Right-click: pop top; Shift-Right-click: clear stack."""

    def __init__(self, master, board: Board,
                 img_dir: pathlib.Path):
        super().__init__(master,
                         width=board.WIDTH*CELL,
                         height=board.HEIGHT*CELL,
                         background="white", highlightthickness=0)
        self.board, self.img_dir = board, img_dir
        self.cache: Dict[str, ImageTk.PhotoImage] = {}
        self._draw_all()

        self.bind("<Button-1>", self._left)
        self.bind("<Button-3>", self._right)

    # ------------ rendering ------------------------------------------- #
    def _draw_all(self):
        self.delete("all")
        self._grid(); self._sections()
        for row in self.board.grid:
            for cell in row:
                self._draw_stack(cell.x, cell.y, cell.stack)

    def _grid(self):
        for x in range(self.board.WIDTH+1):
            self.create_line(x*CELL, 0, x*CELL, self.board.HEIGHT*CELL)
        for y in range(self.board.HEIGHT+1):
            self.create_line(0, y*CELL, self.board.WIDTH*CELL, y*CELL)

    def _sections(self):
        colour = {SectionType.CARD:"blue", SectionType.PIECE:"green",
                  SectionType.TOKEN:"orange", SectionType.DECK:"purple",
                  SectionType.ANY:"gray"}
        for s in self.board.sections:
            x0,y0 = s.x0*CELL, s.y0*CELL
            x1,y1 = (s.x1+1)*CELL, (s.y1+1)*CELL
            self.create_rectangle(x0,y0,x1,y1, dash=(4,2), outline=colour[s.kind])

    def _draw_stack(self, gx, gy, stack):
        for idx,obj in enumerate(stack):
            x0 = gx*CELL + idx*OFFSET
            y0 = gy*CELL + idx*OFFSET
            self._draw_one(x0, y0, obj)

    def _draw_one(self, x0, y0, obj):
        if isinstance(obj, Deck):
            self.create_rectangle(x0+8,y0+8,x0+CELL-8,y0+CELL-8,
                                  fill="plum", outline="black")
            self.create_text(x0+CELL/2,y0+CELL/2,text="Deck",fill="white")
            return
        # prefer image
        if getattr(obj,"image_path",None):
            img=self._img(obj.image_path)
            self.create_image(x0,y0,image=img,anchor="nw")
        elif getattr(obj,"points",None):
            pts=list(itertools.chain.from_iterable((x0+px,y0+py) for px,py in obj.points))
            self.create_polygon(pts,fill="khaki",outline="black")
        elif isinstance(obj,Card):
            self._rounded(x0,y0)
        elif isinstance(obj,Token):
            self.create_oval(x0+6,y0+6,x0+CELL-6,y0+CELL-6,fill="khaki",outline="black")
        else:
            self.create_rectangle(x0,y0,x0+CELL,y0+CELL,fill="lightyellow")
        self.create_text(x0+CELL/2,y0+CELL/2,text=obj.name[:6])

    def _rounded(self,x,y):
        r=RADIUS; pts=[x+r,y,x+CELL-r,y,x+CELL,y,x+CELL,y+r,
                       x+CELL,y+CELL-r,x+CELL,y+CELL,x+CELL-r,y+CELL,
                       x+r,y+CELL,x,y+CELL,x,y+CELL-r,x,y+r,x,y]
        self.create_polygon(pts,smooth=True,fill="white",outline="black")

    def _img(self,name):
        if name not in self.cache:
            im=Image.open(self.img_dir/name).resize((CELL,CELL),Image.LANCZOS)
            self.cache[name]=ImageTk.PhotoImage(im)
        return self.cache[name]

    # ------------ events ---------------------------------------------- #
    def _left(self, ev):
        gx,gy=ev.x//CELL,ev.y//CELL
        sel=getattr(self.winfo_toplevel(),"selected_obj",None)
        if sel and self.board.place(gx,gy,sel):
            self._draw_all()

    def _right(self, ev):
        gx,gy=ev.x//CELL,ev.y//CELL
        if ev.state & 0x0001:         # Shift held: clear stack
            self.board.clear_cell(gx,gy)
        else:                         # pop top
            top=self.board.remove_top(gx,gy)
            if isinstance(top,Deck) and top.cards:
                card=top.draw()
                messagebox.showinfo("Drew",f"{card.name}\n\n{card.description}")
                if top.cards:                    # put deck back
                    self.board.place(gx,gy,top)
        self._draw_all()

    def enter_section_mode(self):
        """Switch the next left-drag into “draw a new section” mode."""
        self.mode = "section"
        self.sec_start = None
