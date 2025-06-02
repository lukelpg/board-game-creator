# ui/board_view.py
from __future__ import annotations

import itertools
import pathlib
from typing import Dict, List

import tkinter as tk
from tkinter import simpledialog, colorchooser, messagebox
from PIL import Image, ImageTk

from game.board import Board, SectionType
from game.card import Card
from game.deck import Deck
from game.piece import Piece
from game.token import Token

# -------------------------------------------------------------------- #
CELL   = 64        # square size in pixels
OFFSET = 8         # diagonal offset between stacked objects
RADIUS = 10        # rounded-corner radius for card silhouette

# -------------------------------------------------------------------- #
class BoardView(tk.Canvas):
    """
    Editing & play canvas.

    Controls
    --------
    Placement / stacks
        Left-click         place selected object (or paint-anywhere)
        Right-click        pop top of stack / draw card from deck
        Ctrl+Right-click   shuffle top deck
        Alt +Right-click   reset top deck
        Space              toggle paint-anywhere (ignores section rules)

    Sections
        S                  begin polygon section mode
        (while drawing)    Left-click to add vertices
        Enter              finish polygon, choose props
        Esc                cancel polygon
        Shift+Right-click  edit / delete an existing section

    Public helper
        enter_section_mode()  – called by sidebar “Section (drag)” button
                                to draw a quick rectangle (drag & type)
    """

    # ---------------------------------------------------------------- #
    def __init__(self, master, board: Board, img_dir: pathlib.Path):
        super().__init__(master,
                         width=board.WIDTH * CELL,
                         height=board.HEIGHT * CELL,
                         background="white",
                         highlightthickness=0)

        self.board   = board
        self.img_dir = img_dir
        self._cache: Dict[str, ImageTk.PhotoImage] = {}

        # mode/state flags
        self.mode            = "place"   # place | paint | poly | section
        self.paint_anywhere  = False
        self.sec_start: tuple[int, int] | None = None
        self.poly_pts: List[tuple[int, int]] = []

        # event bindings
        self.bind("<Button-1>",        self._left)
        self.bind("<ButtonRelease-1>", self._release)
        self.bind("<B1-Motion>",       self._drag)
        self.bind("<Button-3>",        self._right)

        master.bind_all("<space>",     self._toggle_paint)
        master.bind_all("s",           self._start_poly)
        master.bind_all("<Return>",    self._finish_poly)
        master.bind_all("<Escape>",    self._cancel_poly)

        self._redraw_all()

    # ================================================================ #
    #  High-level redraw                                               #
    # ================================================================ #
    def _redraw_all(self):
        self.delete("all")
        self._draw_grid()
        self._draw_sections()
        for row in self.board.grid:
            for cell in row:
                self._draw_stack(cell.x, cell.y, cell.stack)

    def _draw_grid(self):
        for x in range(self.board.WIDTH + 1):
            self.create_line(x * CELL, 0,
                             x * CELL, self.board.HEIGHT * CELL)
        for y in range(self.board.HEIGHT + 1):
            self.create_line(0, y * CELL,
                             self.board.WIDTH * CELL, y * CELL)

    def _draw_sections(self):
        for sec in self.board.sections:
            # polygon (new format)
            if hasattr(sec, "points"):
                pix = [(gx * CELL, gy * CELL) for gx, gy in sec.points]
                self.create_polygon(
                    *itertools.chain.from_iterable(pix),
                    outline=getattr(sec, "outline", "#808080"),
                    fill=getattr(sec, "fill", ""),
                    stipple="gray25" if getattr(sec, "fill", "") else "",
                    width=2, tags="sec")
            # legacy rectangle (if any remain)
            elif all(hasattr(sec, a) for a in ("x0", "y0", "x1", "y1")):
                self.create_rectangle(sec.x0 * CELL, sec.y0 * CELL,
                                      (sec.x1 + 1) * CELL, (sec.y1 + 1) * CELL,
                                      outline=getattr(sec, "outline", "#808080"),
                                      fill=getattr(sec, "fill", ""),
                                      dash=(4, 2), width=2, tags="sec")

    # ================================================================ #
    #  Stack & object rendering                                        #
    # ================================================================ #
    def _draw_stack(self, gx, gy, stack):
        for i, obj in enumerate(stack):
            self._draw_obj(gx * CELL + i * OFFSET,
                           gy * CELL + i * OFFSET, obj)

    def _draw_obj(self, x0: int, y0: int, obj):
        # --- deck pile ------------------------------------------------
        if isinstance(obj, Deck):
            self.create_rectangle(x0 + 8, y0 + 8, x0 + CELL - 8, y0 + CELL - 8,
                                  fill="plum", outline="black")
            self.create_text(x0 + CELL / 2, y0 + CELL / 2,
                             text=(obj.name or "Deck")[:8], fill="white")
            return
        # --- prefer image --------------------------------------------
        if getattr(obj, "image_path", None):
            self.create_image(x0, y0, image=self._img(obj.image_path),
                              anchor="nw")
        # --- polygon token/piece -------------------------------------
        elif getattr(obj, "points", None):
            pts = [(x0 + px, y0 + py) for px, py in obj.points]
            self.create_polygon(
                *itertools.chain.from_iterable(pts),
                fill="khaki", outline="black")
        # --- card silhouette -----------------------------------------
        elif isinstance(obj, Card):
            self._rounded(x0, y0)
        # --- default token circle ------------------------------------
        elif isinstance(obj, Token):
            self.create_oval(x0 + 6, y0 + 6, x0 + CELL - 6, y0 + CELL - 6,
                             fill="khaki", outline="black")
        # --- fallback rectangle --------------------------------------
        else:
            self.create_rectangle(x0, y0, x0 + CELL, y0 + CELL,
                                  fill="lightyellow")
        # text label
        self.create_text(x0 + CELL / 2, y0 + CELL / 2,
                         text=obj.name[:6])

    # --------------------------------------------------------------- #
    def _rounded(self, x: int, y: int):
        r = RADIUS
        pts = [x + r, y, x + CELL - r, y, x + CELL, y,
               x + CELL, y + r, x + CELL, y + CELL - r, x + CELL, y + CELL,
               x + CELL - r, y + CELL, x + r, y + CELL,
               x, y + CELL, x, y + CELL - r, x, y + r, x, y]
        self.create_polygon(pts, smooth=True,
                            fill="white", outline="black")

    def _img(self, name: str):
        if name not in self._cache:
            im = Image.open(self.img_dir / name).resize(
                (CELL, CELL),
                Image.LANCZOS)
            self._cache[name] = ImageTk.PhotoImage(im)
        return self._cache[name]

    # ================================================================ #
    #  Mouse & key interaction                                         #
    # ================================================================ #
    def _toggle_paint(self, _evt):
        self.paint_anywhere = not self.paint_anywhere
        self.master.title(
            "PAINT-ANYWHERE ON"
            if self.paint_anywhere else "")

    # --------------- placement / drawing ---------------------------- #
    def _left(self, ev):
        gx, gy = ev.x // CELL, ev.y // CELL

        # polygon vertex capture
        if self.mode == "poly":
            self.poly_pts.append((gx, gy))
            if len(self.poly_pts) >= 2:
                self.create_line(self.poly_pts[-2][0] * CELL,
                                 self.poly_pts[-2][1] * CELL,
                                 self.poly_pts[-1][0] * CELL,
                                 self.poly_pts[-1][1] * CELL,
                                 fill="red")
            return

        # rectangle quick-section mode
        if self.mode == "section":
            self.sec_start = (gx, gy)
            return

        sel = getattr(self.winfo_toplevel(), "selected_obj", None)
        if not sel:
            return

        # clone deck pile so original stays selectable
        place_obj = sel.clone() if isinstance(sel, Deck) else sel

        allowed = self.paint_anywhere or self.board.can_accept(gx, gy, place_obj)
        if allowed and self.board.place(gx, gy, place_obj):
            self._redraw_all()

    # ---------------------------------------------------------------- #
    def _drag(self, ev):
        if self.mode == "section" and self.sec_start:
            self._redraw_all()
            x0, y0 = self.sec_start
            x1, y1 = ev.x // CELL, ev.y // CELL
            self.create_rectangle(x0 * CELL, y0 * CELL,
                                  (x1 + 1) * CELL, (y1 + 1) * CELL,
                                  dash=(2, 2), outline="red")

    # ---------------------------------------------------------------- #
    def _release(self, ev):
        # finish quick rectangle section
        if self.mode == "section" and self.sec_start:
            x0, y0 = self.sec_start
            x1, y1 = ev.x // CELL, ev.y // CELL
            x0, x1 = sorted((x0, x1))
            y0, y1 = sorted((y0, y1))

            pts = [(x0, y0), (x1 + 1, y0),
                   (x1 + 1, y1 + 1), (x0, y1 + 1)]
            name = simpledialog.askstring("Section name", "Name:",
                                          parent=self.master) or "Area"
            kind = simpledialog.askstring("Type",
                                          "card/piece/token/deck/any:",
                                          initialvalue="Any",
                                          parent=self.master) or "Any"
            outline = colorchooser.askcolor(title="Outline")[1] or "#808080"
            fill = colorchooser.askcolor(title="Fill (cancel = none)")[1] or ""
            self.board.add_section(name,
                                   SectionType(kind.capitalize()),
                                   pts, outline, fill)

            self.sec_start = None
            self.mode = "place"
            self._redraw_all()
            return

    # ---------------------------------------------------------------- #
    def _right(self, ev):
        gx, gy = ev.x // CELL, ev.y // CELL

        # section edit menu (Shift)
        if ev.state & 0x0001:
            sec = self._find_section(gx, gy)
            if not sec:
                return
            choice = simpledialog.askstring(
                "Section",
                "delete / card / piece / token / deck / any",
                initialvalue=sec.kind.value,
                parent=self.master)
            if not choice:
                return
            choice = choice.capitalize()
            if choice == "Delete":
                self.board.sections.remove(sec)
            elif choice in ("Card", "Piece", "Token", "Deck", "Any"):
                sec.kind = SectionType(choice)
            sec.outline = colorchooser.askcolor(
                title="Outline", initialcolor=sec.outline)[1] or sec.outline
            fill_col = colorchooser.askcolor(
                title="Fill (cancel keeps current)",
                initialcolor=sec.fill or "#ffffff")[1]
            if fill_col is not None:
                sec.fill = fill_col
            self._redraw_all()
            return

        # cell empty?
        cell = self.board.grid[gy][gx]
        if not cell.stack:
            return
        top = cell.stack[-1]

        # deck special actions
        if isinstance(top, Deck):
            if ev.state & 0x0004:          # Ctrl shuffle
                top.shuffle(); self._redraw_all(); return
            if ev.state & 0x0008:          # Alt reset
                top.reset(); self._redraw_all(); return

        # normal pop / draw
        popped = self.board.remove_top(gx, gy)
        if isinstance(popped, Deck):
            if popped.cards:
                card = popped.draw()
                messagebox.showinfo("Drew",
                                    f"{card.name}\n\n{card.description}",
                                    parent=self.master)
                if popped.cards:
                    self.board.place(gx, gy, popped)
        self._redraw_all()

    # ================================================================ #
    #  Polygon-drawing helpers                                         #
    # ================================================================ #
    def _start_poly(self, _evt):
        self.mode = "poly"
        self.poly_pts.clear()
        self.winfo_toplevel().title("Polygon mode: click vertices, Enter=finish, Esc=cancel")

    def _finish_poly(self, _evt):
        if self.mode != "poly" or len(self.poly_pts) < 3:
            return
        name = simpledialog.askstring("Section name", "Name:",
                                      parent=self.master) or "Area"
        kind = simpledialog.askstring("Type",
                                      "card/piece/token/deck/any:",
                                      initialvalue="Any",
                                      parent=self.master) or "Any"
        outline = colorchooser.askcolor(title="Outline")[1] or "#808080"
        fill = colorchooser.askcolor(
            title="Fill (cancel = none)")[1] or ""
        self.board.add_section(name,
                               SectionType(kind.capitalize()),
                               self.poly_pts[:],
                               outline, fill)
        self.mode = "place"
        self.poly_pts.clear()
        self._redraw_all()
        self.master.title("")

    def _cancel_poly(self, _evt):
        if self.mode == "poly":
            self.mode = "place"
            self.poly_pts.clear()
            self._redraw_all()
            self.master.title("")

    # ================================================================ #
    #  Utilities                                                       #
    # ================================================================ #
    def _find_section(self, gx: int, gy: int):
        for s in self.board.sections:
            if hasattr(s, "points"):
                if self.board._pnpoly(s.points, gx + .5, gy + .5):
                    return s
            elif all(hasattr(s, a) for a in ("x0", "y0", "x1", "y1")):
                if s.x0 <= gx <= s.x1 and s.y0 <= gy <= s.y1:
                    return s

    # called by sidebar when user wants quick rectangle
    def enter_section_mode(self):
        self.mode = "section"
