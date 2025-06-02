from __future__ import annotations
import tkinter as tk
from tkinter import ttk, messagebox
import json, pathlib
from typing import List
from game import Card, Piece, Token, Deck
from game.game_data import GameData
from .card_editor   import CardEditor
from .piece_editor  import PieceEditor
from .token_editor  import TokenEditor
from .board_view    import BoardView
from .catalog_view  import CatalogViewer
from game.board     import SectionType


def open_creator(games_dir: pathlib.Path,
                 img_dir: pathlib.Path,
                 game_name: str):

    # ---- load file ---------------------------------------------------- #
    path = games_dir / f"{game_name}.json"
    j = json.loads(path.read_text())
    gd = GameData.from_dict(j)

    root = tk.Toplevel(); root.title(f"Creator – {gd.name}")

    # ---- state -------------------------------------------------------- #
    cards  : List[Card]  = gd.cards
    pieces : List[Piece] = gd.pieces
    tokens : List[Token] = gd.tokens
    decks  : List[Deck]  = gd.decks
    board  = gd.make_board()

    # ---- sidebar lists ------------------------------------------------ #
    side = ttk.Frame(root, padding=6); side.grid(row=0, column=0, sticky="ns")
    def _lbl(txt): ttk.Label(side, text=txt).pack(anchor="w")
    def _lb(): lb = tk.Listbox(side, width=22, height=5); lb.pack(); return lb
    _lbl("Cards");   lbC = _lb()
    _lbl("Pieces");  lbP = _lb()
    _lbl("Tokens");  lbT = _lb()
    _lbl("Decks");   lbD = _lb()

    # ▼▼▼  ADD THIS FUNCTION +
    def _new_deck():
        name = tk.simpledialog.askstring("Deck name", "Deck name:", parent=root)
        if not name:
            return
        # choose cards
        dlg = tk.Toplevel(root); dlg.title("Add cards to deck")
        clb = tk.Listbox(dlg, selectmode="multiple", width=30, height=15)
        clb.pack(padx=8, pady=8)
        for c in cards:
            clb.insert("end", c.name)
        def _done():
            chosen = [cards[i] for i in clb.curselection()]
            d = Deck(name, chosen)
            d.shuffle()
            decks.append(d)
            refresh()
            dlg.destroy()
        tk.Button(dlg, text="Create deck", command=_done).pack(pady=6)

    # ▲▲▲  AND THIS BUTTON
    ttk.Button(side, text="New Deck", command=_new_deck)\
        .pack(fill="x", pady=(4,2))

    def refresh():
        lbC.delete(0,"end"); [lbC.insert("end", c.name) for c in cards]
        lbP.delete(0,"end"); [lbP.insert("end", p.name) for p in pieces]
        lbT.delete(0,"end"); [lbT.insert("end", t.name) for t in tokens]
        lbD.delete(0,"end"); [lbD.insert("end", d.name) for d in decks]
    refresh()

    # ---- board view --------------------------------------------------- #
    centre = ttk.Frame(root, padding=6); centre.grid(row=0, column=1)
    view = BoardView(centre, board, img_dir, lambda *a: None)
    view.pack()

    # ---- editors ------------------------------------------------------ #
    nb = ttk.Notebook(root); nb.grid(row=0,column=2, sticky="n")
    nb.add(CardEditor (nb,img_dir,lambda c:(cards.append(c),refresh())),text="Card")
    nb.add(PieceEditor(nb,img_dir,lambda p:(pieces.append(p),refresh())),text="Piece")
    nb.add(TokenEditor(nb,img_dir,lambda t:(tokens.append(t),refresh())),text="Token")

    # ---- buttons ------------------------------------------------------ #
    ttk.Button(side, text="Section (drag)", command=view.enter_section_mode)\
        .pack(fill="x", pady=(6,2))
    ttk.Button(side, text="Catalog",
               command=lambda: CatalogViewer(root,cards,pieces,tokens,img_dir))\
        .pack(fill="x", pady=2)
    ttk.Button(side, text="Save Game",
               command=lambda:_save())\
        .pack(fill="x", pady=(10,2))
    ttk.Button(side, text="Close", command=root.destroy).pack(fill="x")

    # ---- save --------------------------------------------------------- #
    def _save():
        gd.cards,gd.pieces,gd.tokens,gd.decks = cards,pieces,tokens,decks
        gd.board_width,gd.board_height = board.WIDTH, board.HEIGHT
        gd.sections = [dict(x0=s.x0,y0=s.y0,x1=s.x1,y1=s.y1,kind=s.kind.value)
                       for s in board.sections]
        path.write_text(json.dumps(gd.to_dict(), indent=2))
        messagebox.showinfo("Saved", "Game saved!")

    # ---- selection propagation --------------------------------------- #
    root.selected_obj=None
    def _sel(lb,store): idx=lb.curselection(); root.selected_obj=store[idx[0]] if idx else None
    lbC.bind("<<ListboxSelect>>",lambda e:_sel(lbC,cards))
    lbP.bind("<<ListboxSelect>>",lambda e:_sel(lbP,pieces))
    lbT.bind("<<ListboxSelect>>",lambda e:_sel(lbT,tokens))
    lbD.bind("<<ListboxSelect>>",lambda e:_sel(lbD,decks))

    root.columnconfigure(1,weight=1); root.rowconfigure(0,weight=1)
    root.transient(); root.grab_set(); root.wait_window()
