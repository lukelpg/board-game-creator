from __future__ import annotations
import PySimpleGUI as sg
import json, pathlib
from typing import List
from game import Card, Deck, Board, Player, GameEngine
from .card_editor import CardEditor
from .board_view import BoardView

CARD_DB = "cards.json"

# ---------- helpers -------------------------------------------------------
def load_cards(data_dir: pathlib.Path) -> List[Card]:
    path = data_dir / CARD_DB
    return [] if not path.exists() else [Card.from_dict(d) for d in json.loads(path.read_text())]

def save_cards(data_dir: pathlib.Path, cards: List[Card]):
    (data_dir / CARD_DB).write_text(json.dumps([c.to_dict() for c in cards], indent=2))

# ---------- main window ---------------------------------------------------
def run_app(data_dir: pathlib.Path, images_dir: pathlib.Path):
    sg.theme("SystemDefault")

    cards = load_cards(data_dir)
    deck  = Deck("Main", cards.copy())
    board = Board()
    players = [Player("Player 1"), Player("Player 2")]
    engine  = GameEngine(players, deck, board)

    list_key = "-CARDLIST-"

    def refresh():
        window[list_key].update(values=[c.name for c in cards])

    # callback from editor
    def on_card_saved(card: Card):
        cards.append(card)
        save_cards(data_dir, cards)
        refresh()

    card_editor = CardEditor(images_dir, on_card_saved)
    board_view  = BoardView(board, lambda *a: None)

    layout = [
        [
            sg.Column([
                [sg.Text("Cards")],
                [sg.Listbox([c.name for c in cards], size=(20,12), key=list_key)],
                [sg.Button("Shuffle Deck", key="-SHUFFLE-")],
            ]),
            sg.VSeperator(),
            sg.Column([[board_view.layout()]]),
            sg.VSeperator(),
            sg.Column([[card_editor.layout()]]),
        ]
    ]

    window = sg.Window("Card & Board Game", layout, finalize=True)
    selected: Card | None = None

    while True:
        event, values = window.read()
        if event == sg.WINDOW_CLOSED:
            break

        if event == "-SHUFFLE-":
            deck.shuffle()
            sg.popup("Deck shuffled")

        if event == list_key and values[list_key]:
            idx = window[list_key].curselection[0]
            selected = cards[idx]

        board_view.read_event(event, values, selected)
        card_editor.read_event(event, values)

    window.close()
