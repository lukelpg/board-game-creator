from __future__ import annotations
import tkinter as tk, json, pathlib
from tkinter import ttk
from typing import List
from game import Card, Piece, Token, Deck
from game.game_data import GameData
from .board_view import BoardView


def open_player(games_dir: pathlib.Path,
                img_dir: pathlib.Path,
                game_name: str):

    # ---- load --------------------------------------------------------- #
    j = json.loads((games_dir / f"{game_name}.json").read_text())
    gd = GameData.from_dict(j)
    board = gd.make_board()

    root = tk.Toplevel(); root.title(f"Play-test – {gd.name}")

    # ---- left lists --------------------------------------------------- #
    side = ttk.Frame(root, padding=6); side.grid(row=0,column=0, sticky="ns")
    def _lbl(t): ttk.Label(side,text=t).pack(anchor="w")
    def _lb(h): lb=tk.Listbox(side,width=20,height=h); lb.pack(); return lb
    _lbl("Cards" ); lbC=_lb(6)
    _lbl("Pieces"); lbP=_lb(6)
    _lbl("Tokens"); lbT=_lb(6)
    _lbl("Decks" ); lbD=_lb(6)
    for c in gd.cards : lbC.insert("end", c.name)
    for p in gd.pieces: lbP.insert("end", p.name)
    for t in gd.tokens: lbT.insert("end", t.name)
    for d in gd.decks : lbD.insert("end", d.name)

    # ---- board (read-write for play) --------------------------------- #
    centre = ttk.Frame(root, padding=6); centre.grid(row=0,column=1)
    view = BoardView(centre, board, img_dir, lambda *a: None)
    view.pack()

    # ---- close -------------------------------------------------------- #
    ttk.Button(side, text="Quit", command=root.destroy).pack(fill="x", pady=(10,0))

    # selection => root.selected_obj
    root.selected_obj=None
    def _sel(lb,store): idx=lb.curselection(); root.selected_obj=store[idx[0]] if idx else None
    lbC.bind("<<ListboxSelect>>", lambda e:_sel(lbC, gd.cards ))
    lbP.bind("<<ListboxSelect>>", lambda e:_sel(lbP, gd.pieces))
    lbT.bind("<<ListboxSelect>>", lambda e:_sel(lbT, gd.tokens))
    lbD.bind("<<ListboxSelect>>", lambda e:_sel(lbD, gd.decks ))

    root.columnconfigure(1,weight=1); root.rowconfigure(0,weight=1)
    root.transient(); root.grab_set(); root.wait_window()
