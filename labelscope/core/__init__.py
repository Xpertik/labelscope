"""Core rendering primitives shared across label languages (EPL2, ZPL, ...).

This package is intentionally language-agnostic: it must not hardcode
assumptions specific to EPL2 (e.g. coordinate origin, command ordering).
"""

from __future__ import annotations

from labelscope.core.barcodes import BarcodeBackendMissing, render_1d, render_2d
from labelscope.core.canvas import Canvas
from labelscope.core.errors import (
    InvalidArgument,
    LabelscopeError,
    MalformedString,
    ParseError,
    UnknownCommand,
)
from labelscope.core.fonts import CellMetrics, FontRegistry
from labelscope.core.geometry import Rect, dots_to_mm, mm_to_dots, rotate_quarter

__all__ = [
    "BarcodeBackendMissing",
    "Canvas",
    "CellMetrics",
    "FontRegistry",
    "InvalidArgument",
    "LabelscopeError",
    "MalformedString",
    "ParseError",
    "Rect",
    "UnknownCommand",
    "dots_to_mm",
    "mm_to_dots",
    "render_1d",
    "render_2d",
    "rotate_quarter",
]
