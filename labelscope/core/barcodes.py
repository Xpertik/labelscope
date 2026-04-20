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
        import treepoem
    except ImportError as exc:
        raise BarcodeBackendMissing(
            "treepoem is required for barcode rendering. "
            "Install with: pip install 'labelscope[barcodes]'"
        ) from exc
    return treepoem


def render_1d(
    symbology: str,
    data: str,
    narrow: int,
    height: int,
    human_readable: bool,
) -> PILImage:
    """Render a 1D barcode via treepoem/BWIPP.

    Code 128 is force-switched to subset B by prefixing ``^104`` and
    enabling BWIPP's ``parse`` option. The output is scaled so each narrow
    module is ``narrow`` dots wide (horizontal) and the overall barcode
    is exactly ``height`` dots tall (vertical). When ``human_readable`` is
    ``True`` the HRI text is included in the ``height`` budget — callers
    wanting unsquashed HRI should keep the text as a separate ``A``
    command and pass ``human_readable=False``.

    Args:
        symbology: BWIPP symbology name (e.g. ``"code128"``, ``"upca"``).
        data: Barcode payload.
        narrow: Narrow module width in dots (EPL2 ``B`` param 5).
        height: Target total image height in dots (EPL2 ``B`` param 7).
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
    # scale=1 gives 1 pixel per BWIPP module so our `narrow`/`height`
    # math is absolute (not compounded over treepoem's default scale=2).
    raw: PILImage = treepoem.generate_barcode(
        barcode_type=symbology,
        data=payload,
        options=options,
        scale=1,
    )
    img = raw.convert("1", dither=Image.Dither.NONE)
    new_w = img.size[0] * max(narrow, 1)
    new_h = max(height, 1)
    if (new_w, new_h) != img.size:
        img = img.resize((new_w, new_h), resample=Image.Resampling.NEAREST)
    return img


def render_2d(
    symbology: str,
    data: str,
    model: int,
    ecc: str,
    magnification: float,
) -> PILImage:
    """Render a 2D barcode (QR) via treepoem/BWIPP.

    ``model`` selects the QR specification: Model 2 (default, modern) uses
    BWIPP's ``qrcode`` symbology with no ``version`` option so BWIPP can
    auto-select the minimum symbol version (1-40) that fits the payload.
    Model 1 uses the legacy symbology ``qrcode1``.

    Args:
        symbology: BWIPP symbology name (e.g. ``"qrcode"``).
        data: Payload to encode.
        model: QR model number (1 or 2).
        ecc: Error-correction level (``"L"``/``"M"``/``"Q"``/``"H"``).
        magnification: Module-size multiplier applied post-render. Float
            values are supported so callers can apply a printer-specific
            calibration factor (the final pixel dims are rounded).

    Returns:
        A ``PIL.Image`` in mode ``"1"`` holding the rendered symbol.
    """
    treepoem = _import_treepoem()
    effective_symbology = "qrcode1" if model == 1 and symbology == "qrcode" else symbology
    options: dict[str, Any] = {"eclevel": ecc}
    # scale=1 gives 1 pixel per BWIPP module so `magnification` is absolute
    # module-size-in-dots (not compounded over treepoem's default scale=2).
    raw: PILImage = treepoem.generate_barcode(
        barcode_type=effective_symbology,
        data=data,
        options=options,
        scale=1,
    )
    img = raw.convert("1", dither=Image.Dither.NONE)
    new_w = max(1, int(round(img.size[0] * magnification)))
    new_h = max(1, int(round(img.size[1] * magnification)))
    if (new_w, new_h) != img.size:
        img = img.resize((new_w, new_h), resample=Image.Resampling.NEAREST)
    return img
