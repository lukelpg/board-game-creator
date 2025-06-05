from __future__ import annotations

import json, pathlib, tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Dict

from game import Card, Piece, Token, Deck
from game.tile         import Tile  
from game.game_data   import BoardSpec
from game.free_board  import FreeBoard
from ui.board_view     import BoardView
from ui.free_board_view import FreeBoardView


# --------------------------------------------------------------------- #
def open_player(games_dir: pathlib.Path,
                img_dir: pathlib.Path,
                game_name: str):
    """Opens the play-test window for the chosen game."""

    # ---------- load file -------------------------------------------- #
    raw = json.loads((games_dir / f"{game_name}.json").read_text())

    # convenience look-ups for rebuilding objects by name
    cards  = {c["name"]: Card.from_dict(c)   for c in raw.get("cards",  [])}
    pieces = {p["name"]: Piece.from_dict(p)  for p in raw.get("pieces", [])}
    tokens = {t["name"]: Token.from_dict(t)  for t in raw.get("tokens", [])}
    decks  = {d["name"]: Deck.from_dict(d, cards) for d in raw.get("decks", [])}
    tiles = {t["name"]: Tile.from_dict(t) for t in raw.get("tiles", [])}

    # ---------- window shell ----------------------------------------- #
    root = tk.Toplevel()
    root.title(f"Play-test — {raw['name']}")

    # ---------- side bar (object selectors) -------------------------- #
    side = ttk.Frame(root, padding=6)
    side.grid(row=0, column=0, sticky="ns")

    def _lbl(text):
        ttk.Label(side, text=text).pack(anchor="w")
    def _lb(h):
        lb = tk.Listbox(side, width=20, height=h)
        lb.pack()
        return lb

    _lbl("Cards");   lbC = _lb(6)
    _lbl("Pieces");  lbP = _lb(6)
    _lbl("Tokens");  lbT = _lb(6)
    _lbl("Decks");   lbD = _lb(6)
    _lbl("Tiles"); lbTi = _lb(6)

    for name in cards:  lbC.insert("end", name)
    for name in pieces: lbP.insert("end", name)
    for name in tokens: lbT.insert("end", name)
    for name in decks:  lbD.insert("end", name)
    for n in tiles: lbTi.insert("end", n)

    # ---------- board notebook --------------------------------------- #
    centre = ttk.Frame(root, padding=6)
    centre.grid(row=0, column=1, sticky="nsew")
    nb_board = ttk.Notebook(centre)
    nb_board.pack(fill="both", expand=True)

    # helper to rebuild placed objects in free boards
    def _obj_from_rec(rec: Dict) -> Card | Piece | Token | Deck | None:
        typ = rec["type"]
        name = rec["name"]
        return (cards.get(name)  if typ == "Card"  else
                pieces.get(name) if typ == "Piece" else
                tokens.get(name) if typ == "Token" else
                decks.get(name)  if typ == "Deck"  else
                None)

    # ---------- create a tab per board ------------------------------- #
    for b in raw.get("boards", []):
        tab = ttk.Frame(nb_board)

        # ----- FREE canvas board ------------------------------------ #
        if b.get("mode") == "free":
            fb = FreeBoard(b["width"], b["height"], [], b["sections"])
            # restore placed objects (if saved)
            for rec in b.get("placed", []):
                obj = _obj_from_rec(rec)
                if obj:
                    fb.add(obj, rec["x"], rec["y"])
            view = FreeBoardView(tab, fb, img_dir)

        elif b.get("mode") == "tilegrid":
            from ui.tile_grid_view import TileGridView
            tg = TileGridView(tab, list(tiles.values()), b["cols"], b["rows"], img_dir)
            # restore placed:
            for rec in b.get("placed", []):
                tile = tiles.get(rec["name"])
                if tile:
                    tg.place_tile(tile.clone(), rec["col"], rec["row"])
            tg.pack()
            nb_board.add(tab, text=b.get("name", "Tiles"))

        # ----- GRID board ------------------------------------------- #
        else:
            spec = BoardSpec.from_dict(b)
            view = BoardView(tab, spec.build(), img_dir)

        view.pack()
        nb_board.add(tab, text=b.get("name", "Board"))

    # ---------- selection ↔ root.selected_obj ------------------------ #
    root.selected_obj = None

    def _sel(lb, store):
        idx = lb.curselection()
        root.selected_obj = store[lb.get(idx[0])] if idx else None

    lbC.bind("<<ListboxSelect>>", lambda e: _sel(lbC, cards))
    lbP.bind("<<ListboxSelect>>", lambda e: _sel(lbP, pieces))
    lbT.bind("<<ListboxSelect>>", lambda e: _sel(lbT, tokens))
    lbD.bind("<<ListboxSelect>>", lambda e: _sel(lbD, decks))
    lbTi.bind("<<ListboxSelect>>", lambda e:_sel(lbTi, tiles))

    # ---------- quit ------------------------------------------------- #
    ttk.Button(side, text="Quit", command=root.destroy).pack(fill="x", pady=10)

    # layout stretch
    root.columnconfigure(1, weight=1)
    root.rowconfigure   (0, weight=1)

    root.transient(); root.grab_set(); root.wait_window()
