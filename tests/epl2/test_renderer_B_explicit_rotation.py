"""Pin for Req RB4: 1D barcode rotation + anchor correction."""

from __future__ import annotations

import sys
import types
from typing import Any

import pytest
from PIL import Image

from labelscope.epl2.renderer import render


def _install_fake_treepoem(monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    """Install a fake ``treepoem`` module returning a wide (16x1) stub."""
    captured: dict[str, Any] = {}

    def fake_generate_barcode(
        barcode_type: str,
        data: str,
        options: dict[str, Any],
        *,
        scale: int = 2,
    ) -> Image.Image:
        captured["barcode_type"] = barcode_type
        # Wide bar pattern: 16 cols, 1 row of all-ink so resize to
        # ``height`` produces a wide horizontal barcode.
        return Image.new("1", (16, 1), color=0)

    fake_mod = types.ModuleType("treepoem")
    fake_mod.generate_barcode = fake_generate_barcode  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "treepoem", fake_mod)
    return captured


def _ink_bbox(img: Image.Image) -> tuple[int, int, int, int]:
    """Return the ink (``0``) bounding box; fails if none drawn."""
    inverted = img.point(lambda v: 0 if v == 1 else 255, mode="L")
    bb = inverted.getbbox()
    assert bb is not None, "expected ink in rendered image"
    return bb


def test_B_rotation_1_flips_wide_bars_to_tall(monkeypatch: pytest.MonkeyPatch) -> None:
    """A wider-than-tall barcode becomes taller-than-wide at rotation=1."""
    _install_fake_treepoem(monkeypatch)
    # rotation=0 vs rotation=1, same narrow/height so pre-rotation the
    # rendered barcode is a 16-wide by 10-tall block → wider than tall.
    src_rot0 = b'N\nQ200,10\nq300\nB50,50,0,1B,1,2,10,N,"X"\nP1\n'
    src_rot1 = b'N\nQ200,10\nq300\nB50,50,1,1B,1,2,10,N,"X"\nP1\n'

    bb0 = _ink_bbox(render(src_rot0))
    bb1 = _ink_bbox(render(src_rot1))

    w0, h0 = bb0[2] - bb0[0], bb0[3] - bb0[1]
    w1, h1 = bb1[2] - bb1[0], bb1[3] - bb1[1]
    # Pre-rotation is wider than tall.
    assert w0 > h0, (w0, h0)
    # Post-rotation (90° CW) swaps the extents.
    assert h1 > w1, (w1, h1)
    # And rot=1 anchor offset (-W, 0) shifts bars to the LEFT of x=50.
    assert bb1[2] <= 50, ("max_x should be <= anchor x after rot=1", bb1)
