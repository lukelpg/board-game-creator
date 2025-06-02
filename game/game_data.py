from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict, Any

from .card  import Card
from .piece import Piece
from .token import Token
from .deck  import Deck
from .board import Board, SectionType


# ---------- board spec ------------------------------------------------- #
@dataclass
class BoardSpec:
    name: str
    width: int
    height: int
    sections: List[Dict[str, Any]]        # raw section dicts

    def build(self) -> Board:
        bd = Board(self.width, self.height)
        for s in self.sections:
            bd.add_section(s["x0"], s["y0"], s["x1"], s["y1"],
                           SectionType(s["kind"]))
        return bd

    def to_dict(self):
        return {"name": self.name,
                "w": self.width,
                "h": self.height,
                "sections": self.sections}

    @classmethod
    def from_dict(cls, d):
        return cls(d["name"], d["w"], d["h"], d["sections"])


# ---------- full game data -------------------------------------------- #
@dataclass
class GameData:
    name: str
    cards : List[Card]
    pieces: List[Piece]
    tokens: List[Token]
    decks : List[Deck]
    boards: List[BoardSpec]

    # ---------- serialise --------------------------------------------- #
    def to_dict(self):
        return {
            "name":   self.name,
            "cards":  [c.to_dict() for c in self.cards ],
            "pieces": [p.to_dict() for p in self.pieces],
            "tokens": [t.to_dict() for t in self.tokens],
            "decks":  [d.to_dict() for d in self.decks ],
            "boards": [b.to_dict() for b in self.boards],
        }

    # ---------- de-serialise (handles **old & new** formats) ----------- #
    @classmethod
    def from_dict(cls, d):
        from .card  import Card
        from .piece import Piece
        from .token import Token
        from .deck  import Deck

        cards  = [Card .from_dict(c) for c in d.get("cards" , [])]
        pieces = [Piece.from_dict(p) for p in d.get("pieces", [])]
        tokens = [Token.from_dict(t) for t in d.get("tokens", [])]
        decks  = [Deck .from_dict(k) for k in d.get("decks" , [])]

        # ---- NEW format ------------------------------------------------
        if "boards" in d:
            boards = [BoardSpec.from_dict(b) for b in d["boards"]]
            if not boards:           # safety – ensure at least one board
                boards = [BoardSpec("Main", 8, 8, [])]
            return cls(d["name"], cards, pieces, tokens, decks, boards)

        # ---- OLD format fallback --------------------------------------
        # old schema: 'board':{'w','h','sections'}
        b = d.get("board") or {}
        w = b.get("w", d.get("board_width" , 8))
        h = b.get("h", d.get("board_height", 8))
        secs = b.get("sections", [])
        boards = [BoardSpec("Main", w, h, secs)]
        return cls(d["name"], cards, pieces, tokens, decks, boards)
