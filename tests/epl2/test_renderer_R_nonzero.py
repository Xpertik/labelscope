"""Pin for Req RC2 R-nonzero: ``R x,y`` shifts subsequent draws by (x, y)."""

from __future__ import annotations

from PIL import Image

from labelscope.epl2.renderer import render


def _ink_bbox(img: Image.Image) -> tuple[int, int, int, int]:
    """Return the ink (``0``) bounding box; fails if none drawn."""
    inverted = img.point(lambda v: 0 if v == 1 else 255, mode="L")
    bb = inverted.getbbox()
    assert bb is not None, "expected ink in rendered image"
    return bb


def test_R_shifts_glyph_by_its_offset() -> None:
    """Same ``A`` renders 20 dots right and 30 dots down under ``R20,30``."""
    base = b'N\nQ100,80\nq200\nA10,10,0,2,1,1,N,"X"\nP1\n'
    with_r = b'R20,30\nN\nQ100,80\nq200\nA10,10,0,2,1,1,N,"X"\nP1\n'

    bb_base = _ink_bbox(render(base))
    bb_shift = _ink_bbox(render(with_r))

    # Both images must be the same size so offsets compare directly.
    assert render(base).size == render(with_r).size

    dx = bb_shift[0] - bb_base[0]
    dy = bb_shift[1] - bb_base[1]
    assert (dx, dy) == (20, 30)
