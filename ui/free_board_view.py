from __future__ import annotations
import tkinter as tk
from tkinter import ttk, simpledialog, colorchooser, messagebox
from PIL import Image, ImageTk
import itertools, pathlib
from typing import Dict, List
from game.free_board import FreeBoard, Placed
from game.board       import SectionType

CELL = 64
OFFSET_SHADOW = 4

class FreeBoardView(tk.Canvas):
    """Canvas with free placement & drag-to-move."""

    # -------------------------------------------------------------- #
    def __init__(self, master, fb: FreeBoard, img_dir: pathlib.Path):
        super().__init__(master, width=fb.width, height=fb.height,
                         background="white", highlightthickness=0)

        self.fb = fb
        self.img_dir = img_dir
        self._cache: Dict[str, ImageTk.PhotoImage] = {}

        # tool mode
        self.mode = tk.StringVar(value="place")      # place/move/erase/draw
        self._build_tool_palette(master)

        # drag state
        self.drag: Placed | None = None
        self.dx = self.dy = 0

        # events
        self.bind("<Button-1>",       self._left)
        self.bind("<B1-Motion>",      self._move_drag)
        self.bind("<ButtonRelease-1>",self._drop)
        self.bind("<Button-3>",       self._popup)

        self.bind_all("<space>",      self._cycle_tool)

        self._redraw()

    # -------------------------------------------------------------- #
    def _build_tool_palette(self, master):
        bar = ttk.Frame(master)
        bar.pack(side="bottom", fill="x")
        for txt in ("place", "move", "erase"):
            ttk.Radiobutton(bar, text=txt.capitalize(),
                            value=txt, variable=self.mode).pack(side="left")
        ttk.Label(bar, text=" ⎵ cycles ").pack(side="right")

    # -------------------------------------------------------------- #
    def _redraw(self):
        self.delete("all")
        # sections (polygons)
        for s in self.fb.sections:
            pts=[(x*CELL,y*CELL) for x,y in s["points"]]
            self.create_polygon(*itertools.chain.from_iterable(pts),
                                outline=s["outline"], fill=s["fill"],
                                stipple="gray25" if s["fill"] else "",
                                width=2)
        # objects
        for p in self.fb.placed:
            self._sprite(p)

    def _sprite(self, p: Placed):
        obj = p.obj
        gx, gy = p.x, p.y
        if getattr(obj, "image_path", None):
            self.create_image(gx, gy, image=self._img(obj.image_path), anchor="nw")
        elif hasattr(obj, "points"):
            pts=[(gx+px,gy+py) for px,py in obj.points]
            self.create_polygon(*itertools.chain.from_iterable(pts),
                                fill="khaki", outline="black")
        else:
            self.create_rectangle(gx, gy, gx+CELL, gy+CELL,
                                  fill="lightyellow", outline="black")
            self.create_text(gx+CELL/2, gy+CELL/2, text=obj.name[:6])

    def _img(self, path:str):
        if path not in self._cache:
            self._cache[path]=ImageTk.PhotoImage(
                Image.open(self.img_dir/path).resize((CELL,CELL),Image.LANCZOS))
        return self._cache[path]

    # -------------------------------------------------------------- #
    #  mouse handlers
    def _left(self, ev):
        tool=self.mode.get()
        px,py=ev.x, ev.y

        if tool=="erase":
            hits=self.fb.objects_at(px,py)
            if hits: self.fb.remove(hits[-1]); self._redraw(); return

        if tool=="move":
            hits=self.fb.objects_at(px,py)
            if hits:
                self.drag=hits[-1]
                self.dx, self.dy = px-self.drag.x, py-self.drag.y
            return

        if tool=="place":
            sel=getattr(self.winfo_toplevel(),"selected_obj",None)
            if not sel: return
            self.fb.add(sel.clone() if hasattr(sel,"clone") else sel,
                        px, py)
            self._redraw()

    def _move_drag(self, ev):
        if self.mode.get()!="move" or not self.drag: return
        self.drag.x, self.drag.y = ev.x-self.dx, ev.y-self.dy
        self._redraw()

    def _drop(self, _ev):
        self.drag=None

    # -------------------------------------------------------------- #
    def _popup(self, ev):
        hits=self.fb.objects_at(ev.x,ev.y)
        if not hits: return
        top=hits[-1].obj
        menu=tk.Menu(self, tearoff=0)
        menu.add_command(label="Delete",
                         command=lambda h=hits[-1]: (self.fb.remove(h),
                                                     self._redraw()))
        if isinstance(top, Deck):
            menu.add_command(label="Draw",
                command=lambda d=top:self._draw_card(d))
            menu.add_command(label="Shuffle", command=lambda d=top:(d.shuffle(),self._redraw()))
            menu.add_command(label="Reset",   command=lambda d=top:(d.reset(),  self._redraw()))
        menu.tk_popup(ev.x_root, ev.y_root)

    def _draw_card(self, deck:Deck):
        if not deck.cards: return
        c=deck.draw()
        messagebox.showinfo("Drew", f"{c.name}\n\n{c.description}", parent=self)
        self._redraw()

    # -------------------------------------------------------------- #
    def _cycle_tool(self, _e):
        order=["place","move","erase"]
        cur=order.index(self.mode.get())
        self.mode.set(order[(cur+1)%len(order)])

    # -------------------------------------------------------------- #
    def enter_section_mode(self):
        # rectangle helper (same dialog as old)
        self.mode="section"
