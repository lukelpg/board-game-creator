# ui/board_view.py
from __future__ import annotations

import itertools, pathlib, tkinter as tk
from tkinter import ttk, simpledialog, colorchooser, messagebox
from typing import Dict, List, Tuple

from PIL import Image, ImageTk

from game.board  import Board, SectionType
from game.card   import Card
from game.piece  import Piece
from game.token  import Token
from game.deck   import Deck

# -------------------------------------------------------------------- #
CELL   = 64
OFFSET = 8
RADIUS = 10
PREVIEW_SCALE = 0.4                # cursor-preview sprite scale


# -------------------------------------------------------------------- #
class BoardView(tk.Canvas):
    """
    Grid canvas with stacks, drag-to-move, erase, deck draw → cursor.

    • Radio palette bottom-left: Place / Move / Erase   (Space cycles)
    • Right-click deck  → pop card + auto-select
    • Selected object follows cursor as translucent preview
    """

    # ================================================================ #
    def __init__(self, master, board: Board, img_dir: pathlib.Path):
        super().__init__(master, width=board.WIDTH * CELL,
                         height=board.HEIGHT * CELL,
                         background="white", highlightthickness=0)

        self.board   = board
        self.img_dir = img_dir
        self._cache: Dict[str, ImageTk.PhotoImage] = {}
        self._preview_cache: Dict[str, ImageTk.PhotoImage] = {}

        # ---- tool mode --------------------------------------------- #
        self.mode = tk.StringVar(value="place")      # place / move / erase
        self._build_palette(master)

        # ---- drag state -------------------------------------------- #
        self.drag_src: Tuple[int, int] | None = None

        # ---- bindings ---------------------------------------------- #
        self.bind("<Button-1>",        self._left)
        self.bind("<B1-Motion>",       self._drag)
        self.bind("<ButtonRelease-1>", self._drop)
        self.bind("<Button-3>",        self._right)

        self.bind_all("<space>",       self._cycle_tool)
        self.bind("<Motion>",          self._mouse_move)

        self._redraw_all()

    # ---------------------------------------------------------------- #
    def _build_palette(self, master):
        bar = ttk.Frame(master); bar.pack(side="bottom", fill="x")
        for txt in ("place", "move", "erase"):
            ttk.Radiobutton(bar, text=txt.capitalize(),
                            value=txt, variable=self.mode).pack(side="left")
        ttk.Label(bar, text=" ⎵ cycles ").pack(side="right")

    def _cycle_tool(self, _e):
        order = ("place", "move", "erase")
        cur   = order.index(self.mode.get())
        self.mode.set(order[(cur + 1) % len(order)])

    # ================================================================ #
    #  Main redraw                                                     #
    # ================================================================ #
    def _redraw_all(self):
        self.delete("all")
        self._grid(); self._sections()
        for row in self.board.grid:
            for cell in row:
                for i, obj in enumerate(cell.stack):
                    self._draw_obj(cell.x, cell.y, obj, i * OFFSET)

    def _grid(self):
        for x in range(self.board.WIDTH + 1):
            self.create_line(x * CELL, 0,
                             x * CELL, self.board.HEIGHT * CELL)
        for y in range(self.board.HEIGHT + 1):
            self.create_line(0, y * CELL,
                             self.board.WIDTH * CELL, y * CELL)

    def _sections(self):
        colour = {SectionType.CARD: "blue", SectionType.PIECE: "green",
                  SectionType.TOKEN: "orange", SectionType.DECK: "purple",
                  SectionType.ANY: "gray"}
        for s in self.board.sections:
            pts = [(gx * CELL, gy * CELL) for gx, gy in s.points]
            self.create_polygon(
                *itertools.chain.from_iterable(pts),
                outline=colour[s.kind],
                fill="",
                dash=(4, 2),
                width=2)

    # ================================================================ #
    #  Drawing helpers                                                 #
    # ================================================================ #
    def _draw_obj(self, gx: int, gy: int, obj, offset: int = 0):
        x0, y0 = gx * CELL + offset, gy * CELL + offset

        if isinstance(obj, Deck):
            self.create_rectangle(x0 + 8, y0 + 8, x0 + CELL - 8, y0 + CELL - 8,
                                  fill="plum", outline="black")
            self.create_text(x0 + CELL / 2, y0 + CELL / 2,
                             text=(obj.name or "Deck")[:8], fill="white")
            return

        if getattr(obj, "image_path", None):
            self.create_image(x0, y0, image=self._img(obj.image_path),
                              anchor="nw")
        elif getattr(obj, "points", None):           # polygon token/piece
            pts = [(x0 + px, y0 + py) for px, py in obj.points]
            self.create_polygon(
                *itertools.chain.from_iterable(pts),
                fill="khaki", outline="black")
        elif isinstance(obj, Card):
            self._rounded(x0, y0)
        else:  # generic
            self.create_rectangle(x0, y0, x0 + CELL, y0 + CELL,
                                  fill="lightyellow", outline="black")
        self.create_text(x0 + CELL / 2, y0 + CELL / 2, text=obj.name[:6])

    def _rounded(self, x: int, y: int):
        r = RADIUS
        pts = [x + r, y, x + CELL - r, y, x + CELL, y,
               x + CELL, y + r, x + CELL, y + CELL - r, x + CELL, y + CELL,
               x + CELL - r, y + CELL, x + r, y + CELL,
               x, y + CELL, x, y + CELL - r, x, y + r, x, y]
        self.create_polygon(pts, smooth=True, fill="white", outline="black")

    def _img(self, name: str):
        if name not in self._cache:
            im = Image.open(self.img_dir / name).resize((CELL, CELL), Image.LANCZOS)
            self._cache[name] = ImageTk.PhotoImage(im)
        return self._cache[name]

    # ================================================================ #
    #  Mouse handlers                                                  #
    # ================================================================ #
    def _left(self, ev):
        gx, gy = ev.x // CELL, ev.y // CELL
        tool = self.mode.get()

        if tool == "erase":
            if self.board.remove_top(gx, gy):
                self._redraw_all()
            return

        if tool == "move":
            if self.board.grid[gy][gx].stack:
                self.drag_src = (gx, gy)
            return

        if tool == "place":
            sel = getattr(self.winfo_toplevel(), "selected_obj", None)
            if not sel:
                return
            ok = self.board.place(gx, gy, sel.clone() if isinstance(sel, Deck) else sel)
            if ok:
                # clear selection after drop
                self.winfo_toplevel().selected_obj = None
                self._redraw_all()

    def _drag(self, ev):
        if self.mode.get() != "move" or not self.drag_src:
            return
        gx1, gy1 = ev.x // CELL, ev.y // CELL
        gx0, gy0 = self.drag_src
        if (gx1, gy1) != (gx0, gy0):
            obj = self.board.remove_top(gx0, gy0)
            if obj and self.board.place(gx1, gy1, obj):
                self.drag_src = (gx1, gy1)
                self._redraw_all()

    def _drop(self, _ev):
        self.drag_src = None

    # ---------------------------------------------------------------- #
    def _right(self, ev):
        gx, gy = ev.x // CELL, ev.y // CELL
        cell = self.board.grid[gy][gx]
        if not cell.stack:
            return
        top = cell.stack[-1]

        # deck actions
        if isinstance(top, Deck):
            menu = tk.Menu(self, tearoff=0)
            menu.add_command(label="Draw",
                             command=lambda d=top, x=gx, y=gy:
                                        self._draw_card(d, x, y))
            menu.add_separator()
            menu.add_command(label="Shuffle",
                             command=lambda d=top: (d.shuffle(),
                                                    self._redraw_all()))
            menu.add_command(label="Reset",
                             command=lambda d=top: (d.reset(),
                                                    self._redraw_all()))
            menu.add_separator()
            menu.add_command(label="Delete",
                             command=lambda x=gx, y=gy:
                                        (self.board.remove_top(x, y),
                                         self._redraw_all()))
            menu.tk_popup(ev.x_root, ev.y_root)
            return

        # otherwise just pop
        self.board.remove_top(gx, gy)
        self._redraw_all()
    
    def _draw_card(self, deck: Deck, gx: int, gy: int):
        if not deck.cards:
            messagebox.showinfo("Deck empty",
                                "This pile has no cards left.",
                                parent=self.winfo_toplevel())
            return
        card = deck.draw()
        top = self.winfo_toplevel()
        messagebox.showinfo("Drew card",
                            f"{card.name}\n\n{card.description}",
                            parent=top)
        self.winfo_toplevel().selected_obj = card      # cursor-preview & place
        if deck.cards:
            self.board.place(gx, gy, deck)
        self._redraw_all()

    # ================================================================ #
    #  Mouse-move for preview cursor                                   #
    # ================================================================ #
    def _mouse_move(self, ev):
        self.delete("cursor_preview")
        sel = getattr(self.winfo_toplevel(), "selected_obj", None)
        if sel:
            self.create_image(ev.x, ev.y,
                            image=self._preview_img(sel),
                            anchor="center",
                            tags="cursor_preview")

    def _preview(self, obj):
        key = f"prev::{getattr(obj, 'image_path', obj.name)}"
        if key in self._preview_cache:
            return self._preview_cache[key]

        if getattr(obj, "image_path", None):
            im = Image.open(self.img_dir / obj.image_path)
        else:
            # make blank silhouette for non-image items
            im = Image.new("RGBA", (CELL, CELL), "#aaaaaa88")
        w, h = im.size
        im = im.resize((int(w * PREVIEW_SCALE), int(h * PREVIEW_SCALE)),
                       Image.LANCZOS)
        self._preview_cache[key] = ImageTk.PhotoImage(im)
        return self._preview_cache[key]

    # ================================================================ #
    #  External rectangle-section helper                               #
    # ================================================================ #
    def enter_section_mode(self):
        self.mode.set("section")
        self.sec_start = None
        self.bind("<Button-1>", self._sec_start)
        self.bind("<B1-Motion>", self._sec_drag)
        self.bind("<ButtonRelease-1>", self._sec_release)

    def _sec_start(self, ev):
        self.sec_start = (ev.x // CELL, ev.y // CELL)

    def _sec_drag(self, ev):
        self._redraw_all()
        if not self.sec_start:
            return
        x0, y0 = self.sec_start
        x1, y1 = ev.x // CELL, ev.y // CELL
        self.create_rectangle(x0 * CELL, y0 * CELL,
                              (x1 + 1) * CELL, (y1 + 1) * CELL,
                              dash=(2, 2), outline="red")

    def _sec_release(self, ev):
        if not self.sec_start:
            return
        gx0, gy0 = self.sec_start
        gx1, gy1 = ev.x // CELL, ev.y // CELL
        if (gx0, gy0) == (gx1, gy1):
            self._reset_sec_binds()
            return
        pts = [(gx0, gy0), (gx1 + 1, gy0),
               (gx1 + 1, gy1 + 1), (gx0, gy1 + 1)]
        name = simpledialog.askstring("Section name", "Name:", parent=self.master) or "Area"
        kind = simpledialog.askstring("Type", "card/piece/token/deck/any:",
                                      initialvalue="Any", parent=self.master) or "Any"
        self.board.add_section(name,
                               SectionType(kind.capitalize()),
                               pts,
                               "#808080", "")
        self._reset_sec_binds()
        self._redraw_all()

    def _reset_sec_binds(self):
        self.sec_start = None
        self.unbind("<Button-1>"); self.unbind("<B1-Motion>"); self.unbind("<ButtonRelease-1>")
        self.bind("<Button-1>", self._left)
        self.bind("<B1-Motion>", self._drag)
        self.bind("<ButtonRelease-1>", self._drop)
        self.mode.set("place")

    def _preview_img(self, obj):
        key = f"prev::{getattr(obj,'image_path', obj.name)}"
        if key in self._preview_cache:
            return self._preview_cache[key]

        if getattr(obj, "image_path", None):
            im = Image.open(self.img_dir / obj.image_path)
        else:
            im = Image.new("RGBA", (CELL, CELL), "#aaaaaa88")

        scl = 0.4
        im = im.resize((int(CELL * scl), int(CELL * scl)), Image.LANCZOS)
        self._preview_cache[key] = ImageTk.PhotoImage(im)
        return self._preview_cache[key]
