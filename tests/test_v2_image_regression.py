"""V2 smoke: byte-exact PNG regression via ``file_regression``.

Our snapshot policy is byte-exact; ``pytest-regressions.image_regression``
computes Manhattan distance over pixel buffers (and requires numpy),
which is not what we want. We use ``file_regression`` with
``binary=True`` so the comparison is strictly byte-for-byte on the PNG
payload produced by ``Image.save(..., format="PNG", optimize=True,
compress_level=9)``.
"""

from __future__ import annotations

import io

import pytest
from PIL import Image
from pytest_regressions.file_regression import FileRegressionFixture


def _solid_black_png(size: tuple[int, int] = (10, 10)) -> bytes:
    img = Image.new("1", size, color=0)
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True, compress_level=9)
    return buf.getvalue()


def test_identical_images_pass(file_regression: FileRegressionFixture) -> None:
    file_regression.check(
        _solid_black_png(),
        binary=True,
        extension=".png",
        basename="v2_solid_black",
    )


def test_one_pixel_difference_fails(file_regression: FileRegressionFixture) -> None:
    img = Image.new("1", (10, 10), color=0)
    img.putpixel((0, 0), 1)
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True, compress_level=9)
    with pytest.raises(AssertionError):
        # Re-uses the baseline written by ``test_identical_images_pass``.
        file_regression.check(
            buf.getvalue(),
            binary=True,
            extension=".png",
            basename="v2_solid_black",
        )
