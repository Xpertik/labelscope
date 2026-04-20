"""Pin for Req RB1 HRI=B: ``human_readable=True`` flows to BWIPP options."""

from __future__ import annotations

import sys
import types
from typing import Any

import pytest
from PIL import Image

from labelscope.epl2.renderer import render


def _install_fake_treepoem(monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    """Install a fake ``treepoem`` module that captures call kwargs."""
    captured: dict[str, Any] = {}

    def fake_generate_barcode(
        barcode_type: str,
        data: str,
        options: dict[str, Any],
        *,
        scale: int = 2,
    ) -> Image.Image:
        captured["barcode_type"] = barcode_type
        captured["data"] = data
        captured["options"] = options
        return Image.new("1", (16, 8), color=0)

    fake_mod = types.ModuleType("treepoem")
    fake_mod.generate_barcode = fake_generate_barcode  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "treepoem", fake_mod)
    return captured


def test_B_hri_flag_enables_includetext(monkeypatch: pytest.MonkeyPatch) -> None:
    """``B...,B,"HELLO"`` passes ``includetext=True`` to BWIPP."""
    captured = _install_fake_treepoem(monkeypatch)
    source = b'N\nQ200,10\nq300\nB100,100,0,1B,1,2,50,B,"HELLO"\nP1\n'
    render(source)
    assert captured["options"]["includetext"] is True
