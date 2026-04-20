"""Error-path parser tests (Req P4).

The parser is always strict: unknown commands, bad integers, and
unterminated quoted strings must all raise typed errors with accurate
1-based ``line``/``col`` positions.
"""

from __future__ import annotations

import pytest

from labelscope.core.errors import (
    InvalidArgument,
    MalformedString,
    UnknownCommand,
)
from labelscope.epl2.parser import parse


def test_unknown_command_raises_with_position() -> None:
    """A letter not in the dispatch table raises ``UnknownCommand``."""
    src = "N\nXfoo\nP1\n"
    with pytest.raises(UnknownCommand) as exc_info:
        parse(src)
    err = exc_info.value
    assert err.line == 2
    assert err.col == 1
    assert "X" in err.msg


def test_unknown_command_preserves_column_after_indent() -> None:
    """``col`` must point at the identifier, not at column 1."""
    src = "N\n    @bad\nP1\n"
    with pytest.raises(UnknownCommand) as exc_info:
        parse(src)
    assert exc_info.value.line == 2
    assert exc_info.value.col == 5


def test_bad_integer_raises_invalid_argument() -> None:
    """Non-numeric values where an int is expected raise ``InvalidArgument``."""
    src = "N\nqABC\nP1\n"
    with pytest.raises(InvalidArgument) as exc_info:
        parse(src)
    err = exc_info.value
    assert err.line == 2
    assert err.col == 1


def test_bad_integer_in_A_command_raises_invalid_argument() -> None:
    """Malformed int inside an ``A`` command raises ``InvalidArgument``."""
    src = 'A0,0,0,X,1,1,N,"hi"\n'
    with pytest.raises(InvalidArgument):
        parse(src)


def test_unterminated_quoted_string_raises_malformed_string() -> None:
    """An unclosed ``"..."`` payload raises ``MalformedString``."""
    src = 'A0,0,0,2,1,1,N,"unclosed\n'
    with pytest.raises(MalformedString) as exc_info:
        parse(src)
    err = exc_info.value
    assert err.line == 1
    assert err.col == 1


def test_wrong_arity_raises_invalid_argument() -> None:
    """Too few arguments for ``A`` raises ``InvalidArgument``."""
    src = "A0,0,0\n"
    with pytest.raises(InvalidArgument):
        parse(src)


def test_Z_missing_suffix_raises_invalid_argument() -> None:
    """A bare ``Z`` with no ``T``/``B`` suffix is rejected."""
    with pytest.raises(InvalidArgument):
        parse("Z\n")


def test_Z_wrong_suffix_raises_invalid_argument() -> None:
    """``ZX`` (neither T nor B) is rejected with a typed error."""
    with pytest.raises(InvalidArgument):
        parse("ZX\n")


def test_A_bad_reverse_flag_raises_invalid_argument() -> None:
    """``A`` must receive ``N`` or ``R`` as the reverse-video flag."""
    src = 'A0,0,0,2,1,1,X,"hi"\n'
    with pytest.raises(InvalidArgument):
        parse(src)


def test_B_bad_hri_flag_raises_invalid_argument() -> None:
    """``B`` must receive ``N`` or ``B`` as the human-readable flag."""
    src = 'B0,0,0,1B,1,2,35,X,"hi"\n'
    with pytest.raises(InvalidArgument):
        parse(src)
