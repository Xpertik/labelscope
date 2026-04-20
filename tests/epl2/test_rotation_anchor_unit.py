"""Unit pin for ``_rotation_anchor_offset`` (bug-fix #rotation-anchor).

Per Zebra EPL2 empirical behavior, the anchor corner rotates with the
text: top-left for 0°, top-right for 90° CW, bottom-right for 180°,
bottom-left for 270° CW. This test pins the exact offset math.
"""

from __future__ import annotations

import pytest

from labelscope.epl2.renderer import _rotation_anchor_offset


@pytest.mark.parametrize(
    ("rotation", "expected"),
    [
        (0, (0, 0)),
        (1, (-40, 0)),  # -W
        (2, (-40, -16)),  # -W, -H
        (3, (0, -16)),  # -H
    ],
)
def test_rotation_anchor_offset(rotation: int, expected: tuple[int, int]) -> None:
    """Each of the 4 rotations maps to its documented (dx, dy) offset."""
    size = (40, 16)
    assert _rotation_anchor_offset(rotation, size) == expected
