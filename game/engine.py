from __future__ import annotations
from typing import List
from .player import Player
from .deck import Deck
from .board import Board

class GameEngine:
    """Turn-based engine (extend to add rules)."""

    def __init__(self, players: List[Player], deck: Deck, board: Board):
        self.players = players
        self.current_idx = 0
        self.deck = deck
        self.board = board

    # ---------- turn helpers ---------------------------------------------
    @property
    def current_player(self):
        return self.players[self.current_idx]

    def end_turn(self):
        self.current_idx = (self.current_idx + 1) % len(self.players)

    # ---------- rule hooks ------------------------------------------------
    def can_place(self, x, y, card):
        return True   # override for custom rules

    def after_place(self, x, y, card):
        pass
