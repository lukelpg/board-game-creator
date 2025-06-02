from __future__ import annotations
from typing import List
from .card import Card
import json, random, pathlib, copy


class Deck:
    """Named pile of cards with draw / shuffle / reset."""

    def __init__(self, name: str, cards: List[Card] | None = None):
        self.name      = name
        self._original = cards[:] if cards else []
        self.cards     = self._original[:]

    # ---------------- gameplay ----------------------------------------- #
    def shuffle(self):
        random.shuffle(self.cards)

    def draw(self) -> Card | None:
        return self.cards.pop() if self.cards else None

    def reset(self):
        self.cards = self._original[:]

    # ---------------- persistence -------------------------------------- #
    def to_dict(self):
        return {"name": self.name,
                "cards": [c.to_dict() for c in self._original]}

    @classmethod
    def from_dict(cls, d):
        from .card import Card
        return cls(d["name"], [Card.from_dict(cd) for cd in d["cards"]])

    # quick clone (used by BoardView when resetting pile on board)
    def clone(self):                   # keeps original list intact
        dup = Deck(self.name, self._original)
        dup.cards = self.cards[:]
        return dup
