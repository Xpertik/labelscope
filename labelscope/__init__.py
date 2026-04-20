"""labelscope: preview thermal printer labels (EPL2, ZPL planned) from source code."""

from __future__ import annotations

from labelscope.epl2.renderer import Renderer, render

__all__ = ["Renderer", "__version__", "render"]
__version__ = "0.1.0"
