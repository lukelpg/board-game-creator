"""Maintain backward-compatibility for pre-refactor modules that still do
   `from ui.view.zoom import ZoomMixin`.

   New code should import **ZoomMixin** from *ui.view.mixins.zoom* instead, but
   having this tiny wrapper means you don't have to touch dozens of legacy
   files right away (board_view.py, free_board_view.py, tile_grid_view.py …).
"""

from .mixins.zoom import ZoomMixin
__all__ = ["ZoomMixin"]
