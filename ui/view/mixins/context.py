"""Right‑click common context‑menu: Delete on every object, and Deck helpers
(Draw, Shuffle, Reset). Subclasses just supply *_delete_selected()* and optional
*_*draw_card(deck)* handler.*"""

from __future__ import annotations
import tkinter as tk
from typing import Callable
from game.deck import Deck      # type: ignore

class ContextMenuMixin:
    def _popup_common(self, ev: tk.Event, obj, delete_cb: Callable[[], None]):  # type: ignore[name-defined]
        menu = tk.Menu(self, tearoff=0)
        if isinstance(obj, Deck):
            menu.add_command(label="Draw",    command=lambda d=obj: self._draw_card(d))
            menu.add_separator()
            menu.add_command(label="Shuffle", command=lambda d=obj:(d.shuffle(), self.redraw()))  # type: ignore[attr-defined]
            menu.add_command(label="Reset",   command=lambda d=obj:(d.reset(),   self.redraw()))  # type: ignore[attr-defined]
            menu.add_separator()
        menu.add_command(label="Delete", command=lambda:(delete_cb(), self.redraw()))  # type: ignore[attr-defined]
        menu.tk_popup(ev.x_root, ev.y_root)

    # optional – only needed if the subclass shows Decks
    def _draw_card(self, deck: Deck): ...