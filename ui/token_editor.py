from __future__ import annotations
import tkinter as tk, pathlib, shutil
from tkinter import ttk, filedialog, messagebox
from typing import Callable

from game.token import Token
from ui.shape_canvas import ShapeCanvas


class TokenEditor(ttk.Frame):
    """Editor for Tokens – lets user draw a custom polygon."""

    def __init__(self, master, images_dir: pathlib.Path,
                 on_save: Callable[[Token], None]):
        super().__init__(master, padding=6)
        self.images_dir, self.on_save = images_dir, on_save
        self._build()

    # ---------------- UI ------------------------------------------------ #
    def _build(self):
        self.columnconfigure(1, weight=1)

        ttk.Label(self, text="Token Name").grid(row=0, column=0, sticky="w")
        self.name = ttk.Entry(self); self.name.grid(row=0, column=1, sticky="ew")

        ttk.Label(self, text="Description").grid(row=1, column=0, sticky="nw")
        self.desc = tk.Text(self, width=28, height=3)
        self.desc.grid(row=1, column=1, sticky="ew")

        # Optional image
        ttk.Label(self, text="Image").grid(row=2, column=0, sticky="w")
        imgf = ttk.Frame(self); imgf.grid(row=2, column=1, sticky="ew")
        self.img_path = tk.StringVar()
        ttk.Entry(imgf, textvariable=self.img_path).pack(side="left", fill="x", expand=True)
        ttk.Button(imgf, text="Browse", command=self._browse).pack(side="right")

        # Shape drawing canvas
        ttk.Label(self, text="Or Draw Shape").grid(row=3, column=0, sticky="nw", pady=(6,0))
        self.canvas = ShapeCanvas(self)
        self.canvas.grid(row=3, column=1, sticky="w", pady=(6,0))

        # save
        ttk.Button(self, text="Save Token", command=self._save)\
            .grid(row=4, column=0, columnspan=2, pady=6)

    # ---------------- callbacks ---------------------------------------- #
    def _browse(self):
        p = filedialog.askopenfilename(title="Select image")
        if p: self.img_path.set(p)

    def _save(self):
        n = self.name.get().strip()
        if not n:
            messagebox.showerror("Missing", "Token name required"); return

        img_name = None
        if self.img_path.get():
            src = pathlib.Path(self.img_path.get())
            if src.exists():
                dest = self.images_dir / src.name
                shutil.copy(src, dest)
                img_name = src.name

        token = Token.new(
            n,
            self.desc.get("1.0", "end").strip(),
            img_name,
            self.canvas.points[:] if self.canvas.points else None
        )
        self.on_save(token)
        messagebox.showinfo("Saved", f"Token “{token.name}” saved")

        # reset
        self.name.delete(0, "end")
        self.desc.delete("1.0", "end")
        self.img_path.set("")
        self.canvas.points.clear(); self.canvas._redraw()
