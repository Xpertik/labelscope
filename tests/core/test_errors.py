"""Tests for the typed exception hierarchy (Req P4)."""

from __future__ import annotations

import pytest

from labelscope.core.errors import (
    InvalidArgument,
    LabelscopeError,
    MalformedString,
    ParseError,
    UnknownCommand,
)


def test_labelscope_error_is_exception() -> None:
    assert issubclass(LabelscopeError, Exception)


def test_parse_error_hierarchy() -> None:
    assert issubclass(ParseError, LabelscopeError)
    assert issubclass(UnknownCommand, ParseError)
    assert issubclass(InvalidArgument, ParseError)
    assert issubclass(MalformedString, ParseError)


def test_parse_error_attributes() -> None:
    err = ParseError(line=3, col=7, msg="bad token")
    assert err.line == 3
    assert err.col == 7
    assert err.msg == "bad token"
    assert "3:7" in str(err)
    assert "bad token" in str(err)


def test_subclasses_inherit_fields() -> None:
    err = UnknownCommand(line=1, col=1, msg="ZZ is not supported")
    assert err.line == 1
    assert err.col == 1
    assert err.msg == "ZZ is not supported"
    assert isinstance(err, ParseError)


def test_parse_error_is_raisable() -> None:
    with pytest.raises(MalformedString) as exc_info:
        raise MalformedString(line=2, col=9, msg="unterminated quote")
    assert exc_info.value.line == 2
