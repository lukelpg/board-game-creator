from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional
import uuid

@dataclass
class Card:
    """A single game card."""
    id: str
    name: str
    description: str = ""
    image_path: Optional[str] = None   # stored relative to data/images
    attack: int = 0
    defense: int = 0

    # ---- helpers ---------------------------------------------------------
    @classmethod
    def new(cls, name: str, description: str = "",
            image_path: Optional[str] = None,
            attack: int = 0, defense: int = 0) -> "Card":
        return cls(str(uuid.uuid4()), name, description,
                   image_path, attack, defense)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Card":
        return cls(**d)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
