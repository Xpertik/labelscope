"""Typed exception hierarchy for labelscope.

Parser errors carry 1-based ``line``/``col`` positions and a human message
so CLI can emit GCC-style diagnostics (``file:line:col: msg``).
"""

from __future__ import annotations


class LabelscopeError(Exception):
    """Base exception for every error raised by the labelscope library."""


class ParseError(LabelscopeError):
    """Raised when the EPL2 tokenizer cannot interpret a source line.

    Attributes:
        line: 1-based source line number where the error was detected.
        col: 1-based column of the offending token.
        msg: Human-readable explanation of the failure.
    """

    def __init__(self, line: int, col: int, msg: str) -> None:
        """Store position fields and build the formatted message.

        Args:
            line: 1-based source line number.
            col: 1-based column of the offending token.
            msg: Human-readable explanation.
        """
        self.line: int = line
        self.col: int = col
        self.msg: str = msg
        super().__init__(f"{line}:{col}: {msg}")


class UnknownCommand(ParseError):
    """Raised in strict mode when a command identifier is not supported."""


class InvalidArgument(ParseError):
    """Raised when a command argument has the wrong type or arity."""


class MalformedString(ParseError):
    """Raised when a quoted string argument is not well-formed."""
