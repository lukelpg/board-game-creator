from __future__ import annotations
import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
import json, pathlib
from typing import List
from game import Card, Piece, Deck, Board, Player, GameEngine
from .card_editor  import CardEditor
from .piece_editor import PieceEditor
from .board_view   import BoardView
from .catalog_view import CatalogViewer

CARD_DB  = "cards.json"
PIECE_DB = "pieces.json"

# ---------- helpers ------------------------------------------------------- #
def _load(data_dir: pathlib.Path, fname: str, factory):
    p = data_dir / fname
    return [] if not p.exists() else [factory(d) for d in json.loads(p.read_text())]

def _save(data_dir: pathlib.Path, fname: str, items):
    (data_dir / fname).write_text(json.dumps([i.to_dict() for i in items], indent=2))


# -------------------------------------------------------------------------- #
def run_app(data: pathlib.Path, imgs: pathlib.Path):
    root = tk.Tk(); root.title("Flexible Board-Game Studio")

    # ---------- state ----------------------------------------------------- #
    cards : List[Card]  = _load(data, CARD_DB , Card.from_dict)
    pieces: List[Piece] = _load(data, PIECE_DB, Piece.from_dict)
    deck  = Deck("Main", cards.copy())
    board = Board()           # default 8×8
    players = [Player("Player 1"), Player("Player 2")]
    engine  = GameEngine(players, deck, board)

    # ---------- left sidebar (lists) ------------------------------------- #
    sidebar = ttk.Frame(root, padding=6); sidebar.grid(row=0, column=0, sticky="ns")

    ttk.Label(sidebar, text="Cards").pack(anchor="w")
    card_lb = tk.Listbox(sidebar, height=8, width=22); card_lb.pack()

    ttk.Label(sidebar, text="Pieces").pack(anchor="w", pady=(6,0))
    piece_lb = tk.Listbox(sidebar, height=8, width=22); piece_lb.pack()

    def _refresh():
        card_lb.delete(0,"end"); [card_lb.insert("end", c.name) for c in cards]
        piece_lb.delete(0,"end");[piece_lb.insert("end", p.name) for p in pieces]
    _refresh()

    ttk.Button(sidebar, text="Open Catalog",
            command=lambda: CatalogViewer(root, cards, pieces, imgs))\
            .pack(pady=(2,4), fill="x")

    # ---------- board centre --------------------------------------------- #
    centre = ttk.Frame(root, padding=6); centre.grid(row=0,column=1)
    bv = BoardView(centre, board, imgs, lambda *a: None); bv.pack()

    # ---------- right notebook (editors) --------------------------------- #
    nb = ttk.Notebook(root); nb.grid(row=0,column=2, sticky="n")

    ce  = CardEditor (nb, imgs, lambda c:(cards.append(c), _save(data,CARD_DB,cards), _refresh()))
    pe  = PieceEditor(nb, imgs, lambda p:(pieces.append(p),_save(data,PIECE_DB,pieces),_refresh()))
    nb.add(ce, text="Card Editor"); nb.add(pe, text="Piece Editor")

    # ---------- board settings ------------------------------------------- #
    def resize_board():
        w = simpledialog.askinteger("Board Width" , "New width (columns):", minvalue=1, initialvalue=board.WIDTH)
        h = simpledialog.askinteger("Board Height", "New height (rows):"  , minvalue=1, initialvalue=board.HEIGHT)
        if w and h:
            board.resize(w, h)
            bv.refresh_board()

    ttk.Button(sidebar, text="Resize Board", command=resize_board)\
        .pack(pady=(10,2), fill="x")

    # ---------- global selected object (card *or* piece) ----------------- #
    root.selected_obj = None
    def _sel(evt, seq:list, store):
        idx = seq.curselection()
        root.selected_obj = store[idx[0]] if idx else None
    card_lb.bind ("<<ListboxSelect>>", lambda e:_sel(e, card_lb , cards ))
    piece_lb.bind("<<ListboxSelect>>", lambda e:_sel(e, piece_lb, pieces))

    # grid weights
    root.columnconfigure(1, weight=1); root.rowconfigure(0, weight=1)
    root.mainloop()
