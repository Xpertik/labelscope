"""Thin adapter over ``treepoem`` (BWIPP) for 1D/2D barcodes.

Code 128 is forced to subset B via BWIPP's ``^104`` sentinel in ``parse``
mode. QR defaults (Model 2 / ECC M / magnification 3) are set by the
caller; this module does not inject defaults.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from PIL import Image

from labelscope.core.errors import LabelscopeError

if TYPE_CHECKING:
    from PIL.Image import Image as PILImage


class BarcodeBackendMissing(LabelscopeError):
    """Raised when ``treepoem`` is not importable at render time."""


def _import_treepoem() -> Any:
    """Import ``treepoem`` lazily with an actionable error message.

    Returns:
        The imported ``treepoem`` module.

    Raises:
        BarcodeBackendMissing: If ``treepoem`` cannot be imported.
    """
    try:
        import treepoem  # type: ignore[import-untyped]
    except ImportError as exc:
        raise BarcodeBackendMissing(
            "treepoem is required for barcode rendering. "
            "Install with: pip install 'labelscope[barcodes]'"
        ) from exc
    return treepoem


def render_1d(
    symbology: str,
    data: str,
    scale: int,
    human_readable: bool,
) -> PILImage:
    """Render a 1D barcode via treepoem/BWIPP.

    Code 128 is force-switched to subset B by prefixing ``^104`` and
    enabling BWIPP's ``parse`` option.

    Args:
        symbology: BWIPP symbology name (e.g. ``"code128"``, ``"upca"``).
        data: Barcode payload.
        scale: Integer module-width scaling factor (pixel doubling).
        human_readable: When ``True``, draw the HRI text line.

    Returns:
        A ``PIL.Image`` in mode ``"1"`` holding the rendered symbol.
    """
    treepoem = _import_treepoem()
    options: dict[str, Any] = {"includetext": human_readable}
    payload = data
    if symbology == "code128":
        options["parse"] = True
        payload = f"^104{data}"
    raw: PILImage = treepoem.generate_barcode(
        barcode_type=symbology,
        data=payload,
        options=options,
    )
    img = raw.convert("1", dither=Image.Dither.NONE)
    if scale > 1:
        img = img.resize(
            (img.size[0] * scale, img.size[1] * scale),
            resample=Image.Resampling.NEAREST,
        )
    return img


def render_2d(
    symbology: str,
    data: str,
    model: int,
    ecc: str,
    magnification: int,
) -> PILImage:
    """Render a 2D barcode (QR) via treepoem/BWIPP.

    Args:
        symbology: BWIPP symbology name (e.g. ``"qrcode"``).
        data: Payload to encode.
        model: QR model number (1 or 2).
        ecc: Error-correction level (``"L"``/``"M"``/``"Q"``/``"H"``).
        magnification: Integer module-size multiplier applied post-render.

    Returns:
        A ``PIL.Image`` in mode ``"1"`` holding the rendered symbol.
    """
    treepoem = _import_treepoem()
    options: dict[str, Any] = {
        "version": model,
        "eclevel": ecc,
        "format": "full",
    }
    raw: PILImage = treepoem.generate_barcode(
        barcode_type=symbology,
        data=data,
        options=options,
    )
    img = raw.convert("1", dither=Image.Dither.NONE)
    if magnification > 1:
        img = img.resize(
            (img.size[0] * magnification, img.size[1] * magnification),
            resample=Image.Resampling.NEAREST,
        )
    return img
