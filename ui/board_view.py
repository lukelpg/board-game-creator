"""Thin wrapper kept so legacy imports like `from ui.board_view import BoardView`
   continue to work after the refactor.  All logic now lives in
   *ui.view.grids.grid_view.GridView* so there is no code duplication.
"""

from ui.view.grids.grid_view import GridView as BoardView  # re-export
__all__ = ["BoardView"]