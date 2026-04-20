"""Tokenizer-level parser tests (line splitting, line endings, comments).

Covers Req P1: the parser must split EPL2 programs into one Command per
non-empty, non-comment line and accept both ``LF`` and ``CRLF`` endings.
"""

from __future__ import annotations

from labelscope.epl2.commands import NCommand, PCommand, QCommand, qCommand
from labelscope.epl2.parser import parse


def test_lf_line_splitting() -> None:
    """Happy path: LF-separated lines yield one command each."""
    src = "N\nq430\nQ270,24\nP1\n"
    cmds = parse(src)
    assert [type(c) for c in cmds] == [NCommand, qCommand, QCommand, PCommand]


def test_crlf_line_splitting_matches_lf() -> None:
    """CRLF line endings must produce the same AST as LF."""
    lf = parse("N\nq430\nP1\n")
    crlf = parse("N\r\nq430\r\nP1\r\n")
    assert lf == crlf


def test_bare_cr_line_splitting_matches_lf() -> None:
    """Classic Mac-style bare CR endings are also normalized."""
    lf = parse("N\nq430\nP1\n")
    cr = parse("N\rq430\rP1\r")
    assert lf == cr


def test_blank_lines_are_skipped() -> None:
    """Empty and whitespace-only lines must not produce a Command."""
    cmds = parse("\nN\n\n\n  \nP1\n")
    assert [type(c) for c in cmds] == [NCommand, PCommand]


def test_comment_lines_are_skipped() -> None:
    """Lines starting with ``;`` are comments and never emit a Command."""
    src = "; header comment\nN\n;mid comment\nP1\n"
    cmds = parse(src)
    assert [type(c) for c in cmds] == [NCommand, PCommand]


def test_indented_comment_is_skipped() -> None:
    """A comment preceded by whitespace is still a comment (lstripped check)."""
    src = "N\n   ; indented\nP1\n"
    cmds = parse(src)
    assert [type(c) for c in cmds] == [NCommand, PCommand]


def test_line_and_col_are_one_based() -> None:
    """``line``/``col`` positions must be 1-based and point at the identifier."""
    src = ";comment\n   N\nP1\n"
    cmds = parse(src)
    assert cmds[0].line == 2
    assert cmds[0].col == 4  # after 3 spaces
    assert cmds[1].line == 3
    assert cmds[1].col == 1


def test_missing_trailing_newline_is_fine() -> None:
    """Sources without a trailing newline must still parse cleanly."""
    cmds = parse("N\nP1")
    assert [type(c) for c in cmds] == [NCommand, PCommand]
