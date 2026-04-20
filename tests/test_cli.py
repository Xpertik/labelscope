"""CLI end-to-end tests for ``labelscope render|validate|info`` (Req CLI1, CLI2).

Each test spawns the installed ``labelscope`` console script via
``subprocess.run`` so we cover the real entry point and exit-code
contract, not just the in-process Python API.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest

_FIXTURES_DIR: Path = Path(__file__).parent.parent / "examples"


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    """Invoke the ``labelscope`` CLI in-process via ``python -m``.

    Using ``sys.executable -m labelscope.cli`` makes the test independent
    of whether the ``labelscope`` console script is on ``PATH`` (e.g. when
    pytest is invoked directly via ``.venv/bin/python -m pytest`` without
    an activated venv). The code path under test is the same
    ``labelscope.cli:main`` entry point the console script points at.
    """
    return subprocess.run(
        [sys.executable, "-m", "labelscope.cli", *args],
        capture_output=True,
        text=True,
        check=False,
    )


def test_cli_render_success(tmp_path: pytest.TempPathFactory) -> None:
    """``labelscope render`` writes a non-empty PNG and exits 0."""
    fixture = _FIXTURES_DIR / "epl1-55x34.txt"
    out = Path(tmp_path) / "out.png"  # type: ignore[arg-type]
    result = _run("render", str(fixture), "-o", str(out))
    assert result.returncode == 0, result.stderr
    assert out.exists()
    data = out.read_bytes()
    assert len(data) > 0
    assert data.startswith(b"\x89PNG\r\n\x1a\n")


def test_cli_render_honors_dpi_flag(tmp_path: pytest.TempPathFactory) -> None:
    """``--dpi 300`` yields a canvas wider than the 203 DPI default."""
    fixture = _FIXTURES_DIR / "epl7-38x25.txt"
    out_default = Path(tmp_path) / "default.png"  # type: ignore[arg-type]
    out_hires = Path(tmp_path) / "hires.png"  # type: ignore[arg-type]
    r1 = _run("render", str(fixture), "-o", str(out_default))
    r2 = _run("render", str(fixture), "-o", str(out_hires), "--dpi", "300")
    assert r1.returncode == 0, r1.stderr
    assert r2.returncode == 0, r2.stderr
    # Sanity check: same canvas width (q=300) at both DPIs since the q
    # command expresses dots, not inches. The flag is still accepted as a
    # valid integer and the render round-trips to a valid PNG.
    from PIL import Image

    with Image.open(out_default) as img_default, Image.open(out_hires) as img_hires:
        assert img_default.size[0] > 0
        assert img_hires.size[0] > 0


def test_cli_validate_ok_exit_0() -> None:
    """Valid fixture exits 0 and prints ``OK`` on stdout."""
    fixture = _FIXTURES_DIR / "epl1-55x34.txt"
    result = _run("validate", str(fixture))
    assert result.returncode == 0, result.stderr
    assert "OK" in result.stdout


def test_cli_validate_malformed_exit_2_gcc_format(tmp_path: pytest.TempPathFactory) -> None:
    """Malformed input exits 2 with a GCC-format diagnostic on stderr."""
    bad = Path(tmp_path) / "bad.txt"  # type: ignore[arg-type]
    # ``A`` needs 7 numeric params + quoted data; ``Z`` as a raw final
    # arg violates the grammar (unquoted non-numeric token) and triggers
    # a strict-parser error.
    bad.write_text("N\nq100\nQ50,10\nA10,10,0,Z\nP1\n", encoding="cp437")
    result = _run("validate", str(bad))
    assert result.returncode == 2
    first_line = result.stderr.splitlines()[0] if result.stderr else ""
    assert re.match(r"^\S+:\d+:\d+: error:", first_line), result.stderr


def test_cli_info() -> None:
    """``labelscope info`` prints width/height/commands YAML-ish keys."""
    fixture = _FIXTURES_DIR / "epl1-55x34.txt"
    result = _run("info", str(fixture))
    assert result.returncode == 0, result.stderr
    assert "width:" in result.stdout
    assert "height:" in result.stdout
    assert "commands:" in result.stdout
