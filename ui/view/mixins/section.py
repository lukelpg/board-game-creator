"""Drag‑a‑rectangle helper for defining board areas/sections.  Subclasses only
need to provide two call‑backs:

* **_section_bounds_to_points(x0,y0,x1,y1) -> list[tuple[int,int]]** – convert
  the pixel rectangle into the *board‑unit* polygon that should be stored.
* **_add_section(name, kind, pts, outline, fill)** – persists the section in
  whatever internal model the view controls (Board, FreeBoard, …).
"""

from __future__ import annotations
import tkinter as tk
from tkinter import simpledialog, colorchooser
from typing import Callable

class SectionMixin:
    # call in subclass __init__ *after* creating self.canvas items
    def _init_section_mixin(self, cell_size: int, get_mode: Callable[[], str]) -> None:
        self._sec_cell     = cell_size            # board unit in pixels
        self._get_mode     = get_mode             # typically self.mode.get
        self._sec_start: tuple[int,int] | None = None

    # ------------------------------------------------------ public ---- #
    def enter_section_mode(self) -> None:
        """Switch bindings to rectangle‑drag mode."""
        if not hasattr(self, "_sec_cell"):
            raise RuntimeError("SectionMixin not initialised – call _init_section_mixin() in __init__()")

        self._get_mode().__setitem__(0, "section")  # type: ignore[index]
        self._sec_start = None
        self.bind("<Button-1>",        self._sec_start_ev)
        self.bind("<B1-Motion>",       self._sec_drag_ev)
        self.bind("<ButtonRelease-1>", self._sec_release_ev)

    # ------------------------------------------------------ events ---- #
    def _sec_start_ev(self, ev: tk.Event):          # type: ignore[name-defined]
        self._sec_start = (ev.x, ev.y)

    def _sec_drag_ev(self, ev: tk.Event):           # type: ignore[name-defined]
        self.delete("__section_preview")
        if not self._sec_start:
            return
        x0,y0 = self._sec_start;  x1,y1 = ev.x, ev.y
        self.create_rectangle(x0,y0,x1,y1, dash=(2,2), outline="red",
                              tags="__section_preview")

    def _sec_release_ev(self, ev: tk.Event):        # type: ignore[name-defined]
        self.delete("__section_preview")
        if not self._sec_start:
            return
        x0,y0 = self._sec_start;  x1,y1 = ev.x, ev.y
        if abs(x1-x0) < 10 or abs(y1-y0) < 10:
            self._reset_section_binds(); return

        # --- convert to board units via subclass helper -------------- #
        pts = self._section_bounds_to_points(x0,y0,x1,y1)
        if not pts:
            self._reset_section_binds(); return

        name = simpledialog.askstring("Section name", "Name:", parent=self) or "Area"
        kind = simpledialog.askstring("Type", "card/piece/token/deck/any:",
                                      initialvalue="Any", parent=self) or "Any"
        outline = colorchooser.askcolor(title="Outline")[1] or "#808080"
        fill    = colorchooser.askcolor(title="Fill (cancel = none)")[1] or ""

        self._add_section(name, kind.capitalize(), pts, outline, fill)
        self._reset_section_binds();  self.redraw()   # type: ignore[attr-defined]

    # ------------------------------------------------------ helpers --- #
    def _reset_section_binds(self):
        self._sec_start = None
        self.unbind("<Button-1>"); self.unbind("<B1-Motion>"); self.unbind("<ButtonRelease-1>")
        # subclass must re‑bind its normal handlers afterwards

    # ------------------------------------------------------ hooks ------ #
    # subclasses **must** implement the following two methods
    def _section_bounds_to_points(self, x0:int, y0:int, x1:int, y1:int):
        raise NotImplementedError
    def _add_section(self, name:str, kind:str, pts, outline:str, fill:str):
        raise NotImplementedError
