"""Shared pytest fixtures and path constants.

Fixtures live in the repository's ``examples/`` directory (not duplicated
under ``tests/``). This module exposes the canonical paths and small
helpers so tests can read fixtures by name.
"""

from __future__ import annotations

from pathlib import Path

FIXTURES_DIR: Path = Path(__file__).parent.parent / "examples"
"""Absolute path to the real EPL2 fixtures (``examples/epl*.txt``)."""

EPL_FILES: list[Path] = sorted(FIXTURES_DIR.glob("epl*.txt"))
"""All EPL2 source fixtures (``examples/epl[1-7]-*.txt``), sorted by name."""


def fixture_path(name: str) -> Path:
    """Return the absolute path to a fixture by file name.

    Args:
        name: File name inside ``examples/`` (e.g. ``"epl1-55x34.txt"``).

    Returns:
        Absolute :class:`pathlib.Path` to the fixture.

    Raises:
        FileNotFoundError: If the fixture does not exist.
    """
    path = FIXTURES_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"Fixture not found: {path}")
    return path


def read_fixture_bytes(name: str) -> bytes:
    """Read a fixture file as raw bytes.

    Args:
        name: File name inside ``examples/`` (e.g. ``"epl1-55x34.txt"``).

    Returns:
        The fixture's contents as ``bytes``.
    """
    return fixture_path(name).read_bytes()


def read_fixture_text(name: str, encoding: str = "cp437") -> str:
    """Read a fixture file decoded as text (CP437 by default).

    Args:
        name: File name inside ``examples/``.
        encoding: Text encoding; defaults to CP437 per EPL2 convention.

    Returns:
        The fixture's contents as a string.
    """
    return fixture_path(name).read_text(encoding=encoding)
