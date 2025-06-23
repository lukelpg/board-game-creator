class ZoomMixin:
    """Adds Ctrl-wheel zooming (0.25×-3.0×) to a Tk Canvas."""
    _scale = 1.0
    def _bind_zoom(self):
        # Windows / Linux   wheel event delta in event.delta (120/-120)
        # macOS             use <MouseWheel> with event.delta = ±1 or ±3
        self.bind("<Control-MouseWheel>", self._on_zoom)
        self.bind("<Control-Button-4>",   lambda e: self._on_zoom(e,  120))
        self.bind("<Control-Button-5>",   lambda e: self._on_zoom(e, -120))

    def _on_zoom(self, event, delta=None):
        delta = delta if delta is not None else event.delta
        f = 1.2 if delta > 0 else 1/1.2
        new = min(3.0, max(0.25, self._scale * f))
        if abs(new - self._scale) < 0.001:
            return
        self._scale = new
        self.scale("all", 0, 0, f, f)      # zoom canvas items
        self.configure(scrollregion=self.bbox("all"))
        if hasattr(self, "_zoom_changed"):
            self._zoom_changed(self._scale)
