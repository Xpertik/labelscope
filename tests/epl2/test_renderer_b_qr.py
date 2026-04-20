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
        return Image.new("1", (8, 8), color=0)

    fake_mod = types.ModuleType("treepoem")
    fake_mod.generate_barcode = fake_generate_barcode  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "treepoem", fake_mod)
    return captured


def test_b_qr_defaults_model2_eccm_mag3_with_zd410_calibration(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured = _install_fake_treepoem(monkeypatch)
    source = b'N\nQ100,10\nq200\nb20,20,Q,"hello"\nP1\n'
    img = render(source)
    # Model 2 uses the default "qrcode" symbology and omits BWIPP's
    # ``version`` option so it can auto-pick symbol size (1-40).
    assert captured["barcode_type"] == "qrcode"
    assert captured["data"] == "hello"
    assert "version" not in captured["options"]
    assert captured["options"]["eclevel"] == "M"
    # Default magnification 3 * ZD410 calibration 0.50 = 1.5.
    # 8x8 stub scaled to round(8 * 1.5) = 12x12.
    assert img.getpixel((20, 20)) == 0
    assert img.getpixel((20 + 12 - 1, 20 + 12 - 1)) == 0


def test_b_qr_honors_explicit_params(monkeypatch: pytest.MonkeyPatch) -> None:
    captured = _install_fake_treepoem(monkeypatch)
    source = b'N\nQ100,10\nq200\nb20,20,Q,m2,s5,eH,"hi"\nP1\n'
    render(source)
    assert captured["barcode_type"] == "qrcode"
    assert "version" not in captured["options"]
    assert captured["options"]["eclevel"] == "H"
