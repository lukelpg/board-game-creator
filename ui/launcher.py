# launcher.py
from __future__ import annotations

import argparse
import json
import pathlib
import tkinter as tk
from tkinter import ttk, simpledialog, messagebox

from game.game_data import GameData, BoardSpec
from ui.creator_window import open_creator
from ui.play_window import open_player


# --------------------------------------------------------------------------- #
# CLI wrapper – lets you choose where games / images live without editing code
# --------------------------------------------------------------------------- #
def main() -> None:
    parser = argparse.ArgumentParser(description="Table-top game launcher")
    parser.add_argument(
        "-g", "--games", default="games", help="Directory that stores *.json games (default: ./games/)"
    )
    parser.add_argument(
        "-i", "--images", default="images", help="Directory that stores shared images (default: ./images/)"
    )
    args = parser.parse_args()

    games_dir = pathlib.Path(args.games).expanduser().resolve()
    images_dir = pathlib.Path(args.images).expanduser().resolve()
    games_dir.mkdir(parents=True, exist_ok=True)
    images_dir.mkdir(parents=True, exist_ok=True)

    launch_selector(games_dir, images_dir)


# --------------------------------------------------------------------------- #
# GUI selector
# --------------------------------------------------------------------------- #
def launch_selector(games_dir: pathlib.Path, images_dir: pathlib.Path) -> None:
    root = tk.Tk()
    root.title("Select a Game")
    root.resizable(False, False)

    # ——— main frame -------------------------------------------------------- #
    frame = ttk.Frame(root, padding=10)
    frame.pack(fill="both", expand=True)

    lb = tk.Listbox(frame, width=42, height=12, activestyle="dotbox")
    lb.grid(row=0, column=0, sticky="nsew")
    frame.rowconfigure(0, weight=1)
    frame.columnconfigure(0, weight=1)

    sb = ttk.Scrollbar(frame, orient="vertical", command=lb.yview)
    sb.grid(row=0, column=1, sticky="ns")
    lb.configure(yscrollcommand=sb.set)

    # ——— utilities --------------------------------------------------------- #
    def refresh() -> None:
        lb.delete(0, "end")
        for path in sorted(games_dir.glob("*.json")):
            lb.insert("end", path.stem)

    def create_blank_game() -> None:
        name = simpledialog.askstring("New Game", "Game name:", parent=root)
        if not name:
            return
        path = games_dir / f"{name}.json"
        if path.exists():
            messagebox.showerror("Exists", "A game with that name already exists.", parent=root)
            return

        blank = GameData(
            name=name,
            cards=[],
            pieces=[],
            tokens=[],
            decks=[],
            boards=[BoardSpec("Main", 8, 8, [])],
        )
        path.write_text(json.dumps(blank.to_dict(), indent=2))
        refresh()
        # auto-select the new game so the user can jump straight into edit/play
        idx = lb.get(0, "end").index(name)
        lb.selection_set(idx)

    def edit_selected(_evt=None) -> None:  # noqa: ANN001
        if not lb.curselection():
            return
        root.withdraw()
        open_creator(games_dir, images_dir, lb.get(lb.curselection()[0]))
        root.deiconify()
        refresh()

    def play_selected(_evt=None) -> None:  # noqa: ANN001
        if not lb.curselection():
            return
        root.withdraw()
        open_player(games_dir, images_dir, lb.get(lb.curselection()[0]))
        root.deiconify()

    # ——— listbox shortcuts -------------------------------------------------- #
    lb.bind("<Double-Button-1>", play_selected)
    lb.bind("<Return>", play_selected)

    # ——— control buttons ---------------------------------------------------- #
    btns = ttk.Frame(frame)
    btns.grid(row=1, column=0, columnspan=2, pady=(8, 0), sticky="ew")

    ttk.Button(btns, text="New Game", command=create_blank_game).pack(fill="x")
    ttk.Button(btns, text="Edit (Creator Mode)", command=edit_selected).pack(fill="x", pady=4)
    ttk.Button(btns, text="Play-test", command=play_selected).pack(fill="x")

    refresh()
    root.mainloop()


# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    main()
