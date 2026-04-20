"""V1 smoke: real treepoem call forces Code 128 subset B via ``^104`` prefix."""

from __future__ import annotations

import pytest
from PIL import Image

treepoem = pytest.importorskip("treepoem")


def test_treepoem_accepts_start_b_sentinel() -> None:
    img = treepoem.generate_barcode(
        barcode_type="code128",
        data="^104ABC123",
        options={"parse": True},
    )
    assert isinstance(img, Image.Image)
    assert img.size[0] > 0
    assert img.size[1] > 0
