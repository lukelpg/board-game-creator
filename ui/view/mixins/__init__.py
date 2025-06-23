"""Mix‑ins shared by every canvas view."""

from .zoom import ZoomMixin
from .section import SectionMixin
from .context import ContextMenuMixin

__all__ = ["ZoomMixin", "SectionMixin", "ContextMenuMixin"]
