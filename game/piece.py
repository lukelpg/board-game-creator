from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional
import uuid

@dataclass
class Piece:
    """A board piece / miniature / token (non-card)."""
    id: str
    name: str
    description: str = ""
    image_path: Optional[str] = None

    # ------------ helpers ---------------------------------------------- #
    @classmethod
    def new(cls, name: str, desc: str = "", image_path: str | None = None):
        return cls(str(uuid.uuid4()), name, desc, image_path)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Piece":
        return cls(**d)
