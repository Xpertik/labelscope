"""Smoke test for the two-pass renderer dispatch."""

from __future__ import annotations

from labelscope.epl2.renderer import render


def test_renders_blank_label_without_errors() -> None:
    source = b"N\nQ100,10\nq200\nP1\n"
    img = render(source)
    assert img.size == (200, 100)
    assert img.mode == "1"
    # All paper — no draw commands issued, so no ink anywhere.
    assert 0 not in set(img.getdata())
