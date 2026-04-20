"""Determinism pin (Req D1): same input → same bytes in-process."""

from __future__ import annotations

import io

from PIL import Image
from PIL.PngImagePlugin import PngInfo

from labelscope.epl2.renderer import render

_FIXTURE = b'N\nQ100,10\nq200\nA10,10,0,2,1,1,N,"HELLO"\nA10,40,0,3,1,1,R,"WORLD"\nP1\n'


def test_render_twice_yields_identical_pixels() -> None:
    a = render(_FIXTURE)
    b = render(_FIXTURE)
    assert a.tobytes() == b.tobytes()


def test_saved_png_bytes_are_identical() -> None:
    def _save(img: Image.Image) -> bytes:
        buf = io.BytesIO()
        img.save(
            buf,
            format="PNG",
            optimize=True,
            compress_level=9,
            pnginfo=PngInfo(),
        )
        return buf.getvalue()

    a = _save(render(_FIXTURE))
    b = _save(render(_FIXTURE))
    assert a == b
