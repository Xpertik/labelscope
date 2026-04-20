"""Byte-exact PNG snapshot regression for the 7 EPL2 MVP fixtures.

Each fixture renders at the default DPI and is compared byte-for-byte
against a PNG baseline under ``tests/epl2/test_snapshots/`` via the
``file_regression`` fixture from ``pytest-regressions`` (no numpy
dependency; pixel diffing is not used because our policy is byte-exact).
Baselines are generated once with ``pytest --force-regen`` and then
treated as golden.
"""

from __future__ import annotations

import io
from pathlib import Path

import pytest
from pytest_regressions.file_regression import FileRegressionFixture

from labelscope.epl2.renderer import render
from tests.conftest import EPL_FILES


def _render_to_png_bytes(source_path: Path) -> bytes:
    """Render a fixture and return deterministic PNG bytes."""
    img = render(source_path.read_bytes())
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True, compress_level=9)
    return buf.getvalue()


@pytest.mark.parametrize("path", EPL_FILES, ids=lambda p: Path(p).stem)
def test_fixture_snapshot(path: Path, file_regression: FileRegressionFixture) -> None:
    """Render a fixture and compare its PNG bytes against the baseline."""
    png_bytes = _render_to_png_bytes(path)
    file_regression.check(png_bytes, binary=True, extension=".png", basename=path.stem)
