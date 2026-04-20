"""Geometric primitives: dots/mm conversions and deterministic rotations.

Quarter-turn rotations always go through ``Image.transpose`` — never
``Image.rotate(angle)`` — so the result is an exact pixel permutation
with no resampling. This is load-bearing for byte-exact snapshots.
"""

from __future__ import annotations

from dataclasses import dataclass

from PIL import Image

# EPL2 ``p3`` rotation code (1/2/3 = 90/180/270 CW) → Pillow Transpose.
# Pillow's ``ROTATE_90`` is counter-clockwise, so EPL2 1 (90 CW) maps to
# ``ROTATE_270`` and EPL2 3 (270 CW) maps to ``ROTATE_90``. Code ``0`` is
# handled via an early-return in :func:`rotate_quarter` and omitted here.
_EPL2_TO_PIL_TRANSPOSE: dict[int, Image.Transpose] = {
    1: Image.Transpose.ROTATE_270,
    2: Image.Transpose.ROTATE_180,
    3: Image.Transpose.ROTATE_90,
}


@dataclass(frozen=True, slots=True)
class Rect:
    """Axis-aligned rectangle in integer dots.

    Attributes:
        x: Top-left X in dots.
        y: Top-left Y in dots.
        w: Width in dots.
        h: Height in dots.
    """

    x: int
    y: int
    w: int
    h: int


def mm_to_dots(mm: float, dpi: int) -> int:
    """Convert millimeters to printer dots at the given DPI.

    Args:
        mm: Length in millimeters.
        dpi: Print resolution in dots per inch.

    Returns:
        Rounded integer dot count.
    """
    return round(mm * dpi / 25.4)


def dots_to_mm(dots: int, dpi: int) -> float:
    """Convert printer dots to millimeters at the given DPI.

    Args:
        dots: Length in dots.
        dpi: Print resolution in dots per inch.

    Returns:
        Length in millimeters as a float.
    """
    return dots * 25.4 / dpi


def rotate_quarter(img: Image.Image, code: int) -> Image.Image:
    """Rotate an image by a quarter-turn using ``transpose``.

    Args:
        img: Source image.
        code: EPL2 rotation code (0/1/2/3 = 0/90/180/270 CW).

    Returns:
        A new image rotated by the requested quarter-turn. For ``code == 0``
        the original image is returned unchanged.

    Raises:
        ValueError: If ``code`` is not one of ``0``, ``1``, ``2``, ``3``.
    """
    if code == 0:
        return img
    if code not in _EPL2_TO_PIL_TRANSPOSE:
        raise ValueError(f"Invalid rotation code: {code!r}; expected 0|1|2|3")
    return img.transpose(_EPL2_TO_PIL_TRANSPOSE[code])
