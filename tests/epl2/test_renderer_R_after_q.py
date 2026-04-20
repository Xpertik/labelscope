"""Decision D: ``R`` after ``q`` resets canvas to the full head width."""

from __future__ import annotations

from labelscope.epl2.renderer import render


def test_R_before_q_leaves_q_width_intact() -> None:
    source = b"R0,0\nN\nq300\nQ80,10\nP1\n"
    img = render(source)
    assert img.size == (300, 80)


def test_R_after_q_resets_to_full_head_width() -> None:
    # R follows q → decision D: reset to full 832-dot ZD410 head width.
    source = b"N\nq300\nR0,0\nQ80,10\nP1\n"
    img = render(source)
    assert img.size == (832, 80)
