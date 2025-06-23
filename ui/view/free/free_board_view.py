from __future__ import annotations
import itertools, json, pathlib, tkinter as tk
from tkinter import messagebox
from typing import Dict
from PIL import Image, ImageTk

from game.free_board import FreeBoard, Placed
from game.deck       import Deck
from ..mixins import SectionMixin, ContextMenuMixin
from ..base import BaseCanvasView

CELL = 64     # updated on zoom

class FreeBoardView(SectionMixin, ContextMenuMixin, BaseCanvasView):
    """Free‑placement canvas with move / erase / zoom / deck support."""

    def __init__(self, master, fb: FreeBoard, img_dir: pathlib.Path):
        self.fb      = fb;     self.img_dir = img_dir
        self._cache: Dict[str,ImageTk.PhotoImage] = {}
        self._preview_cache: Dict[str,ImageTk.PhotoImage] = {}
        self.drag: Placed|None = None; self.dx=self.dy=0
        super().__init__(master, fb.width, fb.height, palette=True, on_redraw=self._draw)

        self.bind("<B1-Motion>", self._move_drag)
        # section‑mixin init
        self._init_section_mixin(CELL, self.mode.get)  # type: ignore[arg-type]

    # ----------------------------------------------------- drawing ----
    def _draw(self):
        # sections
        for s in self.fb.sections:
            pts=[(x*CELL,y*CELL) for x,y in s["points"]]
            self.create_polygon(*itertools.chain.from_iterable(pts), outline=s["outline"], fill=s["fill"],
                                stipple="gray25" if s["fill"] else "", width=2)
        # objects
        for p in self.fb.placed: self._sprite(p)

    def _sprite(self,p:Placed):
        obj,x,y = p.obj,p.x,p.y
        if getattr(obj,"image_path",None):
            self.create_image(x,y, image=self._img(obj.image_path), anchor="nw")
        elif getattr(obj,"points",None):
            pts=[(x+px,y+py) for px,py in obj.points]
            self.create_polygon(*itertools.chain.from_iterable(pts), fill="khaki", outline="black")
        else:
            self.create_rectangle(x,y,x+CELL,y+CELL, fill="lightyellow", outline="black")
        self.create_text(x+CELL/2,y+CELL/2,text=obj.name[:6])

    def _img(self,path:str):
        if path not in self._cache:
            im = Image.open(self.img_dir/path).resize((CELL,CELL), Image.LANCZOS)
            self._cache[path]=ImageTk.PhotoImage(im)
        return self._cache[path]

    # ----------------------------------------------------- mouse ----
    def _on_left(self, ev):
        tool = self.mode.get(); px,py = ev.x,ev.y
        if tool=="erase":
            hits=self.fb.objects_at(px,py);  (self.fb.remove(hits[-1]),self.redraw()) if hits else None; return
        if tool=="move":
            hits=self.fb.objects_at(px,py);  (setattr(self,"drag",hits[-1]), self._set_dxdy(px,py)) if hits else None; return
        if tool=="place":
            sel=getattr(self.winfo_toplevel(),"selected_obj",None)
            if sel:
                self.fb.add(sel.clone() if hasattr(sel,"clone") else sel, px,py)
                self._broadcast_place(sel,px,py); self.redraw()

    def _set_dxdy(self,px,py):
        if self.drag: self.dx, self.dy = px-self.drag.x, py-self.drag.y

    def _move_drag(self, ev):
        if self.mode.get()!="move" or not self.drag: return
        self.drag.x, self.drag.y = ev.x-self.dx, ev.y-self.dy; self.redraw()

    def _on_drop(self,_): self.drag=None

    def _on_right(self, ev):
        hits=self.fb.objects_at(ev.x,ev.y)
        if hits: self._popup_common(ev, hits[-1].obj, lambda:self.fb.remove(hits[-1]))

    # ------------------------------------------------ section hooks ----
    def _section_bounds_to_points(self,x0,y0,x1,y1):
        gx0,gy0 = x0//CELL, y0//CELL;  gx1,gy1 = x1//CELL, y1//CELL
        return [(gx0,gy0),(gx1,gy0),(gx1,gy1),(gx0,gy1)]

    def _add_section(self,name,kind,pts,outline,fill):
        self.fb.sections.append(dict(name=name,kind=kind,points=pts,outline=outline,fill=fill))

    # ------------------------------------------------ misc --------------
    def _draw_card(self, deck: Deck):
        if not deck.cards:
            messagebox.showinfo("Deck empty","This pile has no cards left.", parent=self.winfo_toplevel()); return
        c=deck.draw(); messagebox.showinfo("Drew",f"{c.name}\n\n{c.description}",parent=self)
        self.winfo_toplevel().selected_obj=c

    def _broadcast_place(self, sel,x,y):
        out_q=getattr(self.winfo_toplevel(),"out_q",None)
        if out_q: out_q.put(json.dumps({"act":"place","board":"Board","name":sel.name,"x":x,"y":y}))

    def _zoom_changed(self, scale):
        global CELL; CELL=int(64*scale); self.redraw()
