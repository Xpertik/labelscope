"""Cross-process determinism pin (Req D1): two CLI invocations → same bytes."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

_FIXTURES_DIR: Path = Path(__file__).parent.parent.parent / "examples"


def test_cli_render_is_byte_identical_across_processes(
    tmp_path: pytest.TempPathFactory,
) -> None:
    """Rendering the same fixture twice via CLI yields byte-identical PNGs."""
    fixture = _FIXTURES_DIR / "epl1-55x34.txt"
    out_a = Path(tmp_path) / "a.png"  # type: ignore[arg-type]
    out_b = Path(tmp_path) / "b.png"  # type: ignore[arg-type]

    cmd_a = [sys.executable, "-m", "labelscope.cli", "render", str(fixture), "-o", str(out_a)]
    cmd_b = [sys.executable, "-m", "labelscope.cli", "render", str(fixture), "-o", str(out_b)]
    r1 = subprocess.run(cmd_a, capture_output=True, text=True, check=False)
    r2 = subprocess.run(cmd_b, capture_output=True, text=True, check=False)
    assert r1.returncode == 0, r1.stderr
    assert r2.returncode == 0, r2.stderr
    assert out_a.read_bytes() == out_b.read_bytes()
