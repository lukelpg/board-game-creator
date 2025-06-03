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

        for raw in self.sections:
            # unified accessor helpers
            pts  = raw.get("points")
            kind = raw.get("kind", "Any")
            name = raw.get("name", "Area")
            out  = raw.get("outline", "#808080")
            fill = raw.get("fill", "")

            # legacy rectangle → make a 4-point polygon
            if pts is None and {"x0", "y0", "x1", "y1"} <= raw.keys():
                pts = [(raw["x0"],      raw["y0"]),
                       (raw["x1"] + 1, raw["y0"]),
                       (raw["x1"] + 1, raw["y1"] + 1),
                       (raw["x0"],      raw["y1"] + 1)]

            bd.add_section(name,
                           SectionType(kind.capitalize()),
                           pts,
                           out,
                           fill)
        return bd

    def to_dict(self):
        return {
            "name": self.name,
            "w": self.width,
            "h": self.height,
            "sections": self.sections
        }

    @classmethod
    def from_dict(cls, d):
        """
        Accept either old‐style ('w','h') or new‐style ('width','height').
        """
        # Extract the board name (should always exist)
        name = d.get("name", "")

        # Old style:  keys 'w' and 'h'
        if "w" in d and "h" in d:
            w = d["w"]
            h = d["h"]
            secs = d.get("sections", [])
            return cls(name, w, h, secs)

        # New style: keys 'width' and 'height'
        if "width" in d and "height" in d:
            w = d["width"]
            h = d["height"]
            secs = d.get("sections", [])
            return cls(name, w, h, secs)

        # Fallback: if someone saved a BoardSpec via to_dict(), 'w' & 'h' should exist.
        # If not, treat it as an empty 8×8 board.
        return cls(name, 8, 8, d.get("sections", []))


# ---------- full game data -------------------------------------------- #
@dataclass
class GameData:
    name: str
    cards : List[Card]
    pieces: List[Piece]
    tokens: List[Token]
    decks : List[Deck]
    boards: List[Any]

    # ---------- serialise --------------------------------------------- #
    def to_dict(self):
        return {
            "name":   self.name,
            "cards":  [c.to_dict() for c in self.cards ],
            "pieces": [p.to_dict() for p in self.pieces],
            "tokens": [t.to_dict() for t in self.tokens],
            "decks":  [d.to_dict() for d in self.decks ],
            "boards": [
                (b.to_dict() if isinstance(b, BoardSpec) else b)
                for b in self.boards
            ],
        }

    # ---------- de-serialise (handles **old & new** formats) ----------- #
    @classmethod
    def from_dict(cls, d):
        from .card  import Card
        from .piece import Piece
        from .token import Token
        from .deck  import Deck

        # Rebuild cards & lookup map
        cards  = [Card.from_dict(c) for c in d.get("cards", [])]
        card_map = {c.name: c for c in cards}

        pieces = [Piece.from_dict(p) for p in d.get("pieces", [])]
        tokens = [Token.from_dict(t) for t in d.get("tokens", [])]

        # Rebuild decks using names
        decks  = [Deck.from_dict(dd, card_map) for dd in d.get("decks", [])]

        # --- NEW format (grid + free boards mixed) -------------------
        boards = []
        for bd in d.get("boards", []):
            # 1) Free‐board dict (mode:"free") → keep verbatim
            if isinstance(bd, dict) and bd.get("mode") == "free":
                boards.append(bd)
                continue

            # 2) Grid board, old style: {'name', 'w', 'h', 'sections'}
            if isinstance(bd, dict) and "w" in bd and "h" in bd and "sections" in bd:
                boards.append(BoardSpec(bd["name"], bd["w"], bd["h"], bd["sections"]))
                continue

            # 3) Grid board, new style: {'name', 'width', 'height', 'sections'}
            if isinstance(bd, dict) and "width" in bd and "height" in bd and "sections" in bd:
                boards.append(BoardSpec(bd["name"], bd["width"], bd["height"], bd["sections"]))
                continue

            # 4) Unexpected format, try BoardSpec.from_dict (legacy)
            boards.append(BoardSpec.from_dict(bd))

        # Safety default if nothing found
        if not boards:
            boards = [BoardSpec("Main", 8, 8, [])]

        return cls(d["name"], cards, pieces, tokens, decks, boards)






