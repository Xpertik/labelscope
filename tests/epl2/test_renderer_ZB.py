"""``Z`` orientation is printer feed metadata, not a visual rotation.

Real prints of fixtures declaring ``ZB`` show content at program
coordinates (origin top-left) — the physical label reads right-side up
regardless of ZT vs ZB. We keep the flag in ``_RenderContext.orientation``
for debug / metadata, but the rendered canvas is identical to the ZT
version for the same content.
"""

from __future__ import annotations

from labelscope.epl2.renderer import render


def test_ZB_and_ZT_produce_identical_rasters() -> None:
    zt_src = b'N\nQ80,10\nq120\nA10,10,0,2,1,1,N,"AB"\nP1\n'
    zb_src = b'N\nZB\nQ80,10\nq120\nA10,10,0,2,1,1,N,"AB"\nP1\n'
    zt_img = render(zt_src)
    zb_img = render(zb_src)
    assert zb_img.tobytes() == zt_img.tobytes()
