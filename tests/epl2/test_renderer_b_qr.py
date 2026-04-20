"""``b`` 2D QR handler — default params applied when omitted."""

from __future__ import annotations

import sys
import types
from typing import Any

import pytest
from PIL import Image

from labelscope.epl2.renderer import render


def _install_fake_treepoem(monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    captured: dict[str, Any] = {}

    def fake_generate_barcode(barcode_type: str, data: str, options: dict[str, Any]) -> Image.Image:
        captured["barcode_type"] = barcode_type
        captured["data"] = data
        captured["options"] = options
        return Image.new("1", (8, 8), color=0)

    fake_mod = types.ModuleType("treepoem")
    fake_mod.generate_barcode = fake_generate_barcode  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "treepoem", fake_mod)
    return captured


def test_b_qr_defaults_model2_eccm_mag3(monkeypatch: pytest.MonkeyPatch) -> None:
    captured = _install_fake_treepoem(monkeypatch)
    source = b'N\nQ100,10\nq200\nb20,20,Q,"hello"\nP1\n'
    img = render(source)
    assert captured["barcode_type"] == "qrcode"
    assert captured["data"] == "hello"
    assert captured["options"]["version"] == 2
    assert captured["options"]["eclevel"] == "M"
    # Default magnification 3 → 8x8 stub scaled to 24x24.
    # The image contains that ink block at (20, 20).
    assert img.getpixel((20, 20)) == 0
    assert img.getpixel((20 + 24 - 1, 20 + 24 - 1)) == 0


def test_b_qr_honors_explicit_params(monkeypatch: pytest.MonkeyPatch) -> None:
    captured = _install_fake_treepoem(monkeypatch)
    source = b'N\nQ100,10\nq200\nb20,20,Q,m2,s5,eH,"hi"\nP1\n'
    render(source)
    assert captured["options"]["version"] == 2
    assert captured["options"]["eclevel"] == "H"
