# ui/tile_editor.py
from __future__ import annotations
import tkinter as tk
from tkinter import ttk, simpledialog, colorchooser, filedialog
from PIL import Image, ImageTk
from game.tile import Tile, ShapePts, CELL
import pathlib
import math

def hex_points(cell_size: int):
    """Return 6 points for a flat-topped regular hexagon."""
    cx = cy = cell_size // 2
    r  = cell_size * 0.5
    return [
        (cx + r * math.cos(math.radians(a)),
         cy + r * math.sin(math.radians(a)))
        for a in (0, 60, 120, 180, 240, 300)
    ]

class TileEditor(ttk.Frame):
    """Simple form to make / edit one Tile template."""

    def __init__(self, master, img_dir, on_add):
        super().__init__(master, padding=8)
        self.img_dir = img_dir
        self.on_add = on_add
        self.img_preview = None     # PhotoImage

        ttk.Label(self, text="Name").grid(row=0, column=0, sticky="w")
        self.e_name = ttk.Entry(self, width=16)
        self.e_name.grid(row=0, column=1, pady=2)

        ttk.Label(self, text="Shape").grid(row=1, column=0, sticky="w")
        self.shape = tk.StringVar(value="rect")
        ttk.Combobox(self, textvariable=self.shape,
                     values=("rect", "hex", "poly"), width=13)\
            .grid(row=1, column=1, pady=2)

        ttk.Label(self, text="Outline").grid(row=2, column=0, sticky="w")
        self.out_col = tk.StringVar(value="#808080")
        ttk.Button(self, textvariable=self.out_col,
                   command=lambda:self._pick(self.out_col)).grid(row=2,column=1)

        ttk.Label(self, text="Fill").grid(row=3, column=0, sticky="w")
        self.fill_col = tk.StringVar(value="#cccccc")
        ttk.Button(self, textvariable=self.fill_col,
                   command=lambda:self._pick(self.fill_col)).grid(row=3,column=1)

        ttk.Button(self, text="Image...", command=self._choose_img)\
            .grid(row=4, column=0, columnspan=2, pady=6)

        ttk.Button(self, text="Add Tile", command=self._make)\
            .grid(row=5, column=0, columnspan=2, pady=4)

    def _pick(self, var):
        col = colorchooser.askcolor(initialcolor=var.get())[1]
        if col: var.set(col)

    def _choose_img(self):
        fn = filedialog.askopenfilename(title="Choose tile image",
                                        filetypes=[("PNG","*.png"),("JPEG","*.jpg;*.jpeg")])
        if fn: self.img_path = pathlib.Path(fn).name

    def _make(self):
        name = self.e_name.get() or "Tile"
        shape = self.shape.get()
        pts: ShapePts
        if shape == "rect":
            pts = [(0,0),(CELL,0),(CELL,CELL),(0,CELL)]
        elif shape == "hex":
            pts = hex_points(CELL)
        else:
            # simple triangle example for custom; refine later
            pts = [(CELL//2,0),(CELL, CELL),(0,CELL)]
        t = Tile(name, shape, pts, self.out_col.get(), self.fill_col.get(),
                 getattr(self,'img_path',None))
        self.on_add(t)
        self._reset()

    def _reset(self):
        for e in (self.e_name,): e.delete(0,"end")
        self.shape.set("rect")
        self.out_col.set("#808080")
        self.fill_col.set("#cccccc")
        self.img_path = None
