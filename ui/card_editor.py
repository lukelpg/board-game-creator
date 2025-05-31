from __future__ import annotations
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pathlib, shutil
from typing import Callable, Optional
from game.card import Card

class CardEditor(ttk.Frame):
    """Right-hand pane for creating/editing cards."""

    def __init__(self, master, images_dir: pathlib.Path,
                 on_save: Callable[[Card], None]):
        super().__init__(master, padding=6)
        self.images_dir = images_dir
        self.on_save = on_save
        self._build_widgets()

    # ------------------------------------------------------------------ #
    def _build_widgets(self):
        self.columnconfigure(1, weight=1)

        ttk.Label(self, text="Name").grid(row=0, column=0, sticky="w")
        self.name = ttk.Entry(self)
        self.name.grid(row=0, column=1, sticky="ew")

        ttk.Label(self, text="Description").grid(row=1, column=0, sticky="nw")
        self.desc = tk.Text(self, width=28, height=4)
        self.desc.grid(row=1, column=1, sticky="ew")

        ttk.Label(self, text="Image").grid(row=2, column=0, sticky="w")
        img_frame = ttk.Frame(self)
        img_frame.grid(row=2, column=1, sticky="ew")
        self.img_path = tk.StringVar()
        ttk.Entry(img_frame, textvariable=self.img_path).pack(side="left", fill="x", expand=True)
        ttk.Button(img_frame, text="Browse", command=self._choose_img).pack(side="right")

        stat_frame = ttk.Frame(self)
        stat_frame.grid(row=3, column=0, columnspan=2, pady=4, sticky="ew")
        ttk.Label(stat_frame, text="Attack").pack(side="left")
        self.atk = ttk.Entry(stat_frame, width=5)
        self.atk.pack(side="left", padx=(2, 10))
        ttk.Label(stat_frame, text="Defense").pack(side="left")
        self.defn = ttk.Entry(stat_frame, width=5)
        self.defn.pack(side="left", padx=2)

        ttk.Button(self, text="Save", command=self._save).grid(row=4, column=0,
                                                               columnspan=2, pady=6)

    # ------------------------------------------------------------------ #
    def _choose_img(self):
        path = filedialog.askopenfilename(title="Select image")
        if path:
            self.img_path.set(path)

    # ------------------------------------------------------------------ #
    def _save(self):
        name = self.name.get().strip()
        if not name:
            messagebox.showerror("Missing data", "Card name is required")
            return

        img_name = None
        if self.img_path.get():
            src = pathlib.Path(self.img_path.get())
            if src.exists():
                dest = self.images_dir / src.name
                shutil.copy(src, dest)
                img_name = src.name

        card = Card.new(
            name,
            self.desc.get("1.0", "end").strip(),
            img_name,
            int(self.atk.get() or 0),
            int(self.defn.get() or 0),
        )
        self.on_save(card)
        messagebox.showinfo("Saved", f"Card “{card.name}” saved")
        self._clear()

    def _clear(self):
        self.name.delete(0, "end")
        self.desc.delete("1.0", "end")
        self.img_path.set("")
        self.atk.delete(0, "end")
        self.defn.delete(0, "end")
