"""Pin for Req M2: ``D`` and ``S`` are visual no-ops (byte-identical output)."""

from __future__ import annotations

from labelscope.epl2.renderer import render


def test_D_and_S_produce_identical_bytes() -> None:
    """Two renders differing only in ``D14``/``S5`` yield identical bytes."""
    without = b'N\nQ80,10\nq200\nA10,10,0,2,1,1,N,"HELLO"\nP1\n'
    with_ds = b'N\nD14\nS5\nQ80,10\nq200\nA10,10,0,2,1,1,N,"HELLO"\nP1\n'
    img_a = render(without)
    img_b = render(with_ds)
    assert img_a.tobytes() == img_b.tobytes()
