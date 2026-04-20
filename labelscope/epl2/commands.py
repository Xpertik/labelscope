"""Dataclasses representing each EPL2 P1 command.

Each command stores its 1-based ``line``/``col`` source position so
parser/renderer diagnostics can point at the offending input token.
Synthetic (renderer-internal) commands may set both to ``0`` — no
real-world EPL2 source uses a zero-based origin.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

__all__ = [
    "ACommand",
    "BCommand",
    "Command",
    "DCommand",
    "NCommand",
    "PCommand",
    "QCommand",
    "RCommand",
    "SCommand",
    "ZCommand",
    "bCommand",
    "qCommand",
]


@dataclass(frozen=True, slots=True)
class Command:
    """Base class for every EPL2 command AST node.

    Attributes:
        line: 1-based source line where the command starts (``0`` if synthetic).
        col: 1-based column of the command identifier (``0`` if synthetic).
    """

    line: int
    col: int


@dataclass(frozen=True, slots=True)
class NCommand(Command):
    """``N`` — clear image buffer (manual p. 122). No parameters."""


@dataclass(frozen=True, slots=True)
class RCommand(Command):
    """``R x,y`` — set reference point global offset in dots (manual p. 143)."""

    x: int
    y: int


@dataclass(frozen=True, slots=True)
class qCommand(Command):
    """``q <width>`` — set label width in dots (manual p. 137)."""

    width: int


@dataclass(frozen=True, slots=True)
class QCommand(Command):
    """``Q <height>,<gap>`` — set form length and gap in dots (manual p. 139)."""

    height: int
    gap: int
    gap_mode: Literal["gap", "blackline"] = "gap"


@dataclass(frozen=True, slots=True)
class ZCommand(Command):
    """``ZT`` / ``ZB`` — print direction: top-first vs bottom-first (manual p. 170)."""

    direction: Literal["T", "B"]


@dataclass(frozen=True, slots=True)
class SCommand(Command):
    """``S <speed>`` — print speed 1..5 (visual no-op; manual p. 144)."""

    speed: int


@dataclass(frozen=True, slots=True)
class DCommand(Command):
    """``D <density>`` — head density 0..15 (visual no-op; manual p. 88)."""

    density: int


@dataclass(frozen=True, slots=True)
class ACommand(Command):
    """``A x,y,rot,font,hmult,vmult,N|R,"DATA"`` — ASCII text (manual p. 43)."""

    x: int
    y: int
    rotation: int
    font: int
    h_mult: int
    v_mult: int
    reverse: bool
    data: str


@dataclass(frozen=True, slots=True)
class BCommand(Command):
    """``B x,y,rot,sel,narrow,wide,height,N|B,"DATA"`` — 1D barcode (manual p. 52)."""

    x: int
    y: int
    rotation: int
    symbology: str
    narrow: int
    wide: int
    height: int
    human_readable: bool
    data: str


@dataclass(frozen=True, slots=True)
class bCommand(Command):
    """``b x,y,sel[,params],"DATA"`` — 2D barcode (QR/PDF417/...; manual p. 83)."""

    x: int
    y: int
    symbology: str
    params: str
    data: str


@dataclass(frozen=True, slots=True)
class PCommand(Command):
    """``P copies[,qty]`` — print copies; metadata only (manual p. 135)."""

    copies: int
    qty: int | None = None
