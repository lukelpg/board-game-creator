from __future__ import annotations
from typing import List
from .card import Card
import json, random, pathlib


class Deck:
    """Just a shuffled list of Card objects."""

    def __init__(self, name: str, cards: List[Card] | None = None):
        self.name = name
        self.cards = cards[:] if cards else []

    # ---------------- gameplay ----------------------------------------- #
    def shuffle(self):
        random.shuffle(self.cards)

    def draw(self) -> Card | None:
        return self.cards.pop() if self.cards else None

    # ---------------- persistence -------------------------------------- #
    def to_dict(self):
        return {"name": self.name,
                "cards": [c.to_dict() for c in self.cards]}

    @classmethod
    def from_dict(cls, d):
        from .card import Card
        return cls(d["name"], [Card.from_dict(cd) for cd in d["cards"]])

    def save(self, path: pathlib.Path):
        path.write_text(json.dumps(self.to_dict(), indent=2))
