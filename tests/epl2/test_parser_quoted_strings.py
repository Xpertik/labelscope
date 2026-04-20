"""Quoted-string parser tests (Req P3, R6 empty string).

Covers the EPL2 quoted-argument rules: embedded commas are preserved,
``""`` escapes a literal ``"``, and an empty ``""`` yields an empty data
field without raising.
"""

from __future__ import annotations

from labelscope.epl2.commands import ACommand, BCommand
from labelscope.epl2.parser import parse


def test_comma_inside_quoted_string_is_preserved() -> None:
    """``A10,20,0,1,1,1,N,"Hello, World"`` parses as a single payload arg."""
    src = 'A10,20,0,1,1,1,N,"Hello, World"\n'
    a = parse(src)[0]
    assert isinstance(a, ACommand)
    assert a.data == "Hello, World"


def test_escaped_double_quote_inside_string() -> None:
    """``""`` inside a quoted payload resolves to a single literal ``"``."""
    src = 'A0,0,0,1,1,1,N,"She said ""hi"""\n'
    a = parse(src)[0]
    assert isinstance(a, ACommand)
    assert a.data == 'She said "hi"'


def test_empty_quoted_string_accepted() -> None:
    """An empty ``""`` payload must parse and yield ``data == ""``."""
    # Mirrors the real fixture `A260,30,1,3,1,1,N,""` from epl7-38x25.
    src = 'A260,30,1,3,1,1,N,""\n'
    a = parse(src)[0]
    assert isinstance(a, ACommand)
    assert a.data == ""


def test_multiple_commas_inside_quoted_string() -> None:
    """All embedded commas remain inside the payload, not split points."""
    src = 'A0,0,0,1,1,1,N,"a,b,c,d"\n'
    a = parse(src)[0]
    assert isinstance(a, ACommand)
    assert a.data == "a,b,c,d"


def test_barcode_payload_with_slash_and_special_chars() -> None:
    """``B`` payloads may contain ``/`` without escaping."""
    src = 'B180,130,0,1B,1,2,35,N,"W1A/1000260"\n'
    b = parse(src)[0]
    assert isinstance(b, BCommand)
    assert b.data == "W1A/1000260"
    assert b.symbology == "1B"
    assert b.human_readable is False
