"""Synthetic EAN-13 render smoke — selector ``E`` → BWIPP ``ean13``.

Uses the bare ``E`` family selector to exercise the fallback mapping in
``_B_SYMBOLOGY_MAP``. Runs against a real ``treepoem`` when importable;
skipped otherwise.
"""

from __future__ import annotations

import pytest

from labelscope.epl2.renderer import render


def test_B_ean13_synthetic_renders_mode1_image() -> None:
    """``B…E…"590123412345"`` renders a non-empty 1-bit EAN-13 symbol."""
    pytest.importorskip("treepoem")
    source = b'N\nQ200,10\nq300\nB100,100,0,E,2,3,50,N,"590123412345"\nP1\n'
    img = render(source)
    assert img.mode == "1"
    assert img.size[0] > 0 and img.size[1] > 0
    pixels = set(img.getdata())
    assert 0 in pixels, "expected ink pixels in EAN-13 output"
    assert 1 in pixels, "expected paper pixels in EAN-13 output"
