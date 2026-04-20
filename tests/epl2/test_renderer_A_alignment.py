"""Pin test for decision E: ``A`` Y-origin = top-left of the glyph cell.

Renders a single character at a known ``(x, y)`` with rotation 0 and font 2
and asserts that all ink pixels fall inside the expected cell rectangle.
A small alignment tolerance is allowed above the anchor (DejaVu ascenders
can stick out by a pixel when the point-size search lands on a tight fit)
but not below or to the sides.
"""

from __future__ import annotations

from labelscope.core.fonts import FontRegistry
from labelscope.epl2.renderer import render

_ANCHOR_X: int = 100
_ANCHOR_Y: int = 100
_Y_TOP_TOLERANCE: int = 2


def test_A_anchor_is_top_left_of_cell() -> None:
    """Ink from ``A100,100,0,2,1,1,N,"X"`` stays inside the font-2 cell."""
    source = b'N\nQ200,10\nq300\nA100,100,0,2,1,1,N,"X"\nP1\n'
    img = render(source)
    metrics = FontRegistry.cell_metrics(2, 1, 1, dpi=203)

    cell_left = _ANCHOR_X
    cell_right = _ANCHOR_X + metrics.width
    cell_top = _ANCHOR_Y
    cell_bottom = _ANCHOR_Y + metrics.height

    width, height = img.size
    ink_coords: list[tuple[int, int]] = [
        (x, y) for y in range(height) for x in range(width) if img.getpixel((x, y)) == 0
    ]
    assert ink_coords, "expected ink pixels for glyph 'X'"

    xs = [x for x, _ in ink_coords]
    ys = [y for _, y in ink_coords]
    assert min(xs) >= cell_left, (min(xs), cell_left)
    assert max(xs) < cell_right, (max(xs), cell_right)
    assert min(ys) >= cell_top - _Y_TOP_TOLERANCE, (min(ys), cell_top)
    assert max(ys) < cell_bottom, (max(ys), cell_bottom)
