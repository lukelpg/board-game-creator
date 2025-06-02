from __future__ import annotations
import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
import json, pathlib
from typing import List
from game.game_data import GameData
from ui.creator_window import open_creator
from ui.play_window    import open_player


def launch_selector(games_dir: pathlib.Path,
                    images_dir: pathlib.Path):
    root = tk.Tk(); root.title("Select a Game")

    lb = tk.Listbox(root, width=30, height=12)
    lb.pack(padx=10, pady=10)

    def refresh():
        lb.delete(0, "end")
        for f in sorted(games_dir.glob("*.json")):
            lb.insert("end", f.stem)
    refresh()

    # ---------------- buttons ---------------- #
    def _new():
        name = simpledialog.askstring("New Game", "Game name:", parent=root)
        if not name: return
        path = games_dir / f"{name}.json"
        if path.exists():
            messagebox.showerror("Exists", "A game with that name already exists")
            return
        gd = GameData(name, [], [], [], [],
                      8, 8, [])        # blank template
        path.write_text(json.dumps(gd.to_dict(), indent=2))
        refresh()

    def _edit():
        sel = lb.curselection()
        if not sel: return
        name = lb.get(sel[0])
        root.withdraw()
        open_creator(games_dir, images_dir, name)
        root.deiconify(); refresh()

    def _play():
        sel = lb.curselection()
        if not sel: return
        name = lb.get(sel[0])
        root.withdraw()
        open_player(games_dir, images_dir, name)
        root.deiconify()

    ttk.Button(root, text="New Game", command=_new).pack(fill="x", padx=10)
    ttk.Button(root, text="Edit (Creator Mode)", command=_edit).pack(fill="x", padx=10, pady=4)
    ttk.Button(root, text="Play-test", command=_play).pack(fill="x", padx=10)

    root.mainloop()
