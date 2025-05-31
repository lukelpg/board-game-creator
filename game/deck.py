from __future__ import annotations
from typing import List
from .card import Card
import json
import random
import pathlib

class Deck:
    """A list of cards with shuffle/draw helpers."""

    def __init__(self, name: str, cards: List[Card] | None = None):
        self.name = name
        self.cards = cards[:] if cards else []

    # ---------- gameplay --------------------------------------------------
    def shuffle(self) -> None:
        random.shuffle(self.cards)

    def draw(self) -> Card | None:
        return self.cards.pop() if self.cards else None

    # ---------- persistence ----------------------------------------------
    def to_dict(self):
        return {"name": self.name,
                "cards": [c.to_dict() for c in self.cards]}

    @classmethod
    def from_dict(cls, d):
        from .card import Card
        return cls(d["name"], [Card.from_dict(cd) for cd in d["cards"]])

    @classmethod
    def load_or_create(cls, path: pathlib.Path, name: str):
        if path.exists():
            with path.open("r", encoding="utf-8") as f:
                return cls.from_dict(json.load(f))
        return cls(name)

    def save(self, path: pathlib.Path):
        with path.open("w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)
