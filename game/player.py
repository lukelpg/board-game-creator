from __future__ import annotations
from typing import List
from .card import Card

class Player:
    def __init__(self, name: str):
        self.name = name
        self.hand: List[Card] = []

    def draw(self, deck):
        card = deck.draw()
        if card:
            self.hand.append(card)
