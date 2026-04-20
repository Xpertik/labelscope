"""1-bit raster canvas — the printer's bit buffer.

Mode ``"1"`` is the physically correct model for a thermal head: each
pixel is either ink (``0``) or paper (``1``). No anti-aliasing, no
resampling. All rotations happen via ``Image.transpose``.
"""

from __future__ import annotations

from PIL import Image, ImageChops, ImageDraw


class Canvas:
    """1-bit label canvas backed by a ``PIL.Image`` in mode ``"1"``.

    White (``1``) is paper; black (``0``) is ink.
    """

    def __init__(self, width: int, height: int) -> None:
        """Allocate a blank (all-white) 1-bit canvas.

        Args:
            width: Canvas width in dots.
            height: Canvas height in dots.
        """
        self._img: Image.Image = Image.new("1", (width, height), color=1)

    @property
    def width(self) -> int:
        """Canvas width in dots."""
        return self._img.size[0]

    @property
    def height(self) -> int:
        """Canvas height in dots."""
        return self._img.size[1]

    def draw_text_bitmap(self, raster: Image.Image, x: int, y: int) -> None:
        """Composite a pre-rendered 1-bit glyph raster onto the canvas.

        Args:
            raster: Source image in mode ``"1"``. Ink pixels are ``0``.
            x: Destination top-left X in canvas dots.
            y: Destination top-left Y in canvas dots.
        """
        if raster.mode != "1":
            raster = raster.convert("1", dither=Image.Dither.NONE)
        # Logical AND over mode "1" keeps ink wherever either source has ink.
        region = self._img.crop((x, y, x + raster.size[0], y + raster.size[1]))
        merged = ImageChops.logical_and(region, raster)
        self._img.paste(merged, (x, y))

    def draw_rect(self, x: int, y: int, w: int, h: int, fill: int) -> None:
        """Draw an axis-aligned filled rectangle.

        Args:
            x: Top-left X in dots.
            y: Top-left Y in dots.
            w: Width in dots.
            h: Height in dots.
            fill: ``0`` for ink, ``1`` for paper.
        """
        if w <= 0 or h <= 0:
            return
        ImageDraw.Draw(self._img).rectangle((x, y, x + w - 1, y + h - 1), fill=fill)

    def transpose_180(self) -> None:
        """Rotate the canvas 180 degrees in-place via ``transpose``."""
        self._img = self._img.transpose(Image.Transpose.ROTATE_180)

    def to_pil(self) -> Image.Image:
        """Return a copy of the underlying ``PIL.Image``.

        Returns:
            A fresh image so the caller cannot mutate internal state.
        """
        return self._img.copy()
