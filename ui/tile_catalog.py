# ui/tile_catalog.py
from __future__ import annotations
import tkinter as tk
from tkinter import ttk, colorchooser, simpledialog, messagebox
from game.tile import Tile


class TileCatalog(tk.Toplevel):
    """
    Lets the user rename, recolour, or delete any Tile template.
    """

    def __init__(self, master, tiles: list[Tile], refresh_cb):
        super().__init__(master)
        self.title("Tile Catalog")
        self.geometry("300x380")
        self.tiles = tiles
        self.refresh_cb = refresh_cb

        self.lb = tk.Listbox(self)
        self.lb.pack(fill="both", expand=True, padx=8, pady=6)
        self._fill()

        btn = ttk.Frame(self); btn.pack(fill="x", pady=6)
        ttk.Button(btn, text="Edit",   command=self._edit).pack(side="left", expand=True, fill="x")
        ttk.Button(btn, text="Delete", command=self._delete).pack(side="left", expand=True, fill="x")

    # ---------------------------------------------------------------- #
    def _fill(self):
        self.lb.delete(0, "end")
        for t in self.tiles:
            self.lb.insert("end", f"{t.name}  ({t.shape})")

    def _sel(self) -> Tile | None:
        idx = self.lb.curselection()
        return self.tiles[idx[0]] if idx else None

    # ---------------------------------------------------------------- #
    def _edit(self):
        t = self._sel()
        if not t:
            return

        name = simpledialog.askstring("Name", "Tile name:", initialvalue=t.name, parent=self)
        if name:
            t.name = name

        shape = simpledialog.askstring("Shape", "rect / hex / poly:", initialvalue=t.shape, parent=self)
        if shape and shape in ("rect", "hex", "poly"):
            t.shape = shape

        t.outline = colorchooser.askcolor(title="Outline", initialcolor=t.outline)[1] or t.outline
        fill      = colorchooser.askcolor(title="Fill (cancel = none)", initialcolor=t.fill or "#ffffff")[1]
        if fill is not None:
            t.fill = fill

        self._fill()
        self.refresh_cb()

    # ---------------------------------------------------------------- #
    def _delete(self):
        t = self._sel()
        if not t:
            return
        if messagebox.askyesno("Delete", f"Delete tile '{t.name}'?", parent=self):
            self.tiles.remove(t)
            self._fill()
            self.refresh_cb()
