"""BaseCanvasView – provides zoom, tool palette (place/move/erase) and basic
mouse binding stubs so every concrete board view inherits the same behaviour."""

from __future__ import annotations
import tkinter as tk
from tkinter import ttk
from typing import Callable

from .mixins import ZoomMixin

class BaseCanvasView(ZoomMixin, tk.Canvas):
    """Tk Canvas with a built‑in tool palette and zoom support."""

    def __init__(self, master: tk.Widget,
                 width:int, height:int,
                 palette:bool = True,
                 on_redraw: Callable[[], None] | None = None):
        super().__init__(master, width=width, height=height,
                         background="white", highlightthickness=0)

        self._on_redraw = on_redraw or (lambda: None)
        self.mode       = tk.StringVar(value="place")  # place / move / erase / section
        self._bind_zoom()
        self._bind_mouse()
        if palette:
            self._build_palette(master)
        self.redraw()

    # ------------------------------- palette ----------------------- #
    def _build_palette(self, master: tk.Widget):
        bar = ttk.Frame(master); bar.pack(side="bottom", fill="x")
        for label in ("place", "move", "erase"):
            ttk.Radiobutton(bar, text=label.capitalize(), value=label,
                            variable=self.mode).pack(side="left")
        ttk.Label(bar, text=" ⎵ cycles  •  Ctrl+Wheel zoom").pack(side="right")
        self.bind_all("<space>", lambda _e: self._cycle_tool())

    def _cycle_tool(self):
        order = ("place", "move", "erase")
        cur   = order.index(self.mode.get())
        self.mode.set(order[(cur + 1) % len(order)])

    # ------------------------------- mouse stubs ------------------- #
    def _bind_mouse(self):
        self.bind("<Button-1>",        self._on_left)
        self.bind("<B1-Motion>",       self._on_drag)
        self.bind("<ButtonRelease-1>", self._on_drop)
        self.bind("<Button-3>",        self._on_right)
        self.bind("<Motion>",          self._on_move)

    # subclasses override any they need
    def _on_left (self, ev): ...
    def _on_drag (self, ev): ...
    def _on_drop (self, ev): ...
    def _on_right(self, ev): ...
    def _on_move (self, ev): ...

    # ------------------------------- redraw ------------------------ #
    def redraw(self):
        self.delete("all")
        self._on_redraw()

    # ZoomMixin will call this when scale changes – default resizes scroll‑region
    def _zoom_changed(self, scale: float):
        self.configure(scrollregion=self.bbox("all"))