"""Pin for Req RT3: ``h_mult`` / ``v_mult`` scale the glyph block per-axis."""

from __future__ import annotations

from PIL import Image

from labelscope.epl2.renderer import render


def _ink_bbox(img: Image.Image) -> tuple[int, int, int, int]:
    """Return the ink (``0``) bounding box; fails if none drawn."""
    inverted = img.point(lambda v: 0 if v == 1 else 255, mode="L")
    bb = inverted.getbbox()
    assert bb is not None, "expected ink in rendered image"
    return bb


def test_multipliers_scale_bbox_per_axis() -> None:
    """``h_mult=2, v_mult=2`` roughly doubles each ink-bbox dimension."""
    base = b'N\nQ120,20\nq240\nA10,10,0,2,1,1,N,"XY"\nP1\n'
    scaled = b'N\nQ120,20\nq240\nA10,10,0,2,2,2,N,"XY"\nP1\n'

    bb_base = _ink_bbox(render(base))
    bb_scaled = _ink_bbox(render(scaled))

    w_base, h_base = bb_base[2] - bb_base[0], bb_base[3] - bb_base[1]
    w_scaled, h_scaled = bb_scaled[2] - bb_scaled[0], bb_scaled[3] - bb_scaled[1]

    # Allow 1-pixel slack per axis: at small point sizes DejaVu rounds
    # differently between 1x and 2x so the ratio is 2x within 1 dot.
    assert abs(w_scaled - 2 * w_base) <= 2, (w_base, w_scaled)
    assert abs(h_scaled - 2 * h_base) <= 2, (h_base, h_scaled)
