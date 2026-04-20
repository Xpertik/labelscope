"""Smoke test: every real EPL2 fixture parses without raising.

Parameterized over the 7 ClassicAlpaca fixtures in ``examples/``. This
test asserts only that parsing succeeds; command content is covered by
the targeted unit tests in this package.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from labelscope.epl2.commands import Command
from labelscope.epl2.parser import parse
from tests.conftest import EPL_FILES, read_fixture_bytes


@pytest.mark.parametrize("fixture_path", EPL_FILES, ids=lambda p: p.name)
def test_fixture_parses_without_error(fixture_path: Path) -> None:
    """Each MVP fixture must parse into a non-empty Command list."""
    data = read_fixture_bytes(fixture_path.name)
    cmds = parse(data)
    assert cmds, f"{fixture_path.name}: parser returned no commands"
    for cmd in cmds:
        assert isinstance(cmd, Command)
        assert cmd.line >= 1
        assert cmd.col >= 1


def test_all_seven_fixtures_are_discovered() -> None:
    """Guard rail: make sure the fixture glob still finds all 7 programs."""
    assert len(EPL_FILES) == 7
