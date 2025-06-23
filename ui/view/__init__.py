"""Unified view package – re‑exports the most common classes so callers can:

    from ui.view import GridView, FreeBoardView, TileGridView

without worrying about the folder structure."""

from .grids.grid_view import GridView          # classic square grid / Board
from .free.free_board_view import FreeBoardView
from .grids.tile_grid_view import TileGridView

__all__ = [
    "GridView",
    "FreeBoardView",
    "TileGridView",
]
