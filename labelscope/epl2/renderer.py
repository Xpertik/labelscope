"""Executes an EPL2 AST against a core Canvas to produce a PIL.Image.

The renderer follows a two-pass pipeline: a configuration pass that
consumes setup commands (``R``, ``q``, ``Q``, ``Z``, ``S``, ``D``) to
build the render state, then a draw pass that dispatches each remaining
command to its raster handler. The ``ZB`` orientation is composed as a
single final 180-degree transpose per design §4 step 5.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw

from labelscope.core.barcodes import render_1d, render_2d
from labelscope.core.canvas import Canvas
from labelscope.core.fonts import FontRegistry
from labelscope.core.geometry import rotate_quarter
from labelscope.epl2.commands import (
    ACommand,
    BCommand,
    Command,
    DCommand,
    NCommand,
    PCommand,
    QCommand,
    RCommand,
    SCommand,
    ZCommand,
    bCommand,
    qCommand,
)
from labelscope.epl2.parser import parse

__all__ = ["Renderer", "render"]

# BWIPP symbology names keyed by EPL2 ``B`` selector. See
# ``docs/epl2-reference.md`` "Barcode symbology map".
_B_SYMBOLOGY_MAP: dict[str, str] = {
    "1B": "code128",
    "1": "code128",
    "UA0": "upca",
    "E30": "ean13",
    "E80": "ean8",
    "3": "code39",
    "9": "code93",
}

# BWIPP symbology names keyed by EPL2 ``b`` (2D) selector.
_b_SYMBOLOGY_MAP: dict[str, str] = {
    "Q": "qrcode",
}

# Full Zebra ZD410 (4") print-head width at 203 DPI. Used when an ``R``
# command arrives AFTER ``q`` and overrides the label width per manual
# p. 143 (decision D).
_DEFAULT_FULL_WIDTH: int = 832


@dataclass(slots=True)
class _RenderContext:
    """Mutable renderer configuration collected by the config pass."""

    width: int = 0
    height: int = 0
    ref_x: int = 0
    ref_y: int = 0
    orientation: str = "T"
    speed: int | None = None
    density: int | None = None
    copies: int | None = None
    q_seen: bool = False
    r_after_q: bool = False
    dpi: int = 203
    draw_commands: list[Command] = field(default_factory=list)


class Renderer:
    """EPL2 AST-to-image renderer.

    Attributes:
        dpi: Print-head resolution in dots per inch (default 203).
    """

    def __init__(self, dpi: int = 203) -> None:
        """Create a renderer targeted at the given print resolution.

        Args:
            dpi: Print-head resolution; ``203`` (default) or ``300``.
        """
        self.dpi: int = dpi

    def render(self, source: bytes | str) -> Image.Image:
        """Parse EPL2 source and return the rendered PIL image.

        Args:
            source: Raw EPL2 program as bytes or a CP437-compatible string.

        Returns:
            A ``PIL.Image.Image`` in mode ``"1"`` holding the label bitmap.
        """
        ast = parse(source)
        ctx = self._build_context(ast)
        canvas = Canvas(width=max(ctx.width, 1), height=max(ctx.height, 1))
        for cmd in ctx.draw_commands:
            self._draw(cmd, canvas, ctx)
        if ctx.orientation == "B":
            canvas.transpose_180()
        return canvas.to_pil()

    def render_file(self, path: str | Path) -> Image.Image:
        """Read an EPL2 file from disk and render it.

        Args:
            path: Filesystem path to the EPL2 source file.

        Returns:
            A ``PIL.Image.Image`` in mode ``"1"`` holding the label bitmap.
        """
        return self.render(Path(path).read_bytes())

    # ------------------------------------------------------------------
    # Passes
    # ------------------------------------------------------------------

    def _build_context(self, ast: list[Command]) -> _RenderContext:
        """Run the configuration pass over the AST.

        Args:
            ast: Full parsed command list.

        Returns:
            A populated :class:`_RenderContext` plus the residual draw list.
        """
        ctx = _RenderContext(dpi=self.dpi)
        for cmd in ast:
            match cmd:
                case qCommand(width=w):
                    ctx.width = w
                    ctx.q_seen = True
                case QCommand(height=h):
                    ctx.height = h
                case RCommand(x=x, y=y):
                    ctx.ref_x = x
                    ctx.ref_y = y
                    if ctx.q_seen:
                        # Decision D: R after q resets canvas to full head width.
                        ctx.r_after_q = True
                        ctx.width = _DEFAULT_FULL_WIDTH
                case ZCommand(direction=d):
                    ctx.orientation = d
                case SCommand(speed=s):
                    ctx.speed = s
                case DCommand(density=d):
                    ctx.density = d
                case NCommand():
                    # "Clear image buffer" — the canvas is allocated fresh
                    # from the collected ctx, so N is a logical no-op here.
                    pass
                case PCommand(copies=c):
                    ctx.copies = c
                case _:
                    ctx.draw_commands.append(cmd)
        return ctx

    def _draw(self, cmd: Command, canvas: Canvas, ctx: _RenderContext) -> None:
        """Dispatch a single draw command to its rasterizer."""
        match cmd:
            case ACommand():
                self._draw_a(cmd, canvas, ctx)
            case BCommand():
                self._draw_b(cmd, canvas, ctx)
            case bCommand():
                self._draw_b2d(cmd, canvas, ctx)
            case _:
                # Unknown / deferred command — silently ignored at render
                # time. Parser already surfaces unsupported syntax.
                return

    # ------------------------------------------------------------------
    # Draw handlers
    # ------------------------------------------------------------------

    def _draw_a(self, cmd: ACommand, canvas: Canvas, ctx: _RenderContext) -> None:
        """Render an ``A`` text command onto the canvas."""
        if cmd.data == "":
            # Empty payload: no rectangle, no glyphs (Req RT4 empty+R,
            # Req P3 empty tolerance).
            return
        raster = self._build_text_raster(cmd)
        rotated = rotate_quarter(raster, cmd.rotation)
        canvas.draw_text_bitmap(rotated, x=cmd.x + ctx.ref_x, y=cmd.y + ctx.ref_y)

    def _build_text_raster(self, cmd: ACommand) -> Image.Image:
        """Build the logical (pre-rotation) text raster for an ``A`` command.

        Args:
            cmd: Parsed ``A`` command.

        Returns:
            A mode-``"1"`` image sized ``(cell_w * len(text), cell_h)``.
        """
        metrics = FontRegistry.cell_metrics(cmd.font, cmd.h_mult, cmd.v_mult, dpi=self.dpi)
        font = FontRegistry.get(cmd.font, cmd.h_mult, cmd.v_mult, dpi=self.dpi)
        # Font 5 is documented UPPERCASE ONLY by the manual (p. 45).
        text = cmd.data.upper() if cmd.font == 5 else cmd.data
        total_w = metrics.width * len(text)
        total_h = metrics.height
        # Mode "1" raster: ink=0, paper=1. Start fully paper (white).
        raster = Image.new("1", (total_w, total_h), color=1)
        draw = ImageDraw.Draw(raster)
        for i, ch in enumerate(text):
            cell_x = i * metrics.width
            # Top-left anchor (decision E).
            draw.text((cell_x, 0), ch, fill=0, font=font)
        if cmd.reverse:
            # Reverse-video: solid black rectangle with white glyph holes.
            # Pillow's ``logical_xor`` operates on the boolean polarity of
            # mode "1" pixels (paper=1, ink=0). XORing the text raster
            # against an all-paper mask flips every pixel, so paper→ink
            # (rectangle background) and ink→paper (glyph holes). The
            # rectangle and glyphs live in one raster and rotate as a
            # single unit (R7).
            solid = Image.new("1", raster.size, color=1)
            raster = ImageChops.logical_xor(raster, solid)
        return raster

    def _draw_b(self, cmd: BCommand, canvas: Canvas, ctx: _RenderContext) -> None:
        """Render a ``B`` 1D barcode command onto the canvas."""
        if cmd.data == "":
            return
        symbology = _B_SYMBOLOGY_MAP.get(cmd.symbology, "code128")
        scale = max(cmd.narrow, 1)
        img = render_1d(
            symbology=symbology,
            data=cmd.data,
            scale=scale,
            human_readable=cmd.human_readable,
        )
        rotated = rotate_quarter(img, cmd.rotation)
        canvas.draw_text_bitmap(rotated, x=cmd.x + ctx.ref_x, y=cmd.y + ctx.ref_y)

    def _draw_b2d(self, cmd: bCommand, canvas: Canvas, ctx: _RenderContext) -> None:
        """Render a ``b`` 2D barcode (QR) command onto the canvas."""
        if cmd.data == "":
            return
        symbology = _b_SYMBOLOGY_MAP.get(cmd.symbology, "qrcode")
        model, magnification, ecc, _input_mode = _parse_qr_params(cmd.params)
        img = render_2d(
            symbology=symbology,
            data=cmd.data,
            model=model,
            ecc=ecc,
            magnification=magnification,
        )
        canvas.draw_text_bitmap(img, x=cmd.x + ctx.ref_x, y=cmd.y + ctx.ref_y)


def render(source: bytes | str, *, dpi: int = 203) -> Image.Image:
    """Convenience wrapper around :class:`Renderer` for one-shot rendering.

    Args:
        source: Raw EPL2 program as bytes or string.
        dpi: Print-head resolution (default 203).

    Returns:
        A rendered ``PIL.Image.Image`` in mode ``"1"``.
    """
    return Renderer(dpi=dpi).render(source)


def _parse_qr_params(params: str) -> tuple[int, int, str, str]:
    """Parse the QR ``b`` params string into ``(model, mag, ecc, input)``.

    Defaults per Req RQR1: Model 2, magnification 3, ECC ``M``, input ``A``.

    Args:
        params: Raw comma-joined params from ``bCommand.params``.

    Returns:
        Tuple ``(model, magnification, ecc, input_mode)``.
    """
    model = 2
    magnification = 3
    ecc = "M"
    input_mode = "A"
    if not params:
        return model, magnification, ecc, input_mode
    for tok in params.split(","):
        tok = tok.strip()
        if not tok:
            continue
        prefix, rest = tok[0], tok[1:]
        match prefix:
            case "m":
                model = int(rest)
            case "s":
                magnification = int(rest)
            case "e":
                ecc = rest
            case "i":
                input_mode = rest
            case _:
                # Unknown QR sub-param — silently ignored; the manual
                # allows additional prefixes (e.g. ``D``) that the MVP
                # does not implement.
                continue
    return model, magnification, ecc, input_mode
