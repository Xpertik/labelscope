"""ZB orientation composes as a final 180-degree transpose (Req RC3)."""

from __future__ import annotations

from PIL import Image

from labelscope.epl2.renderer import render


def test_ZB_equals_transpose_180_of_ZT() -> None:
    zt_src = b'N\nQ80,10\nq120\nA10,10,0,2,1,1,N,"AB"\nP1\n'
    zb_src = b'N\nZB\nQ80,10\nq120\nA10,10,0,2,1,1,N,"AB"\nP1\n'
    zt_img = render(zt_src)
    zb_img = render(zb_src)
    rotated = zt_img.transpose(Image.Transpose.ROTATE_180)
    assert zb_img.tobytes() == rotated.tobytes()
