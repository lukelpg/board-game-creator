from __future__ import annotations
import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
import json, pathlib
from typing import List

from game import Card, Piece, Token, Deck
from game.board     import SectionType
from game.game_data import GameData, BoardSpec
from .board_view    import BoardView
from .card_editor   import CardEditor
from .piece_editor  import PieceEditor
from .token_editor  import TokenEditor
from .catalog_view  import CatalogViewer


# --------------------------------------------------------------------- #
def open_creator(games_dir: pathlib.Path,
                 img_dir: pathlib.Path,
                 game_name: str):

    # ---------- load --------------------------------------------------- #
    path = games_dir / f"{game_name}.json"
    gd   = GameData.from_dict(json.loads(path.read_text()))

    root = tk.Toplevel(); root.title(f"Creator – {gd.name}")

    # ---------- state lists ------------------------------------------- #
    cards  : List[Card]  = list(gd.cards)
    pieces : List[Piece] = list(gd.pieces)
    tokens : List[Token] = list(gd.tokens)
    decks  : List[Deck]  = list(gd.decks)
    boards : List[BoardSpec] = list(gd.boards)   # editable list

    # ---------- sidebar lists ----------------------------------------- #
    side = ttk.Frame(root, padding=6); side.grid(row=0, column=0, sticky="ns")
    def _lbl(txt): ttk.Label(side, text=txt).pack(anchor="w")
    def _lst(): lb = tk.Listbox(side, width=22, height=5); lb.pack(); return lb
    _lbl("Cards");   lbC = _lst()
    _lbl("Pieces");  lbP = _lst()
    _lbl("Tokens");  lbT = _lst()
    _lbl("Decks");   lbD = _lst()

    # ---------- board notebook ---------------------------------------- #
    board_notebook = ttk.Notebook(root)
    board_notebook.grid(row=0, column=1, sticky="nsew")
    root.columnconfigure(1, weight=1); root.rowconfigure(0, weight=1)

    board_views: List[BoardView] = []

    def _add_board_tab(bspec: BoardSpec):
        frm = ttk.Frame(board_notebook)
        view = BoardView(frm, bspec.build(), img_dir)
        view.pack()
        board_notebook.add(frm, text=bspec.name)
        board_views.append(view)

    for bs in boards:
        _add_board_tab(bs)

    # ---------- editor notebook --------------------------------------- #
    editors = ttk.Notebook(root); editors.grid(row=0, column=2, sticky="n")
    editors.add(CardEditor (editors, img_dir, lambda c:(cards.append(c), _refresh())), text="Card")
    editors.add(PieceEditor(editors, img_dir, lambda p:(pieces.append(p),_refresh())), text="Piece")
    editors.add(TokenEditor(editors, img_dir, lambda t:(tokens.append(t),_refresh())), text="Token")

    # ---------- helpers ------------------------------------------------ #
    def _refresh():
        lbC.delete(0,"end"); [lbC.insert("end", c.name) for c in cards]
        lbP.delete(0,"end"); [lbP.insert("end", p.name) for p in pieces]
        lbT.delete(0,"end"); [lbT.insert("end", t.name) for t in tokens]
        lbD.delete(0,"end"); [lbD.insert("end", d.name) for d in decks]
    _refresh()

    def _current_view() -> BoardView:
        idx = board_notebook.index(board_notebook.select())
        return board_views[idx]

    # ---------- buttons ------------------------------------------------ #
    ttk.Button(side, text="New Deck", command=lambda:_new_deck()).pack(fill="x", pady=(2,4))
    ttk.Button(side, text="New Board", command=lambda:_new_board()).pack(fill="x", pady=(2,4))
    ttk.Button(side, text="Section (drag)",
               command=lambda:_current_view().enter_section_mode())\
        .pack(fill="x", pady=(2,4))
    ttk.Button(side, text="Catalog",
               command=lambda: CatalogViewer(root, cards, pieces, tokens, img_dir))\
        .pack(fill="x", pady=(2,4))
    ttk.Button(side, text="Save Game", command=lambda:_save())\
        .pack(fill="x", pady=(10,2))
    ttk.Button(side, text="Close", command=root.destroy).pack(fill="x")

    # ---------- deck maker -------------------------------------------- #
    def _new_deck():
        name = simpledialog.askstring("Deck Name", "Deck name:", parent=root)
        if not name:
            return
        dlg = tk.Toplevel(root); dlg.title("Select Cards")
        lb = tk.Listbox(dlg, selectmode="multiple", width=30, height=15)
        lb.pack(padx=8, pady=8)
        for c in cards: lb.insert("end", c.name)
        def done():
            chosen = [cards[i] for i in lb.curselection()]
            d = Deck(name, chosen); d.shuffle()
            decks.append(d); _refresh(); dlg.destroy()
        tk.Button(dlg, text="Create Deck", command=done).pack(pady=6)
        dlg.transient(root); dlg.grab_set(); dlg.wait_window()

    # ---------- new board dialog -------------------------------------- #
    def _new_board():
        bname = simpledialog.askstring("Board Name", "Board name:", parent=root)
        if not bname: return
        w = simpledialog.askinteger("Columns", "Width:", minvalue=1, initialvalue=8, parent=root)
        h = simpledialog.askinteger("Rows",    "Height:",minvalue=1, initialvalue=8, parent=root)
        if not (w and h): return
        spec = BoardSpec(bname, w, h, [])
        boards.append(spec); _add_board_tab(spec)

    # ---------- save file --------------------------------------------- #
    def _save():
        # sync board specs with current board_views
        for spec, view in zip(boards, board_views):
            bd = view.board
            spec.width, spec.height = bd.WIDTH, bd.HEIGHT
            spec.sections = [dict(x0=s.x0, y0=s.y0, x1=s.x1, y1=s.y1,
                                  kind=s.kind.value) for s in bd.sections]

        gd.cards , gd.pieces, gd.tokens, gd.decks, gd.boards = \
            cards, pieces, tokens, decks, boards
        path.write_text(json.dumps(gd.to_dict(), indent=2))
        messagebox.showinfo("Saved", "Game saved!")

    # ---------- propagate selection object ---------------------------- #
    root.selected_obj = None
    def _sel(lb, store):
        idx = lb.curselection()
        root.selected_obj = store[idx[0]] if idx else None
    lbC.bind("<<ListboxSelect>>", lambda e:_sel(lbC, cards ))
    lbP.bind("<<ListboxSelect>>", lambda e:_sel(lbP, pieces))
    lbT.bind("<<ListboxSelect>>", lambda e:_sel(lbT, tokens))
    lbD.bind("<<ListboxSelect>>", lambda e:_sel(lbD, decks ))

    root.transient(); root.grab_set(); root.wait_window()
