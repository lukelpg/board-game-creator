from __future__ import annotations
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import pathlib
from typing import Sequence

from game.card  import Card
from game.piece import Piece
from game.token import Token


THUMB = 80   # thumbnail size


class CatalogViewer(tk.Toplevel):
    """Popup window that displays every Card, Piece, and Token."""

    def __init__(self, master,
                 cards: Sequence[Card],
                 pieces: Sequence[Piece],
                 tokens: Sequence[Token],
                 images_dir: pathlib.Path):
        super().__init__(master)
        self.title("Card / Piece / Token Catalog")
        self.geometry("500x600")

        canvas = tk.Canvas(self, highlightthickness=0)
        vsb = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        inner = ttk.Frame(canvas)
        canvas.create_window((0, 0), window=inner, anchor="nw")
        inner.bind("<Configure>",
                   lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        self._img_cache = []  # keep references

        col = row = 0
        items = [("Card", c) for c in cards] + \
                [("Piece", p) for p in pieces] + \
                [("Token", t) for t in tokens]

        for kind, obj in items:
            frame = ttk.Frame(inner, padding=4, relief="ridge")
            frame.grid(row=row, column=col, padx=4, pady=4, sticky="n")
            col += 1
            if col == 4:
                col, row = 0, row + 1

            # thumbnail or placeholder
            if obj.image_path:
                img = Image.open(images_dir / obj.image_path).resize(
                        (THUMB, THUMB), Image.LANCZOS)
                tkimg = ImageTk.PhotoImage(img)
            else:
                ph = tk.PhotoImage(width=THUMB, height=THUMB)
                ph.put(("lightyellow",), to=(0, 0, THUMB, THUMB))
                tkimg = ph
            self._img_cache.append(tkimg)
            ttk.Label(frame, image=tkimg).pack()

            ttk.Label(frame, text=obj.name, font=("TkDefaultFont", 9, "bold"))\
                .pack()
            ttk.Label(frame, text=f"({kind})", foreground="gray").pack()
