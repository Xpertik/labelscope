"""Renderer smoke test over all 7 real EPL2 fixtures."""

from __future__ import annotations

import sys
import types
from pathlib import Path
from typing import Any

import pytest
from PIL import Image

from labelscope.epl2.renderer import render
from tests.conftest import EPL_FILES


@pytest.fixture(autouse=True)
def _fake_treepoem(monkeypatch: pytest.MonkeyPatch) -> None:
    """Stub treepoem so fixtures with QR/Code128 don't need a real backend."""

    def fake_generate_barcode(
        barcode_type: str,
        data: str,
        options: dict[str, Any],
        *,
        scale: int = 2,
    ) -> Image.Image:
        # Tiny all-ink stub; avoids any real BWIPP dependency.
        return Image.new("1", (8, 8), color=0)

    fake_mod = types.ModuleType("treepoem")
    fake_mod.generate_barcode = fake_generate_barcode  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "treepoem", fake_mod)


@pytest.mark.parametrize("path", EPL_FILES, ids=lambda p: Path(p).name)
def test_fixture_renders_without_error(path: Path) -> None:
    img = render(path.read_bytes())
    assert img.mode == "1"
    assert img.size[0] > 0
    assert img.size[1] > 0
