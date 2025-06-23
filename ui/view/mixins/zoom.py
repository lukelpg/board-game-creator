"""Ctrl‑wheel zooming extracted from the previous ZoomMixin so it can be reused
unaltered by every canvas view. The behaviour is identical to the original –
scales between 0.25× and 3× and calls _zoom_changed(scale) if the subclass
implements it."""

from __future__ import annotations
import tkinter as tk

class ZoomMixin:
    """Adds Ctrl‑wheel zooming (0.25×‑3×) to a *tk.Canvas* subclass."""

    _scale = 1.0          # class‑wide – shared across all canvases

    # ---------------------------------------------------------- #
    # public helper (call once in __init__)
    # ---------------------------------------------------------- #
    def _bind_zoom(self) -> None:      # noqa: D401 (imperative)
        # Windows / Linux – wheel event delta ±120
        self.bind("<Control-MouseWheel>", self._on_zoom)
        # macOS – Button‑4/5 generate ±1 or ±3 deltas
        self.bind("<Control-Button-4>",   lambda e: self._on_zoom(e,  120))
        self.bind("<Control-Button-5>",   lambda e: self._on_zoom(e, -120))

    # ---------------------------------------------------------- #
    # internal handler
    # ---------------------------------------------------------- #
    def _on_zoom(self, event: tk.Event, delta: int | None = None) -> None:  # type: ignore[name-defined]
        delta = event.delta if delta is None else delta
        factor = 1.2 if delta > 0 else 1/1.2
        new    = min(3.0, max(0.25, self._scale * factor))
        if abs(new - self._scale) < 0.001:
            return                       # nothing changed

        self._scale = new
        self.scale("all", 0, 0, factor, factor)
        self.configure(scrollregion=self.bbox("all"))
        if hasattr(self, "_zoom_changed"):
            # let subclass update globals / constants
            self._zoom_changed(self._scale)       # type: ignore[attr-defined]
