from __future__ import annotations
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import pathlib
from typing import Sequence
from game.card  import Card
from game.piece import Piece

THUMB = 80  # pixel size for catalog images


class CatalogViewer(tk.Toplevel):
    """Scroll-able gallery showing every Card and Piece with thumbnails."""

    def __init__(self, master,
                 cards: Sequence[Card],
                 pieces: Sequence[Piece],
                 images_dir: pathlib.Path):
        super().__init__(master)
        self.title("Card & Piece Catalog")
        self.geometry("500x600")

        # --- Scrollable canvas scaffold -------------------------------- #
        canvas = tk.Canvas(self, highlightthickness=0)
        vsb = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        inner = ttk.Frame(canvas)
        canvas.create_window((0, 0), window=inner, anchor="nw")

        inner.bind("<Configure>",
                   lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        # --- Build grid of thumbnails ---------------------------------- #
        self._img_cache: list[ImageTk.PhotoImage] = []  # avoid GC
        row = col = 0
        for kind, obj in [("Card", c) for c in cards] + \
                        [("Piece", p) for p in pieces]:
            frame = ttk.Frame(inner, padding=4, relief="ridge")
            frame.grid(row=row, column=col, sticky="nsew", padx=4, pady=4)
            col += 1
            if col == 4:   # 4 columns per row
                col, row = 0, row + 1

            # thumbnail (or fallback rectangle)
            if obj.image_path:
                img = Image.open(images_dir / obj.image_path).resize(
                    (THUMB, THUMB), Image.LANCZOS)
                tkimg = ImageTk.PhotoImage(img)
                self._img_cache.append(tkimg)
                ttk.Label(frame, image=tkimg).pack()
            else:
                ph = tk.PhotoImage(width=THUMB, height=THUMB)
                ph.put(("lightyellow",), to=(0, 0, THUMB, THUMB))
                self._img_cache.append(ph)
                ttk.Label(frame, image=ph).pack()

            # name + type
            ttk.Label(frame, text=obj.name, font=("TkDefaultFont", 9, "bold"))\
                .pack()
            ttk.Label(frame, text=f"({kind})", foreground="gray")\
                .pack()
