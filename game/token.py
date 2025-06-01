from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional, List, Tuple
import uuid

Point = Tuple[int, int]        # (x, y) within 0-64 canvas coordinates


@dataclass
class Token:
    """Cardboard cut-out token (optionally custom polygon)."""
    id: str
    name: str
    description: str = ""
    image_path: Optional[str] = None
    points: List[Point] | None = None          # <-- defaulted **last**

    # -------------- helpers ------------------------------------------- #
    @classmethod
    def new(cls, name: str, desc: str = "",
            image_path: str | None = None,
            points: List[Point] | None = None):
        return cls(str(uuid.uuid4()), name, desc, image_path, points)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Token":
        return cls(**d)
