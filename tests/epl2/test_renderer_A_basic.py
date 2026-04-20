"""Basic ``A`` command renders glyphs into the canvas."""

from __future__ import annotations

from labelscope.epl2.renderer import render


def test_A_command_paints_ink() -> None:
    source = b'N\nQ100,10\nq200\nA10,10,0,2,1,1,N,"HI"\nP1\n'
    img = render(source)
    pixels = set(img.getdata())
    # Some pixels must be ink (0) where glyphs landed.
    assert 0 in pixels
    # And paper pixels (non-zero) must still exist (sanity).
    assert any(p != 0 for p in pixels)
