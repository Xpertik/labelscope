"""Line-based EPL2 tokenizer and parser.

Produces an ordered list of :class:`Command` dataclasses from an EPL2
source (``bytes`` or ``str``). Always strict: the CLI layer wraps this
parser with a warn-and-skip policy when the user opts into permissive
mode.
"""

from __future__ import annotations

from typing import Literal, cast

from labelscope.core.errors import (
    InvalidArgument,
    MalformedString,
    UnknownCommand,
)
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

__all__ = ["parse"]


def parse(source: bytes | str) -> list[Command]:
    """Parse an EPL2 source into an ordered list of command AST nodes.

    Bytes are decoded as CP437 (per EPL2 default codepage); never as
    UTF-8. ``LF``, ``CRLF`` and bare ``CR`` are all normalized to ``LF``
    before line splitting. Blank lines and ``;``-prefixed comments are
    ignored.

    Args:
        source: Raw EPL2 program as bytes or a CP437-compatible string.

    Returns:
        Ordered list of parsed :class:`Command` instances.

    Raises:
        UnknownCommand: The line starts with an unsupported command.
        InvalidArgument: A required integer argument is malformed.
        MalformedString: A quoted string argument is unterminated.
    """
    text = _decode(source)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = text.split("\n")

    commands: list[Command] = []
    for idx, raw in enumerate(lines):
        line_no = idx + 1
        stripped = raw.lstrip()
        if stripped == "" or stripped.startswith(";"):
            continue
        col = len(raw) - len(stripped) + 1
        commands.append(_parse_line(stripped, line_no, col))
    return commands


def _decode(source: bytes | str) -> str:
    """Decode raw bytes as CP437; leave strings as-is.

    CP437 maps every byte 0x00–0xFF to a codepoint without error, so no
    fallback path is needed for byte input.
    """
    if isinstance(source, bytes):
        return source.decode("cp437")
    return source


def _parse_line(line: str, line_no: int, col: int) -> Command:
    """Dispatch one stripped, non-comment line to its command parser."""
    ch = line[0]
    # Two-letter commands first (ZT/ZB) so we don't swallow Z alone.
    if ch == "Z":
        return _parse_Z(line, line_no, col)
    match ch:
        case "N":
            return _parse_N(line, line_no, col)
        case "R":
            return _parse_R(line, line_no, col)
        case "q":
            return _parse_q(line, line_no, col)
        case "Q":
            return _parse_Q(line, line_no, col)
        case "S":
            return _parse_S(line, line_no, col)
        case "D":
            return _parse_D(line, line_no, col)
        case "A":
            return _parse_A(line, line_no, col)
        case "B":
            return _parse_B(line, line_no, col)
        case "b":
            return _parse_b(line, line_no, col)
        case "P":
            return _parse_P(line, line_no, col)
        case _:
            raise UnknownCommand(line_no, col, f"Unknown command '{ch}'")


# ---------------------------------------------------------------------------
# Individual command parsers
# ---------------------------------------------------------------------------


def _parse_N(line: str, line_no: int, col: int) -> NCommand:
    """Parse ``N`` (clear image buffer; no arguments)."""
    _ = line  # N has no args; trailing whitespace ignored
    return NCommand(line=line_no, col=col)


def _parse_R(line: str, line_no: int, col: int) -> RCommand:
    """Parse ``R x,y``."""
    args = _split_args(line[1:], line_no, col)
    _expect_arity(args, 2, "R", line_no, col)
    x = _as_int(args[0], "R.x", line_no, col)
    y = _as_int(args[1], "R.y", line_no, col)
    return RCommand(line=line_no, col=col, x=x, y=y)


def _parse_q(line: str, line_no: int, col: int) -> qCommand:
    """Parse ``q <width>``."""
    args = _split_args(line[1:], line_no, col)
    _expect_arity(args, 1, "q", line_no, col)
    width = _as_int(args[0], "q.width", line_no, col)
    return qCommand(line=line_no, col=col, width=width)


def _parse_Q(line: str, line_no: int, col: int) -> QCommand:
    """Parse ``Q <height>,<gap>`` (ignoring optional ``p3`` offset)."""
    args = _split_args(line[1:], line_no, col)
    if len(args) < 2:
        raise InvalidArgument(line_no, col, f"Q requires 2 arguments, got {len(args)}")
    height = _as_int(args[0], "Q.height", line_no, col)
    gap = _as_int(args[1], "Q.gap", line_no, col)
    return QCommand(line=line_no, col=col, height=height, gap=gap)


def _parse_Z(line: str, line_no: int, col: int) -> ZCommand:
    """Parse ``ZT`` or ``ZB``."""
    if len(line) < 2:
        raise InvalidArgument(line_no, col, "Z command requires 'T' or 'B' suffix")
    suffix = line[1]
    if suffix not in ("T", "B"):
        raise InvalidArgument(line_no, col, f"Z suffix must be 'T' or 'B', got '{suffix}'")
    return ZCommand(line=line_no, col=col, direction=cast(Literal["T", "B"], suffix))


def _parse_S(line: str, line_no: int, col: int) -> SCommand:
    """Parse ``S <speed>``."""
    args = _split_args(line[1:], line_no, col)
    _expect_arity(args, 1, "S", line_no, col)
    speed = _as_int(args[0], "S.speed", line_no, col)
    return SCommand(line=line_no, col=col, speed=speed)


def _parse_D(line: str, line_no: int, col: int) -> DCommand:
    """Parse ``D <density>``."""
    args = _split_args(line[1:], line_no, col)
    _expect_arity(args, 1, "D", line_no, col)
    density = _as_int(args[0], "D.density", line_no, col)
    return DCommand(line=line_no, col=col, density=density)


def _parse_A(line: str, line_no: int, col: int) -> ACommand:
    """Parse ``A x,y,rot,font,hmult,vmult,N|R,"DATA"``."""
    args = _split_args(line[1:], line_no, col)
    if len(args) != 8:
        raise InvalidArgument(line_no, col, f"A requires 8 arguments, got {len(args)}")
    x = _as_int(args[0], "A.x", line_no, col)
    y = _as_int(args[1], "A.y", line_no, col)
    rotation = _as_int(args[2], "A.rotation", line_no, col)
    font = _as_int(args[3], "A.font", line_no, col)
    h_mult = _as_int(args[4], "A.h_mult", line_no, col)
    v_mult = _as_int(args[5], "A.v_mult", line_no, col)
    reverse = _as_reverse_flag(args[6], line_no, col)
    data = _as_quoted(args[7], line_no, col)
    return ACommand(
        line=line_no,
        col=col,
        x=x,
        y=y,
        rotation=rotation,
        font=font,
        h_mult=h_mult,
        v_mult=v_mult,
        reverse=reverse,
        data=data,
    )


def _parse_B(line: str, line_no: int, col: int) -> BCommand:
    """Parse ``B x,y,rot,sel,narrow,wide,height,N|B,"DATA"``."""
    args = _split_args(line[1:], line_no, col)
    if len(args) != 9:
        raise InvalidArgument(line_no, col, f"B requires 9 arguments, got {len(args)}")
    x = _as_int(args[0], "B.x", line_no, col)
    y = _as_int(args[1], "B.y", line_no, col)
    rotation = _as_int(args[2], "B.rotation", line_no, col)
    symbology = args[3]
    narrow = _as_int(args[4], "B.narrow", line_no, col)
    wide = _as_int(args[5], "B.wide", line_no, col)
    height = _as_int(args[6], "B.height", line_no, col)
    human_readable = _as_hri_flag(args[7], line_no, col)
    data = _as_quoted(args[8], line_no, col)
    return BCommand(
        line=line_no,
        col=col,
        x=x,
        y=y,
        rotation=rotation,
        symbology=symbology,
        narrow=narrow,
        wide=wide,
        height=height,
        human_readable=human_readable,
        data=data,
    )


def _parse_b(line: str, line_no: int, col: int) -> bCommand:
    """Parse ``b x,y,sel[,params],"DATA"`` (2D barcodes)."""
    args = _split_args(line[1:], line_no, col)
    if len(args) < 4:
        raise InvalidArgument(line_no, col, f"b requires at least 4 arguments, got {len(args)}")
    x = _as_int(args[0], "b.x", line_no, col)
    y = _as_int(args[1], "b.y", line_no, col)
    symbology = args[2]
    # The last arg MUST be the quoted payload; everything between the
    # symbology and the payload is the per-symbology param block.
    data = _as_quoted(args[-1], line_no, col)
    params = ",".join(args[3:-1])
    return bCommand(
        line=line_no,
        col=col,
        x=x,
        y=y,
        symbology=symbology,
        params=params,
        data=data,
    )


def _parse_P(line: str, line_no: int, col: int) -> PCommand:
    """Parse ``P copies[,qty]``."""
    args = _split_args(line[1:], line_no, col)
    if len(args) < 1 or len(args) > 2:
        raise InvalidArgument(line_no, col, f"P requires 1 or 2 arguments, got {len(args)}")
    copies = _as_int(args[0], "P.copies", line_no, col)
    qty = _as_int(args[1], "P.qty", line_no, col) if len(args) == 2 else None
    return PCommand(line=line_no, col=col, copies=copies, qty=qty)


# ---------------------------------------------------------------------------
# Argument utilities
# ---------------------------------------------------------------------------


def _split_args(tail: str, line_no: int, col: int) -> list[str]:
    """Split a command argument tail on commas, respecting quoted strings.

    Handles the EPL2 manual's ``""`` escape (a doubled quote inside a
    quoted payload represents a literal ``"``). Embedded commas within a
    quoted payload are preserved. Raises :class:`MalformedString` on an
    unterminated quote.
    """
    args: list[str] = []
    buf: list[str] = []
    i = 0
    n = len(tail)
    in_quote = False
    while i < n:
        ch = tail[i]
        if in_quote:
            if ch == '"':
                # Escaped quote: doubled `""` inside a quoted payload.
                if i + 1 < n and tail[i + 1] == '"':
                    buf.append('"')
                    i += 2
                    continue
                buf.append(ch)
                in_quote = False
                i += 1
                continue
            buf.append(ch)
            i += 1
            continue
        if ch == '"':
            buf.append(ch)
            in_quote = True
            i += 1
            continue
        if ch == ",":
            args.append("".join(buf).strip())
            buf = []
            i += 1
            continue
        buf.append(ch)
        i += 1

    if in_quote:
        raise MalformedString(line_no, col, "Unterminated quoted string")

    args.append("".join(buf).strip())
    # If the tail was empty (e.g. a bare `N` command with no args) the
    # split yields `[""]`; treat that as "no args".
    if len(args) == 1 and args[0] == "":
        return []
    return args


def _expect_arity(args: list[str], expected: int, name: str, line_no: int, col: int) -> None:
    """Raise :class:`InvalidArgument` when arity mismatches the contract."""
    if len(args) != expected:
        raise InvalidArgument(
            line_no,
            col,
            f"{name} requires {expected} argument(s), got {len(args)}",
        )


def _as_int(raw: str, name: str, line_no: int, col: int) -> int:
    """Parse ``raw`` as a decimal integer or raise :class:`InvalidArgument`."""
    try:
        return int(raw)
    except ValueError as exc:
        raise InvalidArgument(line_no, col, f"{name} expected integer, got {raw!r}") from exc


def _as_quoted(raw: str, line_no: int, col: int) -> str:
    """Unwrap a ``"..."`` payload, unescaping doubled quotes.

    The tokenizer keeps the outer quotes; this strips them and restores
    any ``""`` escapes that were already collapsed during splitting.
    """
    if len(raw) < 2 or raw[0] != '"' or raw[-1] != '"':
        raise MalformedString(line_no, col, f"Expected quoted string, got {raw!r}")
    return raw[1:-1]


def _as_reverse_flag(raw: str, line_no: int, col: int) -> bool:
    """Map ``A``'s ``p7`` flag (``N``/``R``) to a ``bool`` reverse-video."""
    if raw == "N":
        return False
    if raw == "R":
        return True
    raise InvalidArgument(line_no, col, f"A.reverse must be 'N' or 'R', got {raw!r}")


def _as_hri_flag(raw: str, line_no: int, col: int) -> bool:
    """Map ``B``'s ``p8`` flag (``N``/``B``) to a ``bool`` HRI-line flag."""
    if raw == "N":
        return False
    if raw == "B":
        return True
    raise InvalidArgument(line_no, col, f"B.human_readable must be 'N' or 'B', got {raw!r}")
