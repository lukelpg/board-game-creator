from __future__ import annotations
import tkinter as tk
from tkinter import messagebox, simpledialog
from PIL import Image, ImageTk
import itertools, pathlib
from typing import Dict

from game.board  import Board, SectionType
from game.card   import Card
from game.piece  import Piece
from game.token  import Token
from game.deck   import Deck


CELL, OFFSET, RADIUS = 64, 8, 10


class BoardView(tk.Canvas):
    """Left-click: place • Right-click: pop/draw •
       Ctrl-Right: shuffle • Alt-Right: reset deck • Shift-Right: section edit"""

    def __init__(self, master, board: Board, img_dir: pathlib.Path):
        super().__init__(master, width=board.WIDTH*CELL, height=board.HEIGHT*CELL,
                         background="white", highlightthickness=0)
        self.board, self.img_dir = board, img_dir
        self.cache: Dict[str, ImageTk.PhotoImage] = {}
        self.mode = "place"
        self.sec_start = None
        self._redraw_all()

        self.bind("<Button-1>", self._left)
        self.bind("<ButtonRelease-1>", self._release)
        self.bind("<B1-Motion>", self._drag)
        self.bind("<Button-3>", self._right)

    # ================= drawing ========================================= #
    def _redraw_all(self):
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
        colour={SectionType.CARD:"blue",SectionType.PIECE:"green",
                SectionType.TOKEN:"orange",SectionType.DECK:"purple",
                SectionType.ANY:"gray"}
        for s in self.board.sections:
            self.create_rectangle(s.x0*CELL, s.y0*CELL,
                                  (s.x1+1)*CELL, (s.y1+1)*CELL,
                                  dash=(4,2), outline=colour[s.kind], tags="sec")

    def _draw_stack(self, gx, gy, stack):
        for idx,obj in enumerate(stack):
            self._draw_obj(gx*CELL+idx*OFFSET, gy*CELL+idx*OFFSET, obj)

    def _draw_obj(self, x0, y0, obj):
        if isinstance(obj, Deck):
            self.create_rectangle(x0+8, y0+8, x0+CELL-8, y0+CELL-8,
                                  fill="plum", outline="black")
            label = (obj.name or "Deck")[:8]
            self.create_text(x0+CELL/2, y0+CELL/2, text=label, fill="white")
            return
        if getattr(obj,"image_path",None):
            self.create_image(x0,y0, image=self._img(obj.image_path), anchor="nw")
        elif getattr(obj,"points",None):
            pts=[(x0+px,y0+py) for px,py in obj.points]
            self.create_polygon(list(itertools.chain.from_iterable(pts)),
                                fill="khaki", outline="black")
        elif isinstance(obj,Card):
            self._rounded(x0,y0)
        elif isinstance(obj,Token):
            self.create_oval(x0+6,y0+6,x0+CELL-6,y0+CELL-6,
                             fill="khaki", outline="black")
        else:
            self.create_rectangle(x0,y0,x0+CELL,y0+CELL, fill="lightyellow")
        self.create_text(x0+CELL/2, y0+CELL/2, text=obj.name[:6])

    def _rounded(self,x,y):
        r=RADIUS; pts=[x+r,y,x+CELL-r,y,x+CELL,y,x+CELL,y+r,
                       x+CELL,y+CELL-r,x+CELL,y+CELL,x+CELL-r,y+CELL,
                       x+r,y+CELL,x,y+CELL,x,y+CELL-r,x,y+r,x,y]
        self.create_polygon(pts,smooth=True,fill="white",outline="black")

    def _img(self,name):
        if name not in self.cache:
            self.cache[name]=ImageTk.PhotoImage(
                Image.open(self.img_dir/name).resize((CELL,CELL),Image.LANCZOS))
        return self.cache[name]

    # ================= placement ======================================= #
    def _left(self, ev):
        gx,gy=ev.x//CELL, ev.y//CELL
        if self.mode=="place":
            sel=getattr(self.winfo_toplevel(),"selected_obj",None)
            if sel and self.board.place(gx,gy,sel.clone() if isinstance(sel,Deck) else sel):
                self._redraw_all()
        else:                               # section start
            self.sec_start=(gx,gy)

    def _drag(self, ev):
        if self.mode!="section" or not self.sec_start:return
        self._redraw_all()
        x0,y0=self.sec_start;x1,y1=ev.x//CELL,ev.y//CELL
        self.create_rectangle(x0*CELL,y0*CELL,(x1+1)*CELL,(y1+1)*CELL,
                              dash=(2,2),outline="red")

    def _release(self, ev):
        if self.mode!="section" or not self.sec_start:return
        x0,y0=self.sec_start;x1,y1=ev.x//CELL,ev.y//CELL
        x0,x1=sorted((x0,x1));y0,y1=sorted((y0,y1))
        kind=simpledialog.askstring("Section Type",
                                    "Card / Piece / Token / Deck / Any") or ""
        kind=kind.capitalize()
        if kind in ("Card","Piece","Token","Deck","Any"):
            self.board.add_section(x0,y0,x1,y1,SectionType(kind))
        self.mode="place"; self.sec_start=None; self._redraw_all()

    # ================= right-click menu =============================== #
    def _right(self, ev):
        gx,gy=ev.x//CELL, ev.y//CELL

        # ------- modifier: Shift  → edit / delete section -------------- #
        if ev.state & 0x0001:                # Shift
            sec=self._find_sec(gx,gy)
            if not sec: return
            choice=simpledialog.askstring("Section",
                      "delete / card / piece / token / deck / any",
                      initialvalue=sec.kind.value)
            if not choice: return
            choice=choice.capitalize()
            if choice=="Delete":
                self.board.sections.remove(sec)
            elif choice in ("Card","Piece","Token","Deck","Any"):
                sec.kind=SectionType(choice)
            self._redraw_all(); return

        cell=self.board.grid[gy][gx]
        if not cell.stack: return
        top=cell.stack[-1]

        # ------- Ctrl  → shuffle deck ---------------------------------- #
        if isinstance(top,Deck) and (ev.state & 0x0004):   # Ctrl
            top.shuffle(); self._redraw_all(); return

        # ------- Alt   → reset deck ------------------------------------ #
        if isinstance(top,Deck) and (ev.state & 0x0008):   # Alt
            top.reset(); self._redraw_all(); return

        # ------- default ----------------------------------------------- #
        popped=self.board.remove_top(gx,gy)
        if isinstance(popped,Deck):
            if popped.cards:
                card=popped.draw()
                messagebox.showinfo("Drew",f"{card.name}\n\n{card.description}")
                if popped.cards:                # put deck back if still cards
                    self.board.place(gx,gy,popped)
        self._redraw_all()

    # ================= helpers ======================================== #
    def _find_sec(self,gx,gy):
        for s in self.board.sections:
            if s.x0<=gx<=s.x1 and s.y0<=gy<=s.y1:
                return s

    def enter_section_mode(self):
        self.mode="section"
