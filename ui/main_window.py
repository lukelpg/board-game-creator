from __future__ import annotations
import tkinter as tk
from tkinter import ttk, messagebox
import json, pathlib
from typing import List
from game import Card, Deck, Board, Player, GameEngine
from .card_editor import CardEditor
from .board_view  import BoardView

CARD_DB = "cards.json"

# -------------------------------------------------------------------- #
def load_cards(data_dir: pathlib.Path) -> List[Card]:
    p = data_dir / CARD_DB
    return [] if not p.exists() else [Card.from_dict(d) for d in json.loads(p.read_text())]

def save_cards(data_dir: pathlib.Path, cards: List[Card]):
    (data_dir / CARD_DB).write_text(json.dumps([c.to_dict() for c in cards], indent=2))

# -------------------------------------------------------------------- #
def run_app(data_dir: pathlib.Path, images_dir: pathlib.Path):
    root = tk.Tk()
    root.title("Card & Board Game")

    cards: List[Card] = load_cards(data_dir)
    deck = Deck("Main", cards.copy())
    board = Board()
    players = [Player("Player 1"), Player("Player 2")]
    engine  = GameEngine(players, deck, board)

    # ---------- left pane (card list) ---------------------------------- #
    left = ttk.Frame(root, padding=6)
    left.grid(row=0, column=0, sticky="ns")

    ttk.Label(left, text="Cards").pack(anchor="w")
    listbox = tk.Listbox(left, height=12, width=20)
    listbox.pack(fill="y", expand=True)

    def refresh():
        listbox.delete(0, "end")
        for c in cards:
            listbox.insert("end", c.name)
    refresh()

    def shuffle():
        deck.shuffle()
        messagebox.showinfo("Deck", "Deck shuffled")
    ttk.Button(left, text="Shuffle Deck", command=shuffle).pack(pady=4)

    # ---------- center (board) ----------------------------------------- #
    center = ttk.Frame(root, padding=6)
    center.grid(row=0, column=1)
    board_view = BoardView(center, board, lambda *a: None)
    board_view.pack()

    # ---------- right pane (editor) ------------------------------------ #
    right = CardEditor(root, images_dir, on_save=lambda c: (cards.append(c),
                                                           save_cards(data_dir, cards),
                                                           refresh()))
    right.grid(row=0, column=2, sticky="n")

    # share selected card with board_view
    root.selected_card: Card | None = None
    def on_select(evt):
        idxs = listbox.curselection()
        root.selected_card = cards[idxs[0]] if idxs else None
    listbox.bind("<<ListboxSelect>>", on_select)

    # grid weights
    root.columnconfigure(1, weight=1)
    root.rowconfigure(0, weight=1)

    root.mainloop()
