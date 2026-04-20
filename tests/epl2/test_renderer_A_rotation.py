"""Per-element rotation of ``A`` text (Req RT2)."""

from __future__ import annotations

from PIL import Image

from labelscope.epl2.renderer import render


def _ink_bbox(img: Image.Image) -> tuple[int, int, int, int] | None:
    """Return the ink (``0``) bounding box, or ``None`` if all paper."""
    # Invert so ink becomes 255 and ``getbbox`` finds it.
    inverted = img.point(lambda v: 0 if v == 1 else 255, mode="L")
    return inverted.getbbox()


def _render_and_bbox(rot: int) -> tuple[int, int, int, int]:
    """Render a single 2-char ``A`` at the given rotation; return ink bbox."""
    source = b"N\nQ200,10\nq200\nA60,60," + str(rot).encode() + b',2,1,1,N,"XY"\nP1\n'
    bb = _ink_bbox(render(source))
    assert bb is not None, f"rotation {rot}: no ink drawn"
    return bb


def test_four_rotations_shift_bbox() -> None:
    bb0 = _render_and_bbox(0)
    bb1 = _render_and_bbox(1)
    _ = _render_and_bbox(2)
    _ = _render_and_bbox(3)
    w0, h0 = bb0[2] - bb0[0], bb0[3] - bb0[1]
    w1, h1 = bb1[2] - bb1[0], bb1[3] - bb1[1]
    # 90° rotation swaps extents.
    assert (w0, h0) == (h1, w1)
