"""V2 smoke: ``pytest-regressions`` ``image_regression`` is byte-exact by default."""

from __future__ import annotations

from typing import Any

import pytest
from PIL import Image

pytest.importorskip("pytest_regressions")


def _solid_black(size: tuple[int, int] = (10, 10)) -> Image.Image:
    return Image.new("1", size, color=0)


def test_identical_images_pass(image_regression: Any) -> None:
    img = _solid_black()
    image_regression.check(img.tobytes())


def test_one_pixel_difference_fails(image_regression: Any) -> None:
    img = _solid_black()
    img.putpixel((0, 0), 1)
    with pytest.raises(AssertionError):
        # Re-uses the baseline saved by ``test_identical_images_pass``.
        image_regression.check(img.tobytes(), basename="test_identical_images_pass")
