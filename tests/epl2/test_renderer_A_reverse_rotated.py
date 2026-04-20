"""Pin for Req RT4 rotated + reverse-video (R7 synthetic-only scenario)."""

from __future__ import annotations

from labelscope.epl2.renderer import render


def test_rotated_reverse_video_anchored_with_text() -> None:
    """``A50,50,1,...,R,"OK"`` draws a rotated black rect with white glyphs."""
    source = b'N\nQ120,10\nq200\nA50,50,1,2,1,1,R,"OK"\nP1\n'
    img = render(source)
    width, height = img.size

    ink_coords: list[tuple[int, int]] = [
        (x, y) for y in range(height) for x in range(width) if img.getpixel((x, y)) == 0
    ]
    assert ink_coords, "expected ink pixels for rotated reverse-video rect"

    xs = [x for x, _ in ink_coords]
    ys = [y for _, y in ink_coords]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)

    # The rotated block must live in the lower-left quadrant of the
    # anchor: rotation 1 shifts by (-W, 0) so ink extends LEFT of x=50
    # and DOWN from y=50.
    assert max_x <= 50, (min_x, max_x)
    assert min_y >= 50 - 2, (min_y, max_y)  # small tolerance for ascenders

    # Some paper pixels MUST exist inside the ink bounding box (the
    # glyph "holes" of the reverse-video rectangle).
    ink_inside = any(
        img.getpixel((x, y)) == 0 for y in range(min_y, max_y + 1) for x in range(min_x, max_x + 1)
    )
    paper_inside = any(
        img.getpixel((x, y)) != 0 for y in range(min_y, max_y + 1) for x in range(min_x, max_x + 1)
    )
    assert ink_inside, "no ink pixels in reverse rect"
    assert paper_inside, "no paper (glyph holes) in reverse rect"
