from __future__ import annotations
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import json, pathlib
from typing import List

from game import Card, Piece, Token, Deck, Board, Player, GameEngine
from game.board import SectionType
from game.shape import Point

from .card_editor   import CardEditor
from .piece_editor  import PieceEditor    # assume updated similarly to TokenEditor
from .token_editor  import TokenEditor
from .board_view    import BoardView
from .catalog_view  import CatalogViewer

CARD_DB  = "cards.json"
PIECE_DB = "pieces.json"
TOKEN_DB = "tokens.json"
DECK_DB  = "decks.json"


def _load(data_dir, fname, factory):
    p = data_dir / fname
    return [] if not p.exists() else [factory(d) for d in json.loads(p.read_text())]


def _save(data_dir, fname, items):
    (data_dir / fname).write_text(json.dumps([i.to_dict() for i in items], indent=2))


# ---------------------------------------------------------------------- #
def run_app(data_dir: pathlib.Path, img_dir: pathlib.Path):
    root = tk.Tk(); root.title("Board-Game Studio v2")

    # -------- state ---------------------------------------------------- #
    cards  : List[Card]  = _load(data_dir, CARD_DB , Card.from_dict)
    pieces : List[Piece] = _load(data_dir, PIECE_DB, Piece.from_dict)
    tokens : List[Token] = _load(data_dir, TOKEN_DB, Token.from_dict)
    decks  : List[Deck]  = _load(data_dir, DECK_DB , Deck.from_dict)

    board  = Board()
    players = [Player("Player 1"), Player("Player 2")]
    engine  = GameEngine(players, Deck("Scratch"), board)  # gameplay deck not used here

    # -------- sidebar -------------------------------------------------- #
    side = ttk.Frame(root, padding=6); side.grid(row=0, column=0, sticky="ns")

    def _lb(label): ttk.Label(side, text=label).pack(anchor="w")
    def _mk_list(h):
        lb = tk.Listbox(side, height=h, width=22); lb.pack()
        return lb

    _lb("Cards");   lb_cards  = _mk_list(5)
    _lb("Pieces");  lb_pieces = _mk_list(5)
    _lb("Tokens");  lb_tokens = _mk_list(5)
    _lb("Decks");   lb_decks  = _mk_list(5)

    def _refresh():
        lb_cards .delete(0,"end"); [lb_cards .insert("end", c.name) for c in cards]
        lb_pieces.delete(0,"end"); [lb_pieces.insert("end", p.name) for p in pieces]
        lb_tokens.delete(0,"end"); [lb_tokens.insert("end", t.name) for t in tokens]
        lb_decks .delete(0,"end"); [lb_decks .insert("end", d.name) for d in decks]
    _refresh()

    ttk.Button(side, text="New Deck", command=lambda:_new_deck(root, decks, cards, data_dir, _refresh))\
        .pack(fill="x", pady=(2,6))

    # -------- board ---------------------------------------------------- #
    centre = ttk.Frame(root, padding=6); centre.grid(row=0, column=1)
    view = BoardView(centre, board, img_dir, lambda *a: None)
    view.pack()

    # -------- editors notebook ---------------------------------------- #
    nb = ttk.Notebook(root); nb.grid(row=0, column=2, sticky="n")
    nb.add(CardEditor (nb, img_dir, lambda c:(cards.append(c), _save(data_dir,CARD_DB,cards), _refresh())),
           text="Card")
    nb.add(PieceEditor(nb, img_dir, lambda p:(pieces.append(p),_save(data_dir,PIECE_DB,pieces),_refresh())),
           text="Piece")
    nb.add(TokenEditor(nb, img_dir, lambda t:(tokens.append(t),_save(data_dir,TOKEN_DB,tokens),_refresh())),
           text="Token")

    # -------- catalog / section / resize buttons ---------------------- #
    ttk.Button(side, text="Catalog",
               command=lambda: CatalogViewer(root, cards, pieces, tokens, img_dir))\
        .pack(fill="x")
    ttk.Button(side, text="Add Section (by drag)",
               command=view.enter_section_mode)\
        .pack(fill="x", pady=(6,0))
    ttk.Button(side, text="Resize Board",
               command=lambda:_resize_board(board, view))\
        .pack(fill="x")

    # -------- selected object (Card / Piece / Token / Deck) ----------- #
    root.selected_obj = None
    def sel(lb, store):
        idx = lb.curselection()
        root.selected_obj = store[idx[0]] if idx else None
    lb_cards .bind("<<ListboxSelect>>", lambda e: sel(lb_cards , cards ))
    lb_pieces.bind("<<ListboxSelect>>", lambda e: sel(lb_pieces, pieces))
    lb_tokens.bind("<<ListboxSelect>>", lambda e: sel(lb_tokens, tokens))
    lb_decks .bind("<<ListboxSelect>>", lambda e: sel(lb_decks , decks ))

    root.columnconfigure(1, weight=1); root.rowconfigure(0, weight=1)
    root.mainloop()


# -------------- helpers ------------------------------------------------- #
def _resize_board(board: Board, view: BoardView):
    w = simpledialog.askinteger("Resize", "Columns :", minvalue=1, initialvalue=board.WIDTH)
    h = simpledialog.askinteger("Resize", "Rows :",    minvalue=1, initialvalue=board.HEIGHT)
    if w and h:
        board.resize(w, h); view._draw_everything()


def _new_deck(root, decks: List[Deck], cards: List[Card], data_dir, refresh):
    name = simpledialog.askstring("Deck Name", "Deck name:", parent=root)
    if not name: return
    sel = _multi_card_dialog(root, cards)
    deck = Deck(name, sel); deck.shuffle()
    decks.append(deck); _save(data_dir, DECK_DB, decks); refresh()


def _multi_card_dialog(root, cards):
    win = tk.Toplevel(root); win.title("Choose Cards")
    lb = tk.Listbox(win, selectmode="multiple", width=30, height=15)
    lb.pack(padx=10, pady=10)
    for c in cards: lb.insert("end", c.name)
    chosen = []
    def ok():
        for i in lb.curselection(): chosen.append(cards[i])
        win.destroy()
    tk.Button(win, text="Add to deck", command=ok).pack(pady=6)
    win.wait_window()
    return chosen
