"""EPL2 bitmap font approximation via bundled DejaVu Sans Mono.

Fonts 1–5 are rendered into their manual-specified (W × H) cell. Glyph
shape comes from DejaVu; cell size is force-locked so the output geometry
matches the Zebra bit buffer.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from importlib.resources import as_file, files

from PIL import ImageFont

# Cell dimensions (W × H in dots) at 203 and 300 DPI for EPL2 fonts 1-5.
# Source: ``docs/epl2-reference.md`` §"Bitmap fonts (1–5)", which in turn
# derives from the Zebra EPL2 manual p. 44.
_CELL_TABLE: dict[tuple[int, int], tuple[int, int]] = {
    (1, 203): (8, 12),
    (2, 203): (10, 16),
    (3, 203): (12, 20),
    (4, 203): (14, 24),
    (5, 203): (32, 48),
    (1, 300): (12, 20),
    (2, 300): (16, 28),
    (3, 300): (20, 36),
    (4, 300): (24, 44),
    (5, 300): (48, 80),
}


@dataclass(frozen=True, slots=True)
class CellMetrics:
    """Final cell size for a font+multiplier combo.

    Attributes:
        width: Cell width in dots (after horizontal multiplier).
        height: Cell height in dots (after vertical multiplier).
    """

    width: int
    height: int


def _font_file_path() -> str:
    """Return the filesystem path of the bundled DejaVu Sans Mono TTF.

    Returns:
        Absolute path to the bundled TTF, extracted from package data.
    """
    resource = files("labelscope.core").joinpath("_fonts").joinpath("DejaVuSansMono.ttf")
    with as_file(resource) as path:
        return str(path)


class FontRegistry:
    """Registry that maps an EPL2 font+multiplier to a TrueType renderer.

    The registry caches ``ImageFont`` instances per point size so repeated
    ``get()`` calls are cheap. The cell table is static and hardcoded.
    """

    @staticmethod
    def cell_metrics(font_number: int, h_mult: int, v_mult: int, dpi: int = 203) -> CellMetrics:
        """Return the final cell size for a font+multiplier combo.

        Args:
            font_number: EPL2 font number (1-5).
            h_mult: Horizontal multiplier (integer pixel-doubling factor).
            v_mult: Vertical multiplier (integer pixel-doubling factor).
            dpi: Printer resolution, ``203`` (default) or ``300``.

        Returns:
            :class:`CellMetrics` with width and height after multipliers.

        Raises:
            ValueError: If ``font_number`` or ``dpi`` is unsupported.
        """
        key = (font_number, dpi)
        if key not in _CELL_TABLE:
            raise ValueError(f"Unsupported font/dpi combination: font={font_number}, dpi={dpi}")
        base_w, base_h = _CELL_TABLE[key]
        return CellMetrics(width=base_w * h_mult, height=base_h * v_mult)

    @staticmethod
    def get(font_number: int, h_mult: int, v_mult: int, dpi: int = 203) -> ImageFont.FreeTypeFont:
        """Return a cached ``ImageFont`` sized to approximate the EPL2 cell.

        Args:
            font_number: EPL2 font number (1-5).
            h_mult: Horizontal multiplier.
            v_mult: Vertical multiplier.
            dpi: Printer resolution.

        Returns:
            A loaded ``ImageFont.FreeTypeFont`` whose size targets the
            cell height for deterministic layout.
        """
        metrics = FontRegistry.cell_metrics(font_number, h_mult, v_mult, dpi)
        return _load_ttf(metrics.height)


@lru_cache(maxsize=64)
def _load_ttf(size_px: int) -> ImageFont.FreeTypeFont:
    """Load the bundled DejaVu TTF at the requested pixel size.

    Args:
        size_px: Target character height in pixels.

    Returns:
        A cached ``ImageFont.FreeTypeFont``.
    """
    return ImageFont.truetype(
        _font_file_path(),
        size=size_px,
        layout_engine=ImageFont.Layout.BASIC,
    )
