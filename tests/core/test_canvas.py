"""Tests for the 1-bit label canvas."""

from __future__ import annotations

from PIL import Image

from labelscope.core.canvas import Canvas


def test_canvas_starts_white() -> None:
    canvas = Canvas(width=20, height=10)
    assert canvas.width == 20
    assert canvas.height == 10
    img = canvas.to_pil()
    assert img.mode == "1"
    assert img.size == (20, 10)
    # All pixels are paper (1).
    assert set(img.getdata()) == {1}


def test_draw_rect_paints_ink() -> None:
    canvas = Canvas(width=10, height=10)
    canvas.draw_rect(x=2, y=3, w=4, h=2, fill=0)
    img = canvas.to_pil()
    # Inside rect is ink (0), corners outside stay paper (1).
    assert img.getpixel((2, 3)) == 0
    assert img.getpixel((5, 4)) == 0
    assert img.getpixel((0, 0)) == 1
    assert img.getpixel((6, 5)) == 1


def test_draw_rect_zero_area_noop() -> None:
    canvas = Canvas(width=5, height=5)
    canvas.draw_rect(x=1, y=1, w=0, h=3, fill=0)
    assert set(canvas.to_pil().getdata()) == {1}


def test_transpose_180_twice_is_identity() -> None:
    canvas = Canvas(width=6, height=4)
    canvas.draw_rect(x=0, y=0, w=2, h=2, fill=0)
    before = list(canvas.to_pil().getdata())
    canvas.transpose_180()
    canvas.transpose_180()
    after = list(canvas.to_pil().getdata())
    assert before == after


def test_transpose_180_flips_corner() -> None:
    canvas = Canvas(width=4, height=2)
    canvas.draw_rect(x=0, y=0, w=1, h=1, fill=0)
    assert canvas.to_pil().getpixel((0, 0)) == 0
    canvas.transpose_180()
    assert canvas.to_pil().getpixel((3, 1)) == 0


def test_to_pil_returns_copy() -> None:
    canvas = Canvas(width=3, height=3)
    snapshot = canvas.to_pil()
    canvas.draw_rect(x=0, y=0, w=3, h=3, fill=0)
    assert set(snapshot.getdata()) == {1}


def test_draw_text_bitmap_keeps_ink_union() -> None:
    canvas = Canvas(width=6, height=4)
    glyph = Image.new("1", (2, 2), color=0)  # all-ink glyph
    canvas.draw_text_bitmap(glyph, x=1, y=1)
    img = canvas.to_pil()
    assert img.getpixel((1, 1)) == 0
    assert img.getpixel((2, 2)) == 0
    assert img.getpixel((0, 0)) == 1
