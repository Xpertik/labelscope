"""Command-line interface: ``labelscope render|validate|info``.

The CLI is built on the stdlib :mod:`argparse`. Parse errors are reported
in GCC-style ``<file>:<line>:<col>: <severity>: <msg>`` lines so editors
and CI consumers can pick them up. Exit codes follow a fixed contract:
``0`` success, ``1`` usage error, ``2`` validation error, ``3`` IO error.
"""

from __future__ import annotations

import argparse
import sys
import warnings
from collections import Counter
from pathlib import Path
from typing import IO

from labelscope.core.errors import ParseError
from labelscope.epl2.commands import (
    Command,
    QCommand,
    ZCommand,
    qCommand,
)
from labelscope.epl2.parser import parse
from labelscope.epl2.renderer import Renderer

__all__ = ["main"]


# Exit codes (module constants, referenced by tests).
EXIT_OK = 0
EXIT_USAGE = 1
EXIT_VALIDATION = 2
EXIT_IO = 3


def main(argv: list[str] | None = None) -> int:
    """Dispatch ``labelscope`` subcommands and return a POSIX exit code.

    Args:
        argv: Argument list excluding ``argv[0]``; defaults to ``sys.argv[1:]``.

    Returns:
        Integer exit code (``0`` success, ``1`` usage, ``2`` validation, ``3`` IO).
    """
    parser = _build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        # argparse uses 2 for usage errors; remap to our usage slot.
        code = exc.code if isinstance(exc.code, int) else EXIT_USAGE
        return EXIT_USAGE if code != 0 else EXIT_OK
    handler = args.func
    return int(handler(args))


def _build_parser() -> argparse.ArgumentParser:
    """Construct the top-level parser wired with its three subcommands."""
    parser = argparse.ArgumentParser(
        prog="labelscope",
        description="Preview EPL2 thermal-printer labels from source code.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_render = sub.add_parser("render", help="Render an EPL2 source to PNG.")
    p_render.add_argument("file", type=Path, help="Path to the EPL2 source file.")
    p_render.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Output PNG path. Defaults to <file>.png next to the input.",
    )
    p_render.add_argument(
        "--dpi",
        type=int,
        default=203,
        help="Print-head resolution in DPI (default: 203).",
    )
    p_render.add_argument(
        "--show",
        action="store_true",
        help="Open the rendered image in the platform default viewer.",
    )
    p_render.set_defaults(func=_cmd_render)

    p_validate = sub.add_parser("validate", help="Parse an EPL2 source strictly.")
    p_validate.add_argument("file", type=Path, help="Path to the EPL2 source file.")
    p_validate.set_defaults(func=_cmd_validate)

    p_info = sub.add_parser("info", help="Print label metadata as YAML-ish key/value.")
    p_info.add_argument("file", type=Path, help="Path to the EPL2 source file.")
    p_info.set_defaults(func=_cmd_info)

    return parser


def _cmd_render(args: argparse.Namespace) -> int:
    """Run ``labelscope render``: parse permissively, rasterize, save PNG."""
    file_path: Path = args.file
    source = _read_source(file_path)
    if isinstance(source, int):
        return source  # IO error code
    try:
        _ast, cleaned = _parse_permissive(source, file_path)
    except ParseError as exc:
        _emit_diagnostic(file_path, exc, severity="error", stream=sys.stderr)
        return EXIT_VALIDATION
    renderer = Renderer(dpi=int(args.dpi))
    img = renderer.render(cleaned)
    output = (
        args.output if args.output is not None else file_path.with_suffix(file_path.suffix + ".png")
    )
    try:
        img.save(output, format="PNG", optimize=True, compress_level=9)
    except OSError as exc:
        sys.stderr.write(f"{file_path}: error: cannot write {output}: {exc}\n")
        return EXIT_IO
    if args.show:
        img.show()
    return EXIT_OK


def _cmd_validate(args: argparse.Namespace) -> int:
    """Run ``labelscope validate``: strict parse, GCC-style diagnostics."""
    file_path: Path = args.file
    source = _read_source(file_path)
    if isinstance(source, int):
        return source
    try:
        parse(source)
    except ParseError as exc:
        _emit_diagnostic(file_path, exc, severity="error", stream=sys.stderr)
        return EXIT_VALIDATION
    sys.stdout.write(f"{file_path}: OK\n")
    return EXIT_OK


def _cmd_info(args: argparse.Namespace) -> int:
    """Run ``labelscope info``: parse and dump label metadata to stdout."""
    file_path: Path = args.file
    source = _read_source(file_path)
    if isinstance(source, int):
        return source
    try:
        ast, _ = _parse_permissive(source, file_path)
    except ParseError as exc:
        _emit_diagnostic(file_path, exc, severity="error", stream=sys.stderr)
        return EXIT_VALIDATION
    width, height = _extract_dimensions(ast)
    orientation = _extract_orientation(ast)
    counts = _count_command_types(ast)
    out = sys.stdout
    out.write(f"file: {file_path}\n")
    out.write(f"width: {width}\n")
    out.write(f"height: {height}\n")
    out.write(f"orientation: {orientation}\n")
    out.write("commands:\n")
    for name, n in sorted(counts.items()):
        out.write(f"  {name}: {n}\n")
    return EXIT_OK


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _read_source(path: Path) -> bytes | int:
    """Read a source file as bytes or return an IO exit code on failure."""
    try:
        return path.read_bytes()
    except FileNotFoundError:
        sys.stderr.write(f"{path}: error: file not found\n")
        return EXIT_IO
    except OSError as exc:
        sys.stderr.write(f"{path}: error: {exc}\n")
        return EXIT_IO


def _parse_permissive(source: bytes, path: Path) -> tuple[list[Command], bytes]:
    """Parse ``source`` permissively, returning ``(ast, cleaned_source)``.

    Unknown command identifiers emit a GCC-style warning on stderr; their
    source lines are stripped before the authoritative parse. Other
    :class:`ParseError` subclasses propagate so malformed syntax still
    surfaces loudly. The cleaned bytes are returned so downstream callers
    (e.g. the renderer) can re-parse the same permissive view.
    """
    text = source.decode("cp437")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = text.split("\n")
    cleaned: list[str] = []
    for idx, raw in enumerate(lines):
        stripped = raw.lstrip()
        if stripped == "" or stripped.startswith(";"):
            cleaned.append(raw)
            continue
        ident = stripped[0]
        if ident not in _KNOWN_IDENTIFIERS:
            col = len(raw) - len(stripped) + 1
            sys.stderr.write(f"{path}:{idx + 1}:{col}: warning: unknown command {ident!r}\n")
            continue
        cleaned.append(raw)
    cleaned_text = "\n".join(cleaned)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        ast = parse(cleaned_text)
    return ast, cleaned_text.encode("cp437")


# Single-character identifiers the parser knows about. Must mirror the
# dispatcher in :mod:`labelscope.epl2.parser`.
_KNOWN_IDENTIFIERS: frozenset[str] = frozenset(
    {"N", "R", "q", "Q", "S", "D", "A", "B", "b", "P", "Z"}
)


def _emit_diagnostic(
    path: Path,
    err: ParseError,
    *,
    severity: str,
    stream: IO[str],
) -> None:
    """Write a GCC-style diagnostic line for the given parse error."""
    stream.write(f"{path}:{err.line}:{err.col}: {severity}: {err.msg}\n")


def _extract_dimensions(ast: list[Command]) -> tuple[int, int]:
    """Return ``(width, height)`` in dots, reading the last ``q`` and ``Q``."""
    width = 0
    height = 0
    for cmd in ast:
        if isinstance(cmd, qCommand):
            width = cmd.width
        elif isinstance(cmd, QCommand):
            height = cmd.height
    return width, height


def _extract_orientation(ast: list[Command]) -> str:
    """Return ``"ZT"`` (default) or ``"ZB"`` depending on the last Z command."""
    direction = "T"
    for cmd in ast:
        if isinstance(cmd, ZCommand):
            direction = cmd.direction
    return "ZB" if direction == "B" else "ZT"


def _count_command_types(ast: list[Command]) -> dict[str, int]:
    """Return a name→count map over the AST, keyed by command class name."""
    counter: Counter[str] = Counter(type(c).__name__ for c in ast)
    return dict(counter)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
