"""``B`` 1D barcode handler — mocked treepoem + optional real-backend smoke."""

from __future__ import annotations

import sys
import types
from typing import Any

import pytest
from PIL import Image

from labelscope.epl2.renderer import render


def _install_fake_treepoem(monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    """Install a fake ``treepoem`` module and capture ``generate_barcode`` args."""
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
        return Image.new("1", (16, 8), color=0)  # all-ink stub

    fake_mod = types.ModuleType("treepoem")
    fake_mod.generate_barcode = fake_generate_barcode  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "treepoem", fake_mod)
    return captured


def test_B_1B_forces_code128_subset_b_via_mocked_treepoem(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured = _install_fake_treepoem(monkeypatch)
    source = b'N\nQ100,10\nq200\nB50,50,0,1B,1,2,35,N,"ABC"\nP1\n'
    render(source)
    assert captured["barcode_type"] == "code128"
    assert captured["data"].startswith("^104")
    assert captured["data"] == "^104ABC"
    assert captured["options"]["parse"] is True


def test_B_1B_with_real_treepoem_produces_nonempty_image() -> None:
    pytest.importorskip("treepoem")
    source = b'N\nQ100,10\nq200\nB50,50,0,1B,1,2,35,N,"ABC"\nP1\n'
    img = render(source)
    # Some ink somewhere on the label.
    assert 0 in set(img.getdata())
