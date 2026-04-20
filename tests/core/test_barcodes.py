"""Tests for the barcode adapter (mocked treepoem)."""

from __future__ import annotations

import sys
import types
from typing import Any

import pytest
from PIL import Image

import labelscope.core.barcodes as barcodes


def _make_fake_treepoem(monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    """Install a fake ``treepoem`` module and capture its call arguments."""
    captured: dict[str, Any] = {}

    def fake_generate_barcode(
        barcode_type: str, data: str, options: dict[str, Any]
    ) -> Image.Image:
        captured["barcode_type"] = barcode_type
        captured["data"] = data
        captured["options"] = options
        return Image.new("1", (8, 4), color=1)

    fake_mod = types.ModuleType("treepoem")
    fake_mod.generate_barcode = fake_generate_barcode  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "treepoem", fake_mod)
    return captured


def test_render_1d_code128_prepends_subset_b_sentinel(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured = _make_fake_treepoem(monkeypatch)
    barcodes.render_1d("code128", "W1A/1000260", scale=1, human_readable=False)
    assert captured["barcode_type"] == "code128"
    assert captured["data"] == "^104W1A/1000260"
    assert captured["options"]["parse"] is True
    assert captured["options"]["includetext"] is False


def test_render_1d_upca_does_not_add_sentinel(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured = _make_fake_treepoem(monkeypatch)
    barcodes.render_1d("upca", "01234567890", scale=1, human_readable=True)
    assert captured["barcode_type"] == "upca"
    assert captured["data"] == "01234567890"
    assert "parse" not in captured["options"]
    assert captured["options"]["includetext"] is True


def test_render_1d_scales_output(monkeypatch: pytest.MonkeyPatch) -> None:
    _make_fake_treepoem(monkeypatch)
    img = barcodes.render_1d("code128", "X", scale=3, human_readable=False)
    assert img.size == (24, 12)
    assert img.mode == "1"


def test_render_2d_qr_passes_model_and_ecc(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured = _make_fake_treepoem(monkeypatch)
    barcodes.render_2d("qrcode", "hello", model=2, ecc="M", magnification=1)
    assert captured["barcode_type"] == "qrcode"
    assert captured["data"] == "hello"
    assert captured["options"]["version"] == 2
    assert captured["options"]["eclevel"] == "M"


def test_render_2d_magnifies_via_nearest(monkeypatch: pytest.MonkeyPatch) -> None:
    _make_fake_treepoem(monkeypatch)
    img = barcodes.render_2d("qrcode", "hi", model=2, ecc="M", magnification=4)
    assert img.size == (32, 16)


def test_missing_treepoem_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(sys.modules, "treepoem", None)
    with pytest.raises(barcodes.BarcodeBackendMissing):
        barcodes.render_1d("code128", "X", scale=1, human_readable=False)
