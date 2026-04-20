"""AST-level tests for EPL2 command dataclasses (Req C1, task 4.13).

One test per P1 command verifies construction, equality, hashability,
and immutability. All commands must be frozen (hashable, no mutation)
and differentiable by type even if their field values coincide.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

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


def test_n_command() -> None:
    """``NCommand`` carries only line/col and is immutable + hashable."""
    a = NCommand(line=1, col=1)
    b = NCommand(line=1, col=1)
    assert a == b
    assert hash(a) == hash(b)
    assert {a, b} == {a}
    with pytest.raises(FrozenInstanceError):
        a.line = 2  # type: ignore[misc]


def test_r_command() -> None:
    """``RCommand`` stores x/y reference-point offsets."""
    a = RCommand(line=1, col=1, x=0, y=0)
    b = RCommand(line=1, col=1, x=0, y=0)
    assert a.x == 0
    assert a.y == 0
    assert a == b
    assert {a} == {a, b}
    assert a != RCommand(line=1, col=1, x=10, y=0)


def test_q_lowercase_command() -> None:
    """``qCommand`` stores the label width in dots."""
    a = qCommand(line=2, col=1, width=430)
    b = qCommand(line=2, col=1, width=430)
    assert a.width == 430
    assert a == b
    assert hash(a) == hash(b)
    assert a != qCommand(line=2, col=1, width=431)


def test_q_uppercase_command_default_gap_mode() -> None:
    """``QCommand`` defaults ``gap_mode`` to ``'gap'`` for the standard 2-arg form."""
    a = QCommand(line=3, col=1, height=270, gap=24)
    b = QCommand(line=3, col=1, height=270, gap=24, gap_mode="gap")
    assert a.height == 270
    assert a.gap == 24
    assert a.gap_mode == "gap"
    assert a == b


def test_q_uppercase_command_blackline_gap_mode() -> None:
    """``QCommand`` honors ``gap_mode='blackline'`` for the ``B``-prefixed form."""
    a = QCommand(line=3, col=1, height=270, gap=24, gap_mode="blackline")
    assert a.gap_mode == "blackline"
    assert a != QCommand(line=3, col=1, height=270, gap=24)


def test_z_command() -> None:
    """``ZCommand`` stores the print direction (``'T'`` or ``'B'``)."""
    top = ZCommand(line=4, col=1, direction="T")
    bottom = ZCommand(line=4, col=1, direction="B")
    assert top.direction == "T"
    assert bottom.direction == "B"
    assert top != bottom
    assert {top, bottom} == {top, bottom}


def test_s_command() -> None:
    """``SCommand`` stores the 1..5 speed value verbatim (renderer no-op)."""
    a = SCommand(line=5, col=1, speed=2)
    b = SCommand(line=5, col=1, speed=2)
    assert a.speed == 2
    assert a == b
    assert hash(a) == hash(b)


def test_d_command() -> None:
    """``DCommand`` stores the 0..15 density verbatim (renderer no-op)."""
    a = DCommand(line=6, col=1, density=14)
    b = DCommand(line=6, col=1, density=14)
    assert a.density == 14
    assert a == b
    assert hash(a) == hash(b)


def test_a_command() -> None:
    """``ACommand`` carries all 8 text parameters plus the quoted data."""
    a = ACommand(
        line=7,
        col=1,
        x=22,
        y=8,
        rotation=0,
        font=2,
        h_mult=1,
        v_mult=1,
        reverse=False,
        data="Alpaca Cable Fingerless Gloves",
    )
    b = ACommand(
        line=7,
        col=1,
        x=22,
        y=8,
        rotation=0,
        font=2,
        h_mult=1,
        v_mult=1,
        reverse=False,
        data="Alpaca Cable Fingerless Gloves",
    )
    assert a == b
    assert hash(a) == hash(b)
    assert {a} == {a, b}
    # Reverse flag and rotation differentiate otherwise-identical commands.
    reversed_a = ACommand(
        line=7,
        col=1,
        x=22,
        y=8,
        rotation=0,
        font=2,
        h_mult=1,
        v_mult=1,
        reverse=True,
        data="Alpaca Cable Fingerless Gloves",
    )
    assert a != reversed_a
    with pytest.raises(FrozenInstanceError):
        a.data = "other"  # type: ignore[misc]


def test_a_command_empty_data_allowed() -> None:
    """``ACommand`` accepts an empty data string (R6)."""
    a = ACommand(
        line=1,
        col=1,
        x=0,
        y=0,
        rotation=0,
        font=2,
        h_mult=1,
        v_mult=1,
        reverse=False,
        data="",
    )
    assert a.data == ""


def test_b_command() -> None:
    """``BCommand`` carries all 9 1D-barcode parameters plus the data."""
    a = BCommand(
        line=8,
        col=1,
        x=180,
        y=130,
        rotation=0,
        symbology="1B",
        narrow=1,
        wide=2,
        height=35,
        human_readable=False,
        data="W1A/1000260",
    )
    b = BCommand(
        line=8,
        col=1,
        x=180,
        y=130,
        rotation=0,
        symbology="1B",
        narrow=1,
        wide=2,
        height=35,
        human_readable=False,
        data="W1A/1000260",
    )
    assert a == b
    assert hash(a) == hash(b)
    assert {a, b} == {a}
    # HRI flag differentiates two otherwise-identical commands.
    hri = BCommand(
        line=8,
        col=1,
        x=180,
        y=130,
        rotation=0,
        symbology="1B",
        narrow=1,
        wide=2,
        height=35,
        human_readable=True,
        data="W1A/1000260",
    )
    assert a != hri


def test_b_lowercase_command() -> None:
    """``bCommand`` keeps the raw comma-joined param block for the renderer."""
    a = bCommand(
        line=9,
        col=1,
        x=52,
        y=130,
        symbology="Q",
        params="",
        data="https://classicalpaca.com/help/qr/?s=ht",
    )
    b = bCommand(
        line=9,
        col=1,
        x=52,
        y=130,
        symbology="Q",
        params="",
        data="https://classicalpaca.com/help/qr/?s=ht",
    )
    assert a == b
    assert hash(a) == hash(b)
    # Non-empty params must differentiate.
    with_params = bCommand(
        line=9,
        col=1,
        x=52,
        y=130,
        symbology="Q",
        params="m2,s5,eH",
        data="https://classicalpaca.com/help/qr/?s=ht",
    )
    assert a != with_params


def test_p_command_copies_only() -> None:
    """``PCommand`` accepts the 1-arg form with ``qty`` defaulting to ``None``."""
    a = PCommand(line=10, col=1, copies=1)
    assert a.copies == 1
    assert a.qty is None
    assert a == PCommand(line=10, col=1, copies=1, qty=None)


def test_p_command_with_qty() -> None:
    """``PCommand`` accepts the 2-arg form ``P<copies>,<qty>``."""
    a = PCommand(line=10, col=1, copies=3, qty=2)
    b = PCommand(line=10, col=1, copies=3, qty=2)
    assert a.qty == 2
    assert a == b
    assert hash(a) == hash(b)
    assert a != PCommand(line=10, col=1, copies=3)


def test_command_line_col_defaults() -> None:
    """Line/col accept ``0`` for synthetic (renderer-internal) commands.

    Renderer-internal constructions (e.g. synthetic defaults or tests)
    do NOT need to cite a source position; a zero is valid.
    """
    synthetic_n = NCommand(line=0, col=0)
    assert synthetic_n.line == 0
    assert synthetic_n.col == 0
    synthetic_a = ACommand(
        line=0,
        col=0,
        x=0,
        y=0,
        rotation=0,
        font=2,
        h_mult=1,
        v_mult=1,
        reverse=False,
        data="",
    )
    assert synthetic_a.line == 0
    assert synthetic_a.col == 0


def test_different_commands_are_never_equal() -> None:
    """Two commands of different types are never equal, even at same (line,col)."""
    n = NCommand(line=1, col=1)
    r = RCommand(line=1, col=1, x=0, y=0)
    assert n != r  # type: ignore[comparison-overlap]


def test_all_commands_subclass_command_base() -> None:
    """Every concrete command MUST descend from the shared ``Command`` base."""
    concrete: list[type[Command]] = [
        NCommand,
        RCommand,
        qCommand,
        QCommand,
        ZCommand,
        SCommand,
        DCommand,
        ACommand,
        BCommand,
        bCommand,
        PCommand,
    ]
    for cls in concrete:
        assert issubclass(cls, Command)


def test_command_repr_is_deterministic() -> None:
    """Frozen+slots dataclasses get a stable auto-generated ``__repr__``."""
    a = ACommand(
        line=1,
        col=1,
        x=0,
        y=0,
        rotation=0,
        font=2,
        h_mult=1,
        v_mult=1,
        reverse=False,
        data="hi",
    )
    b = ACommand(
        line=1,
        col=1,
        x=0,
        y=0,
        rotation=0,
        font=2,
        h_mult=1,
        v_mult=1,
        reverse=False,
        data="hi",
    )
    assert repr(a) == repr(b)
    # Field order is stable: line and col come first (from the base).
    assert repr(a).startswith("ACommand(line=1, col=1,")
