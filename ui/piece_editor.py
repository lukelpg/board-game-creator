from __future__ import annotations
import tkinter as tk, pathlib, shutil
from tkinter import ttk, filedialog, messagebox
from typing import Callable
from game.piece import Piece

class PieceEditor(ttk.Frame):
    """Pane for creating/editing board pieces."""
    def __init__(self, master, images_dir: pathlib.Path,
                 on_save: Callable[[Piece], None]):
        super().__init__(master, padding=6)
        self.images_dir, self.on_save = images_dir, on_save
        self._build()

    def _build(self):
        self.columnconfigure(1, weight=1)

        ttk.Label(self, text="Piece Name").grid(row=0, column=0, sticky="w")
        self.name = ttk.Entry(self); self.name.grid(row=0, column=1, sticky="ew")

        ttk.Label(self, text="Description").grid(row=1, column=0, sticky="nw")
        self.desc = tk.Text(self, width=28, height=4)
        self.desc.grid(row=1, column=1, sticky="ew")

        ttk.Label(self, text="Image").grid(row=2, column=0, sticky="w")
        imgf = ttk.Frame(self); imgf.grid(row=2, column=1, sticky="ew")
        self.img_path = tk.StringVar()
        ttk.Entry(imgf, textvariable=self.img_path).pack(side="left", fill="x", expand=True)
        ttk.Button(imgf, text="Browse", command=self._choose).pack(side="right")

        ttk.Button(self, text="Save Piece", command=self._save)\
            .grid(row=3, column=0, columnspan=2, pady=6)

    def _choose(self):
        p = filedialog.askopenfilename(title="Select image")
        if p: self.img_path.set(p)

    def _save(self):
        n = self.name.get().strip()
        if not n:
            messagebox.showerror("Missing", "Piece name required"); return
        img_name = None
        if self.img_path.get():
            src = pathlib.Path(self.img_path.get())
            if src.exists():
                dest = self.images_dir / src.name
                shutil.copy(src, dest)
                img_name = src.name
        piece = Piece.new(n, self.desc.get("1.0", "end").strip(), img_name)
        self.on_save(piece)
        messagebox.showinfo("Saved", f"Piece “{piece.name}” saved")
        self.name.delete(0, "end"); self.desc.delete("1.0", "end"); self.img_path.set("")
