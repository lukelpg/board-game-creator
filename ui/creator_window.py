# ui/creator_window.py
from __future__ import annotations
import json, pathlib, tkinter as tk
from tkinter import ttk, simpledialog, messagebox
from typing import List, Dict, Any

from game import Card, Piece, Token, Deck
from game.tile         import Tile
from game.board        import SectionType
from game.game_data    import GameData, BoardSpec
from game.free_board   import FreeBoard

from ui.board_view      import BoardView
from ui.free_board_view import FreeBoardView
from ui.tile_grid_view  import TileGridView
from ui.card_editor     import CardEditor
from ui.piece_editor    import PieceEditor
from ui.token_editor    import TokenEditor
from ui.catalog_view    import CatalogViewer
from ui.section_catalog import SectionCatalog
from ui.tile_editor     import TileEditor
from ui.tile_catalog    import TileCatalog

# ------------------------------------------------------------------ #
def open_creator(games_dir: pathlib.Path,
                 img_dir:  pathlib.Path,
                 game_name: str):

    # ---------- load ---------------------------------------------- #
    path = games_dir / f"{game_name}.json"
    gd   = GameData.from_dict(json.loads(path.read_text()))

    root = tk.Toplevel(); root.title(f"Creator – {gd.name}")

    # ---------- working copies ------------------------------------ #
    cards  : List[Card]  = list(gd.cards)
    pieces : List[Piece] = list(gd.pieces)
    tokens : List[Token] = list(gd.tokens)
    decks  : List[Deck]  = list(gd.decks)
    tiles  : List[Tile]  = list(gd.tiles)
    boards : List[Any]   = list(gd.boards)   # BoardSpec *or* dict

    # ---------- sidebar ------------------------------------------- #
    side = ttk.Frame(root, padding=6); side.grid(row=0, column=0, sticky="ns")
    def _lbl(t): ttk.Label(side, text=t).pack(anchor="w")
    def _lb():   lb = tk.Listbox(side, width=22, height=5); lb.pack(); return lb
    _lbl("Cards");   lbC  = _lb()
    _lbl("Pieces");  lbP  = _lb()
    _lbl("Tokens");  lbT  = _lb()
    _lbl("Decks");   lbD  = _lb()
    _lbl("Tiles");   lbTi = _lb()

    # ---------- notebook of boards -------------------------------- #
    nb_board = ttk.Notebook(root); nb_board.grid(row=0, column=1, sticky="nsew")
    root.columnconfigure(1, weight=1); root.rowconfigure(0, weight=1)
    board_views: List[tk.Canvas] = []

    # ---------- helper to add tabs -------------------------------- #
    def _add_board_tab(bs):
        if isinstance(bs, dict) and bs.get("mode") == "free":
            fb = FreeBoard(bs["width"], bs["height"], [], bs["sections"])
            for rec in bs.get("placed", []):
                obj = (next((c for c in cards  if c.name == rec["name"]), None) or
                       next((p for p in pieces if p.name == rec["name"]), None) or
                       next((t for t in tokens if t.name == rec["name"]), None) or
                       next((d for d in decks  if d.name == rec["name"]), None))
                if obj: fb.add(obj, rec["x"], rec["y"])

            frm  = ttk.Frame(nb_board)
            view = FreeBoardView(frm, fb, img_dir); view.pack(fill="both", expand=True)
            view.board_name = bs.get("name", "Board")
            nb_board.add(frm, text=view.board_name); board_views.append(view)

        elif isinstance(bs, dict) and bs.get("mode") == "tilegrid":
            frm  = ttk.Frame(nb_board)
            view = TileGridView(frm, tiles, bs["cols"], bs["rows"],
                    img_dir, shape=bs.get("shape", "rect"))
            view.pack(fill="both", expand=True)
            view.board_name = bs.get("name", "Tiles")
            nb_board.add(frm, text=view.board_name); board_views.append(view)

        else:  # classic grid
            frm  = ttk.Frame(nb_board)
            view = BoardView(frm, bs.build(), img_dir)
            view.pack(fill="both", expand=True)
            view.board_name = bs.name
            nb_board.add(frm, text=view.board_name); board_views.append(view)

    for b in boards:
        _add_board_tab(b)

    # ---------- editors (cards / pieces / …) ----------------------- #
    editors = ttk.Notebook(root); editors.grid(row=0, column=2, sticky="n")
    editors.add(CardEditor (editors, img_dir, lambda c:(cards.append(c), _refresh())), text="Card")
    editors.add(PieceEditor(editors, img_dir, lambda p:(pieces.append(p),_refresh())), text="Piece")
    editors.add(TokenEditor(editors, img_dir, lambda t:(tokens.append(t),_refresh())), text="Token")
    editors.add(TileEditor (editors, img_dir, lambda t:(tiles.append(t), _refresh())), text="Tile")

    # ---------- list refresh helper -------------------------------- #
    def _refresh():
        for lb, seq in ((lbC, cards), (lbP, pieces), (lbT, tokens),
                        (lbD, decks), (lbTi, tiles)):
            lb.delete(0, "end"); [lb.insert("end", o.name) for o in seq]
    _refresh()

    # ---------- current-view convenience --------------------------- #
    def _cur_view():
        idx = nb_board.index(nb_board.select()); return board_views[idx]

    # ---------- sidebar buttons ------------------------------------ #
    ttk.Button(side, text="New Deck", command=lambda:_new_deck()).pack(fill="x", pady=(2,4))
    ttk.Button(side, text="New Board",command=lambda:_new_board()).pack(fill="x", pady=(2,4))
    ttk.Button(side, text="Section (drag)",
               command=lambda:_cur_view().enter_section_mode())\
        .pack(fill="x", pady=(2,4))
    ttk.Button(side, text="Catalog",
               command=lambda: CatalogViewer(root, cards, pieces, tokens, img_dir))\
        .pack(fill="x", pady=(2,4))
    ttk.Button(side, text="Sections",
        command=lambda: SectionCatalog(
            root,
            (_cur_view().board.sections if hasattr(_cur_view(), "board")
                                       else _cur_view().fb.sections),
            (_cur_view()._redraw_all    if hasattr(_cur_view(), "_redraw_all")
                                       else _cur_view()._redraw)
        )).pack(fill="x", pady=(2,4))
    ttk.Button(side, text="Tiles",
               command=lambda: TileCatalog(root, tiles, _refresh))\
        .pack(fill="x", pady=(2,4))

    # ---------- delete-board button (now on sidebar) --------------- #
    style = ttk.Style(); style.configure("Danger.TButton", foreground="red")
    def _del_board():
        if not nb_board.tabs(): return
        idx = nb_board.index(nb_board.select())
        nb_board.forget(idx)
        del boards[idx]; del board_views[idx]
    ttk.Button(side, text="🗑 Delete Board",
               style="Danger.TButton",
               command=_del_board).pack(fill="x", pady=(2,4))

    ttk.Button(side, text="Save Game", command=lambda:_save())\
        .pack(fill="x", pady=(10,2))
    ttk.Button(side, text="Close", command=root.destroy).pack(fill="x")

    # ---------- deck creator --------------------------------------- #
    def _new_deck():
        name = simpledialog.askstring("Deck Name", "Deck name:", parent=root)
        if not name: return
        dlg = tk.Toplevel(root); dlg.title("Select Cards")
        lb = tk.Listbox(dlg, selectmode="multiple", width=30, height=15); lb.pack(padx=8, pady=8)
        [lb.insert("end", c.name) for c in cards]
        def done():
            chosen = [cards[i] for i in lb.curselection()]
            decks.append(Deck(name, chosen)); _refresh(); dlg.destroy()
        tk.Button(dlg, text="Create Deck", command=done).pack(pady=6)
        dlg.transient(root); dlg.grab_set(); dlg.wait_window()

    # ---------- create new board ----------------------------------- #
    def _new_board():
        bname = simpledialog.askstring("Board Name", "Board name:", parent=root)
        if not bname: return
        style = simpledialog.askstring("Style", "grid / free / tilegrid",
                                       initialvalue="free", parent=root)
        style = (style or "free").lower()

        if style == "grid":
            w = simpledialog.askinteger("Columns", "Width:",  minvalue=1, initialvalue=8, parent=root)
            h = simpledialog.askinteger("Rows",    "Height:", minvalue=1, initialvalue=8, parent=root)
            if w and h:
                spec = BoardSpec(bname, w, h, [])
                boards.append(spec); _add_board_tab(spec)

        elif style == "free":
            w = simpledialog.askinteger("Canvas W", "Width (px):",  minvalue=200, initialvalue=800, parent=root)
            h = simpledialog.askinteger("Canvas H", "Height (px):", minvalue=200, initialvalue=600, parent=root)
            if w and h:
                fb = {"mode":"free","name":bname,"width":w,"height":h,
                      "sections":[],"placed":[]}
                boards.append(fb); _add_board_tab(fb)

        elif style == "tilegrid":
            shape = simpledialog.askstring("Tile shape", "rect / hex",
                                           initialvalue="hex", parent=root)
            cols  = simpledialog.askinteger("Columns", "Cols:", minvalue=1, initialvalue=6, parent=root)
            rows  = simpledialog.askinteger("Rows", "Rows:",  minvalue=1, initialvalue=4, parent=root)
            if shape and cols and rows:
                tg = {"mode":"tilegrid","name":bname,"shape":shape,
                      "cols":cols,"rows":rows,"placed":[]}
                boards.append(tg); _add_board_tab(tg)

    # ---------- save ----------------------------------------------- #
    def _save():
        boards_out: List[Dict[str,Any]] = []
        for idx, view in enumerate(board_views):
            tab_name = nb_board.tab(nb_board.tabs()[idx], "text")

            if isinstance(view, BoardView):              # grid
                bd = view.board
                boards_out.append({
                    "mode":"grid","name":tab_name,
                    "width":bd.WIDTH,"height":bd.HEIGHT,
                    "sections":[{"name":getattr(s,"name",tab_name),
                                 "kind":  s.kind.value,
                                 "points":s.points,
                                 "outline":getattr(s,"outline","#808080"),
                                 "fill":   getattr(s,"fill","")}
                                for s in bd.sections]
                })

            elif isinstance(view, FreeBoardView):        # free
                fb = view.fb
                boards_out.append({
                    "mode":"free","name":tab_name,
                    "width":fb.width,"height":fb.height,
                    "sections":fb.sections,
                    "placed":[{"type":type(p.obj).__name__,
                               "name":p.obj.name, "x":p.x,"y":p.y}
                              for p in fb.placed]
                })

            elif isinstance(view, TileGridView):         # tile-grid
                tg = view; placed=[]
                for r in range(tg.rows):
                    for c in range(tg.cols):
                        t = tg.grid[r][c]
                        if t: placed.append({"name":t.name,"row":r,"col":c})
                boards_out.append({
                    "mode":"tilegrid","name":tab_name,
                    "shape":tg.tileset[0].shape if tg.tileset else "hex",
                    "cols":tg.cols,"rows":tg.rows,"placed":placed
                })

        gd.cards, gd.pieces, gd.tokens, gd.tiles, gd.decks, gd.boards = \
            cards,    pieces,    tokens,    tiles,   decks, boards_out
        path.write_text(json.dumps(gd.to_dict(), indent=2))
        messagebox.showinfo("Saved", "Game saved!")

    # ---------- selection propagation ------------------------------ #
    root.selected_obj = None
    def _sel(lb, store): idx = lb.curselection(); root.selected_obj = store[idx[0]] if idx else None
    lbC .bind("<<ListboxSelect>>", lambda e:_sel(lbC , cards ))
    lbP .bind("<<ListboxSelect>>", lambda e:_sel(lbP , pieces))
    lbT .bind("<<ListboxSelect>>", lambda e:_sel(lbT , tokens))
    lbD .bind("<<ListboxSelect>>", lambda e:_sel(lbD , decks ))
    lbTi.bind("<<ListboxSelect>>", lambda e:_sel(lbTi, tiles ))

    root.transient(); root.grab_set(); root.wait_window()
