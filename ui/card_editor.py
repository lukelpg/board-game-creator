from __future__ import annotations
import PySimpleGUI as sg
import pathlib
from typing import Callable, Optional
from game.card import Card

class CardEditor:
    """Widget for creating/editing cards."""

    def __init__(self, images_dir: pathlib.Path, on_save: Callable[[Card], None]):
        self.images_dir = images_dir
        self.on_save = on_save
        self.card: Optional[Card] = None
        self._build_layout()

    # ---------------- public API -----------------------------------------
    def layout(self):
        return self.column

    # ---------------- internals ------------------------------------------
    def _build_layout(self):
        self.name_key = "-NAME-"
        self.desc_key = "-DESC-"
        self.img_key  = "-IMG-"
        self.atk_key  = "-ATK-"
        self.def_key  = "-DEF-"
        self.save_key = "-SAVE-"

        self.column = sg.Column([
            [sg.Text("Name"), sg.Input(key=self.name_key)],
            [sg.Text("Description"), sg.Multiline(size=(30,4), key=self.desc_key)],
            [sg.Text("Image"), sg.Input(key=self.img_key, enable_events=True), sg.FileBrowse()],
            [sg.Text("Attack"), sg.Input(size=(5,1), key=self.atk_key),
             sg.Text("Defense"), sg.Input(size=(5,1), key=self.def_key)],
            [sg.Button("Save", key=self.save_key)],
        ])

    def read_event(self, event, values):
        if event == self.save_key:
            self._save(values)
        elif event == self.img_key and values[self.img_key]:
            self._copy_image(values[self.img_key])

    # ---------------- helpers --------------------------------------------
    def _copy_image(self, path):
        src = pathlib.Path(path)
        if src.exists():
            dest = self.images_dir / src.name
            dest.write_bytes(src.read_bytes())

    def _save(self, v):
        name = v[self.name_key].strip()
        if not name:
            sg.popup_error("Card name required")
            return
        card = Card.new(
            name,
            v[self.desc_key],
            pathlib.Path(v[self.img_key]).name if v[self.img_key] else None,
            int(v[self.atk_key] or 0),
            int(v[self.def_key] or 0),
        )
        self.on_save(card)
        sg.popup("Saved “%s”" % card.name)
