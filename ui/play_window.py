# ui/play_window.py
from __future__ import annotations
import json, pathlib, queue, socket, tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from typing import Dict, List

from net.sync import GameServer, GameClient, PORT
from game import Card, Piece, Token, Deck
from game.tile import Tile
from game.game_data import BoardSpec
from game.free_board import FreeBoard
from ui.board_view      import BoardView
from ui.free_board_view import FreeBoardView
from ui.tile_grid_view  import TileGridView

# ------------------------------------------------------------------ #
def open_player(games_dir: pathlib.Path,
                img_dir: pathlib.Path,
                game_name: str):

    raw = json.loads((games_dir / f"{game_name}.json").read_text())

    cards  = {c["name"]: Card .from_dict(c) for c in raw.get("cards",  [])}
    pieces = {p["name"]: Piece.from_dict(p) for p in raw.get("pieces", [])}
    tokens = {t["name"]: Token.from_dict(t) for t in raw.get("tokens", [])}
    decks  = {d["name"]: Deck .from_dict(d, cards)
              for d in raw.get("decks",  [])}
    tiles  = {t["name"]: Tile .from_dict(t) for t in raw.get("tiles",  [])}

    root = tk.Toplevel(); root.title(f"Play-test — {raw['name']}")

    # ── sidebar ───────────────────────────────────────────────────── #
    side = ttk.Frame(root, padding=6); side.grid(row=0, column=0, sticky="ns")
    def _lbl(t): ttk.Label(side, text=t).pack(anchor="w")
    def _lb(h): lb = tk.Listbox(side, width=20, height=h); lb.pack(); return lb
    _lbl("Cards");   lbC  = _lb(6)
    _lbl("Pieces");  lbP  = _lb(6)
    _lbl("Tokens");  lbT  = _lb(6)
    _lbl("Decks");   lbD  = _lb(6)
    _lbl("Tiles");   lbTi = _lb(6)
    for nm in cards:  lbC .insert("end", nm)
    for nm in pieces: lbP .insert("end", nm)
    for nm in tokens: lbT .insert("end", nm)
    for nm in decks:  lbD .insert("end", nm)
    for nm in tiles:  lbTi.insert("end", nm)

    # ── multiplayer toolbar ───────────────────────────────────────── #
    mp_bar = ttk.Frame(root, padding=4); mp_bar.grid(row=1, column=1, sticky="ew")
    root.rowconfigure(1, weight=0)

    out_q: queue.Queue[str] = queue.Queue()
    root.out_q = out_q          # expose to all child views
    srv: GameServer | None = None
    cli: GameClient | None = None

    def start_host():
        nonlocal srv
        if srv: return
        srv = GameServer(out_q); srv.start()
        ip  = socket.gethostbyname(socket.gethostname())
        messagebox.showinfo("Hosting", f"Hosting at {ip}:{PORT}", parent=root)

    def join_host():
        nonlocal cli
        if cli: return
        ip = simpledialog.askstring("Join Game",
                                    "Host IP (blank = localhost):",
                                    parent=root)
        if ip is None:
            return
        cli = GameClient(ip, out_q); cli.start()
        root.after(500, check_client)

    def check_client():
        if cli and cli.error:
            messagebox.showerror("Join failed", cli.error, parent=root)
        elif cli and not cli.is_alive():
            messagebox.showerror("Join failed", "Disconnected.", parent=root)

    ttk.Button(mp_bar, text="Host Game", command=start_host).pack(side="left")
    ttk.Button(mp_bar, text="Join Game", command=join_host).pack(side="left")

    # ── notebook of boards ────────────────────────────────────────── #
    centre   = ttk.Frame(root, padding=6); centre.grid(row=0, column=1, sticky="nsew")
    nb_board = ttk.Notebook(centre); nb_board.pack(fill="both", expand=True)
    board_views: List[tk.Canvas] = []

    def _obj_from_rec(rec: Dict):
        typ, name = rec["type"], rec["name"]
        return (cards .get(name) if typ == "Card"  else
                pieces.get(name) if typ == "Piece" else
                tokens.get(name) if typ == "Token" else
                decks .get(name) if typ == "Deck"  else
                tiles .get(name) if typ == "Tile"  else None)

    for b in raw.get("boards", []):
        tab = ttk.Frame(nb_board)

        if b.get("mode") == "free":
            fb = FreeBoard(b["width"], b["height"], [], b["sections"])
            for rec in b.get("placed", []):
                obj = _obj_from_rec(rec)
                if obj: fb.add(obj, rec["x"], rec["y"])
            view = FreeBoardView(tab, fb, img_dir)

        elif b.get("mode") == "tilegrid":
            cols, rows = b.get("cols"), b.get("rows")
            if cols is None or rows is None:
                continue
            tg = TileGridView(tab, list(tiles.values()), cols, rows, img_dir)
            for rec in b.get("placed", []):
                tile = tiles.get(rec["name"])
                if tile:
                    tg.place_tile(tile.clone(), rec["col"], rec["row"])
            view = tg

        else:   # classic grid
            spec = BoardSpec.from_dict(b)
            view = BoardView(tab, spec.build(), img_dir)

        view.board_name = b.get("name", "Board")   # for network msgs
        view.pack(fill="both", expand=True)
        nb_board.add(tab, text=view.board_name)
        board_views.append(view)

    # ── selection handling ────────────────────────────────────────── #
    root.selected_obj = None
    def _sel(lb, store: Dict[str, object]):
        idx = lb.curselection()
        if idx: root.selected_obj = store[lb.get(idx[0])]

    lbC .bind("<<ListboxSelect>>", lambda e:_sel(lbC , cards ))
    lbP .bind("<<ListboxSelect>>", lambda e:_sel(lbP , pieces))
    lbT .bind("<<ListboxSelect>>", lambda e:_sel(lbT , tokens))
    lbD .bind("<<ListboxSelect>>", lambda e:_sel(lbD , decks ))
    lbTi.bind("<<ListboxSelect>>", lambda e:_sel(lbTi, tiles ))

    ttk.Button(side, text="Quit", command=root.destroy).pack(fill="x", pady=10)

    root.columnconfigure(1, weight=1); root.rowconfigure(0, weight=1)

    # ── network polling loop ─────────────────────────────────────── #
    def _apply_remote(cmd: Dict):
        def _dup(o):                               # ← helper inside _apply_remote
            return o.clone() if hasattr(o, "clone") else o

        if cmd.get("act") == "hello":
            messagebox.showinfo("Connected", "Multiplayer link established!", parent=root)
            return

        if cmd.get("act") == "place":
            board_name = cmd["board"]
            obj_name   = cmd["name"]
            # locate view
            try:
                idx = [nb_board.tab(i, "text") for i in nb_board.tabs()].index(board_name)
                view = board_views[idx]
            except ValueError:
                return
            # object
            obj = (cards.get(obj_name) or pieces.get(obj_name) or
                   tokens.get(obj_name) or tiles .get(obj_name) or
                   decks .get(obj_name))
            if not obj: return
            if isinstance(view, BoardView):            # grid
                view.board.place(cmd["x"], cmd["y"], _dup(obj))
                view._redraw_all()

            elif isinstance(view, FreeBoardView):      # free
                view.fb.add(_dup(obj), cmd["x"], cmd["y"])
                view._redraw()

            elif isinstance(view, TileGridView):       # tile-grid
                view.place_tile(_dup(obj), cmd["col"], cmd["row"])

    def poll_net():
        for q in (getattr(srv, "in_q", None), getattr(cli, "in_q", None)):
            if not q: continue
            while not q.empty():
                _apply_remote(json.loads(q.get()))
        root.after(50, poll_net)

    poll_net()
    root.transient(); root.grab_set(); root.wait_window()
