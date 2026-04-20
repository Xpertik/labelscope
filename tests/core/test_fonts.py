"""Tests for the bundled-font registry."""

from __future__ import annotations

import pytest
from PIL import ImageFont

from labelscope.core.fonts import CellMetrics, FontRegistry


@pytest.mark.parametrize(
    ("font_num", "h", "v", "expected"),
    [
        (1, 1, 1, CellMetrics(width=8, height=12)),
        (2, 1, 1, CellMetrics(width=10, height=16)),
        (3, 1, 1, CellMetrics(width=12, height=20)),
        (4, 1, 1, CellMetrics(width=14, height=24)),
        (5, 1, 1, CellMetrics(width=32, height=48)),
        (2, 2, 3, CellMetrics(width=20, height=48)),
    ],
)
def test_cell_metrics_203dpi(font_num: int, h: int, v: int, expected: CellMetrics) -> None:
    assert FontRegistry.cell_metrics(font_num, h, v, dpi=203) == expected


def test_cell_metrics_300dpi_differs_from_203() -> None:
    a = FontRegistry.cell_metrics(2, 1, 1, dpi=203)
    b = FontRegistry.cell_metrics(2, 1, 1, dpi=300)
    assert a != b


def test_cell_metrics_rejects_unknown_font() -> None:
    with pytest.raises(ValueError):
        FontRegistry.cell_metrics(99, 1, 1, dpi=203)


def test_cell_metrics_rejects_unknown_dpi() -> None:
    with pytest.raises(ValueError):
        FontRegistry.cell_metrics(1, 1, 1, dpi=600)


def test_get_returns_freetype_font() -> None:
    font = FontRegistry.get(2, 1, 1, dpi=203)
    assert isinstance(font, ImageFont.FreeTypeFont)


def test_get_is_cached() -> None:
    a = FontRegistry.get(2, 1, 1, dpi=203)
    b = FontRegistry.get(2, 1, 1, dpi=203)
    # Same underlying cached instance.
    assert a is b
