"""Font 5 is UPPERCASE ONLY (Req RT1; manual p. 45).

Rendering ``"hello"`` via font 5 must yield the same pixels as rendering
``"HELLO"`` because the renderer upcases the payload before rasterizing.
"""

from __future__ import annotations

from labelscope.epl2.renderer import render


def test_font5_renders_lowercase_as_uppercase() -> None:
    """Font 5 with lowercase input produces byte-identical output to upper."""
    lower = b'N\nQ80,10\nq200\nA10,10,0,5,1,1,N,"hello"\nP1\n'
    upper = b'N\nQ80,10\nq200\nA10,10,0,5,1,1,N,"HELLO"\nP1\n'
    img_lower = render(lower)
    img_upper = render(upper)
    assert img_lower.tobytes() == img_upper.tobytes()
