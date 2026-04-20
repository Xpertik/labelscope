"""Synthetic UPC-A render smoke — selector ``UA0`` → BWIPP ``upca``.

Runs against a real ``treepoem`` when importable; skipped otherwise so the
CI matrix without Ghostscript stays green. The assertion is deliberately
loose (non-empty mode ``"1"`` image with both ink and paper present).
"""

from __future__ import annotations

import pytest

from labelscope.epl2.renderer import render


def test_B_upca_synthetic_renders_mode1_image() -> None:
    """``B…UA0…"01234567890"`` renders a non-empty 1-bit UPC-A symbol."""
    pytest.importorskip("treepoem")
    source = b'N\nQ200,10\nq300\nB100,100,0,UA0,2,3,50,N,"01234567890"\nP1\n'
    img = render(source)
    assert img.mode == "1"
    assert img.size[0] > 0 and img.size[1] > 0
    pixels = set(img.getdata())
    assert 0 in pixels, "expected ink pixels in UPC-A output"
    assert 1 in pixels, "expected paper pixels in UPC-A output"
