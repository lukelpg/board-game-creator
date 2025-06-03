from __future__ import annotations
from typing import List
from .card import Card
import random, copy


class Deck:
    def __init__(self, name: str, cards: List[Card]):
        self.name       = name
        self._original  = cards[:]          # pristine order
        self.cards      = cards[:]          # working stack

    # ---------- gameplay -------------------------------------------- #
    def shuffle(self):
        random.shuffle(self.cards)

    def draw(self) -> Card | None:
        return self.cards.pop() if self.cards else None

    def reset(self):
        self.cards = self._original[:]

    def clone(self) -> "Deck":
        dup = Deck(self.name, self._original)
        dup.cards = self.cards[:]            # keep remaining stack
        return dup

    # ---------- (de)serialise --------------------------------------- #
    def to_dict(self):
        """Save just card **names** to keep file small and avoid duplication."""
        return {"name": self.name,
                "cards": [c.name for c in self._original]}

    @classmethod
    def from_dict(cls, d, card_lookup: dict[str, Card]):
        """card_lookup maps name → Card object reconstructed once."""
        card_objs = [card_lookup[n] for n in d["cards"] if n in card_lookup]
        return cls(d["name"], card_objs)
