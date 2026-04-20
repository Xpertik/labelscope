"""Reverse-video ``A`` (Req RT4) — black rect with white glyph holes."""

from __future__ import annotations

from labelscope.epl2.renderer import render


def test_reverse_video_draws_black_rect_with_white_glyphs() -> None:
    # Font 4 @203dpi cell is 14x24. "O/S" is 3 chars → 42x24 ink block.
    source = b'N\nQ100,30\nq80\nA10,4,0,4,1,1,R,"O/S"\nP1\n'
    img = render(source)

    # Top-left corner of the cell must be ink (part of the black rect).
    assert img.getpixel((10, 4)) == 0
    # Bottom-right corner of the scaled cell must also be ink.
    assert img.getpixel((10 + 42 - 1, 4 + 24 - 1)) == 0

    # Inside the black rect, SOME pixel must be paper (glyph hole).
    # Pillow's mode "1" stores "paper" as either 1 or 255 depending on
    # whether the region has been mutated by a composition op; both are
    # non-zero.
    region = img.crop((10, 4, 10 + 42, 4 + 24))
    pixels = list(region.getdata())
    assert any(p != 0 for p in pixels), "no paper pixels inside the reverse-video rect"

    # Outside the rect, pixels stay paper (non-zero).
    assert img.getpixel((0, 0)) != 0


def test_reverse_video_empty_data_draws_nothing() -> None:
    source = b'N\nQ30,10\nq60\nA0,0,0,2,1,1,R,""\nP1\n'
    img = render(source)
    # Empty data → no rect, no glyphs → no ink anywhere.
    assert 0 not in set(img.getdata())
