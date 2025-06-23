# ui/free_board_view.py
from __future__ import annotations

import itertools, pathlib, json, tkinter as tk
from tkinter import ttk, simpledialog, colorchooser, messagebox
from typing import Dict, List
from PIL import Image, ImageTk

from game.free_board import FreeBoard, Placed
from game.deck       import Deck
from ui.view.zoom   import ZoomMixin      # Ctrl-wheel zoom mix-in

# ------------------------------------------------------------------ #
CELL = 64               # base sprite size (px) – updated by zoom
OFFSET_SHADOW = 4       # reserved for future drop shadow

# ------------------------------------------------------------------ #
class FreeBoardView(ZoomMixin, tk.Canvas):
    """Free-placement canvas (no grid) with move / erase / zoom / decks.
       Sends {'act':'place', …} JSON via root.out_q for multiplayer sync.
    """

    # -------------------------------------------------------------- #
    def __init__(self, master, fb: FreeBoard, img_dir: pathlib.Path):
        super().__init__(master, width=fb.width, height=fb.height,
                         background="white", highlightthickness=0)

        self.fb        = fb
        self.img_dir   = img_dir
        self.board_name = "Board"          # overwritten by play_window

        self._cache: Dict[str, ImageTk.PhotoImage]   = {}
        self._preview_cache: Dict[str, ImageTk.PhotoImage] = {}

        # tool: place / move / erase
        self.mode = tk.StringVar(value="place")

        # drag state
        self.drag: Placed | None = None
        self.dx = self.dy = 0

        # zoom
        self._bind_zoom()

        # mouse bindings
        self.bind("<Button-1>",        self._left)
        self.bind("<B1-Motion>",       self._move_drag)
        self.bind("<ButtonRelease-1>", self._drop)
        self.bind("<Button-3>",        self._popup)
        self.bind_all("<space>",       self._cycle_tool)
        self.bind("<Motion>",          self._mouse_move)

        # polygon-section helpers
        self.sec_start: tuple[int,int] | None = None

        self._build_tool_palette(master)
        self._redraw()

    # =========  UI  ================================================== #
    def _build_tool_palette(self, master):
        bar = ttk.Frame(master); bar.pack(side="bottom", fill="x")
        for txt in ("place", "move", "erase"):
            ttk.Radiobutton(bar, text=txt.capitalize(),
                            value=txt, variable=self.mode).pack(side="left")
        ttk.Label(bar, text="⎵ cycles  •  Ctrl+Wheel zoom").pack(side="right")

    def _cycle_tool(self, _e):
        order = ("place", "move", "erase")
        self.mode.set(order[(order.index(self.mode.get()) + 1) % len(order)])

    # =========  DRAW  ================================================= #
    def _redraw(self):
        self.delete("all")

        # sections (stored in board units)
        for s in self.fb.sections:
            pts = [(x*CELL, y*CELL) for x, y in s["points"]]
            self.create_polygon(*itertools.chain.from_iterable(pts),
                                outline=s["outline"],
                                fill=s["fill"],
                                stipple="gray25" if s["fill"] else "",
                                width=2)

        # objects
        for p in self.fb.placed:
            self._sprite(p)

    def _sprite(self, p: Placed):
        obj, x, y = p.obj, p.x, p.y
        if getattr(obj, "image_path", None):
            self.create_image(x, y, image=self._img(obj.image_path), anchor="nw")
        elif getattr(obj, "points", None):
            pts = [(x+px, y+py) for px,py in obj.points]
            self.create_polygon(*itertools.chain.from_iterable(pts),
                                fill="khaki", outline="black")
        else:
            self.create_rectangle(x, y, x+CELL, y+CELL,
                                  fill="lightyellow", outline="black")
        self.create_text(x+CELL/2, y+CELL/2, text=obj.name[:6])

    def _img(self, path:str):
        if path not in self._cache:
            im = Image.open(self.img_dir / path).resize((CELL, CELL), Image.LANCZOS)
            self._cache[path] = ImageTk.PhotoImage(im)
        return self._cache[path]

    # =========  MOUSE  =============================================== #
    def _left(self, ev):
        tool, px, py = self.mode.get(), ev.x, ev.y

        if tool == "erase":
            hits = self.fb.objects_at(px, py)
            if hits:
                self.fb.remove(hits[-1]); self._redraw()
            return

        if tool == "move":
            hits = self.fb.objects_at(px, py)
            if hits:
                self.drag = hits[-1]
                self.dx, self.dy = px - self.drag.x, py - self.drag.y
            return

        if tool == "place":
            sel = getattr(self.winfo_toplevel(), "selected_obj", None)
            if not sel: return
            self.fb.add(sel.clone() if hasattr(sel, "clone") else sel, px, py)
            self._broadcast_place(sel, px, py)
            self._redraw()

    def _move_drag(self, ev):
        if self.mode.get() != "move" or not self.drag: return
        self.drag.x, self.drag.y = ev.x - self.dx, ev.y - self.dy
        self._redraw()

    def _drop(self, _): self.drag = None

    # -- context menu -------------------------------------------------- #
    def _popup(self, ev):
        hits = self.fb.objects_at(ev.x, ev.y)
        if not hits: return
        top_p, obj = hits[-1], hits[-1].obj

        m = tk.Menu(self, tearoff=0)
        if isinstance(obj, Deck):
            m.add_command(label="Draw",    command=lambda d=obj: self._draw_card(d))
            m.add_separator()
            m.add_command(label="Shuffle", command=lambda d=obj:(d.shuffle(),self._redraw()))
            m.add_command(label="Reset",   command=lambda d=obj:(d.reset(),  self._redraw()))
            m.add_separator()
        m.add_command(label="Delete", command=lambda p=top_p:(self.fb.remove(p),self._redraw()))
        m.tk_popup(ev.x_root, ev.y_root)

    def _draw_card(self, deck: Deck):
        if not deck.cards:
            messagebox.showinfo("Deck empty", "This pile has no cards left.",
                                parent=self.winfo_toplevel())
            return
        c = deck.draw()
        messagebox.showinfo("Drew", f"{c.name}\n\n{c.description}", parent=self)
        self.winfo_toplevel().selected_obj = c
        self._redraw()

    # =========  SECTION (drag rectangle)  ============================ #
    def enter_section_mode(self):
        self.mode.set("section")
        self.sec_start = None
        self.bind("<Button-1>",        self._sec_start)
        self.bind("<B1-Motion>",       self._sec_drag)
        self.bind("<ButtonRelease-1>", self._sec_release)

    def _sec_start(self, ev): self.sec_start = (ev.x, ev.y)

    def _sec_drag(self, ev):
        self._redraw()
        if not self.sec_start: return
        x0,y0 = self.sec_start; x1,y1 = ev.x, ev.y
        self.create_rectangle(x0,y0,x1,y1, dash=(2,2), outline="red")

    def _sec_release(self, ev):
        if not self.sec_start: return
        x0,y0 = self.sec_start; x1,y1 = ev.x, ev.y
        if abs(x1-x0)<10 or abs(y1-y0)<10:
            self._reset_sec_binds(); return

        gx0,gy0 = x0//CELL, y0//CELL
        gx1,gy1 = x1//CELL, y1//CELL
        pts = [(gx0,gy0),(gx1,gy0),(gx1,gy1),(gx0,gy1)]

        name = simpledialog.askstring("Section name","Name:",parent=self) or "Area"
        kind = simpledialog.askstring("Type","card/piece/token/deck/any:",
                                      initialvalue="Any",parent=self) or "Any"
        outline = colorchooser.askcolor(title="Outline")[1] or "#808080"
        fill    = colorchooser.askcolor(title="Fill (cancel = none)")[1] or ""

        self.fb.sections.append(dict(name=name, kind=kind.capitalize(),
                                     points=pts, outline=outline, fill=fill))
        self._reset_sec_binds(); self._redraw()

    def _reset_sec_binds(self):
        self.sec_start = None
        self.unbind("<Button-1>"); self.unbind("<B1-Motion>"); self.unbind("<ButtonRelease-1>")
        self.bind("<Button-1>", self._left)
        self.bind("<B1-Motion>", self._move_drag)
        self.bind("<ButtonRelease-1>", self._drop)
        self.mode.set("place")

    # =========  Mouse-move preview =================================== #
    def _mouse_move(self, ev):
        self.delete("cursor_preview")
        sel = getattr(self.winfo_toplevel(), "selected_obj", None)
        if sel:
            self.create_image(ev.x, ev.y,
                              image=self._preview_img(sel),
                              anchor="center", tags="cursor_preview")

    def _preview_img(self, obj):
        key = f"prev::{getattr(obj,'image_path', obj.name)}"
        if key in self._preview_cache:
            return self._preview_cache[key]
        im = (Image.open(self.img_dir / obj.image_path)
              if getattr(obj, "image_path", None)
              else Image.new("RGBA",(CELL,CELL),"#aaaaaa88"))
        im = im.resize((int(CELL*0.4), int(CELL*0.4)), Image.LANCZOS)
        self._preview_cache[key] = ImageTk.PhotoImage(im); return self._preview_cache[key]

    # =========  Multiplayer broadcast & zoom callback ================ #
    def _broadcast_place(self, sel, x, y):
        out_q = getattr(self.winfo_toplevel(), "out_q", None)
        if out_q:
            out_q.put(json.dumps({"act":"place","board":self.board_name,
                                  "name":sel.name,"x":x,"y":y}))

    def _zoom_changed(self, scale):
        global CELL
        CELL = int(64 * scale)
        self._redraw()
