"""CP437 byte-decoding tests (Req P2, R1).

The parser MUST decode byte input as CP437 and MUST NOT attempt UTF-8.
Bytes that are not valid UTF-8 must not raise.
"""

from __future__ import annotations

from labelscope.epl2.commands import ACommand
from labelscope.epl2.parser import parse


def test_cp437_byte_0x96_decodes_without_error() -> None:
    """Byte ``0x96`` is not valid UTF-8 but is a valid CP437 codepoint."""
    # Build an `A` line whose data payload contains raw byte 0x96. In CP437
    # 0x96 maps to U+00FB "u with circumflex" — the exact mapping is not
    # important here; what matters is that decoding does not raise.
    src = b'A0,0,0,2,1,1,N,"x\x96y"\nP1\n'
    cmds = parse(src)
    a = cmds[0]
    assert isinstance(a, ACommand)
    # The payload round-trips through CP437; the 0x96 byte survives as
    # its mapped codepoint, not as a Unicode replacement character.
    assert len(a.data) == 3
    assert a.data[0] == "x"
    assert a.data[2] == "y"
    # CP437 0x96 → U+00FB
    assert a.data[1] == b"\x96".decode("cp437")


def test_utf8_en_dash_bytes_are_decoded_as_three_cp437_glyphs() -> None:
    """``0xE2 0x80 0x93`` (UTF-8 en-dash) must be 3 glyphs, not 1."""
    src = b'A0,0,0,2,1,1,N,"a\xe2\x80\x93b"\nP1\n'
    cmds = parse(src)
    a = cmds[0]
    assert isinstance(a, ACommand)
    # 1 + 3 + 1 = 5 CP437 codepoints, NOT 3 (which would mean UTF-8 was used).
    assert len(a.data) == 5
    assert a.data[0] == "a"
    assert a.data[-1] == "b"


def test_str_input_passes_through_unchanged() -> None:
    """``str`` inputs are consumed directly without re-decoding."""
    src = 'A0,0,0,2,1,1,N,"hello"\nP1\n'
    cmds = parse(src)
    a = cmds[0]
    assert isinstance(a, ACommand)
    assert a.data == "hello"


def test_full_range_of_high_bytes_decodes() -> None:
    """Every high-byte 0x80–0xFF has a CP437 mapping (no UnicodeDecodeError)."""
    payload = bytes(range(0x80, 0x100))
    src = b'A0,0,0,2,1,1,N,"' + payload + b'"\nP1\n'
    cmds = parse(src)
    a = cmds[0]
    assert isinstance(a, ACommand)
    assert len(a.data) == len(payload)
