"""Tests for unit conversion and quarter-turn rotation (Req RC3)."""

from __future__ import annotations

import pytest
from PIL import Image

from labelscope.core.geometry import Rect, dots_to_mm, mm_to_dots, rotate_quarter


def test_mm_to_dots_203dpi() -> None:
    # 55 mm at 203 DPI ≈ 439.57 → 440 dots.
    assert mm_to_dots(55.0, 203) == 440


def test_mm_to_dots_300dpi() -> None:
    # 55 mm at 300 DPI ≈ 649.6 → 650 dots.
    assert mm_to_dots(55.0, 300) == 650


@pytest.mark.parametrize("dpi", [203, 300])
@pytest.mark.parametrize("mm", [10.0, 25.4, 38.0, 55.0, 88.9])
def test_mm_dots_roundtrip_within_one_dot(mm: float, dpi: int) -> None:
    dots = mm_to_dots(mm, dpi)
    back_mm = dots_to_mm(dots, dpi)
    # Worst case: half-dot rounding. 1 dot = 25.4/dpi mm.
    assert abs(back_mm - mm) <= 25.4 / dpi


def test_rect_is_frozen() -> None:
    r = Rect(x=1, y=2, w=10, h=20)
    with pytest.raises((AttributeError, TypeError)):
        r.x = 99  # type: ignore[misc]


def _probe_image() -> Image.Image:
    img = Image.new("1", (3, 2), color=1)
    img.putpixel((0, 0), 0)
    img.putpixel((2, 1), 0)
    return img


@pytest.mark.parametrize("code", [0, 1, 2, 3])
def test_rotate_quarter_preserves_size_mod_swap(code: int) -> None:
    src = _probe_image()
    out = rotate_quarter(src, code)
    if code in (0, 2):
        assert out.size == src.size
    else:
        assert out.size == (src.size[1], src.size[0])


def test_rotate_quarter_zero_is_identity() -> None:
    src = _probe_image()
    out = rotate_quarter(src, 0)
    assert out is src


def test_rotate_quarter_180_is_involutive() -> None:
    src = _probe_image()
    twice = rotate_quarter(rotate_quarter(src, 2), 2)
    assert list(twice.getdata()) == list(src.getdata())


def test_rotate_quarter_360_loop() -> None:
    src = _probe_image()
    img = src
    for code in (1, 1, 1, 1):
        img = rotate_quarter(img, code)
    assert list(img.getdata()) == list(src.getdata())


def test_rotate_quarter_rejects_invalid_code() -> None:
    with pytest.raises(ValueError):
        rotate_quarter(_probe_image(), 4)
