from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import List, Dict, Any
from .card  import Card
from .piece import Piece
from .token import Token
from .deck  import Deck
from .board import Board, SectionType


@dataclass
class GameData:
    """All editable content for one game."""
    name: str
    cards : List[Card]
    pieces: List[Piece]
    tokens: List[Token]
    decks : List[Deck]
    board_width : int
    board_height: int
    sections: List[Dict[str, Any]]      # raw dicts for sections

    # ---------- helpers ------------------------------------------------ #
    def to_dict(self):
        return {
            "name":   self.name,
            "cards":  [c.to_dict() for c in self.cards],
            "pieces": [p.to_dict() for p in self.pieces],
            "tokens": [t.to_dict() for t in self.tokens],
            "decks":  [d.to_dict() for d in self.decks],
            "board": {
                "w": self.board_width,
                "h": self.board_height,
                "sections": self.sections,
            }
        }

    @classmethod
    def from_dict(cls, d):
        from .card  import Card
        from .piece import Piece
        from .token import Token
        from .deck  import Deck
        b = d["board"]
        return cls(
            d["name"],
            [Card .from_dict(c) for c in d["cards"]],
            [Piece.from_dict(p) for p in d["pieces"]],
            [Token.from_dict(t) for t in d["tokens"]],
            [Deck .from_dict(k) for k in d["decks"]],
            b["w"], b["h"], b["sections"]
        )

    # ---------- build a Board object ---------------------------------- #
    def make_board(self):
        from .board import Board, Section
        bd = Board(self.board_width, self.board_height)
        from .board import SectionType
        for s in self.sections:
            bd.add_section(s["x0"], s["y0"], s["x1"], s["y1"],
                           SectionType(s["kind"]))
        return bd
