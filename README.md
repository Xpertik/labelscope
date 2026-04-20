# labelscope

[![PyPI](https://img.shields.io/badge/pypi-unreleased-lightgrey.svg)](https://pypi.org/project/labelscope/)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](./LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)

Python SDK and CLI for previewing Zebra EPL2 thermal labels as deterministic
1-bit PNGs — no physical printer required. Built on Pillow, targets the
Zebra ZD410 at 203 DPI, with an architecture ready for ZPL / TSPL.

## Status

`0.1.0` MVP. Supports EPL2 text, Code 128 (forced subset B), UPC-A, EAN-13,
and QR. Snapshot tests lock the renderer byte-for-byte.

## Install

```bash
pip install labelscope            # core (text only)
pip install "labelscope[barcodes]" # adds treepoem / Ghostscript for barcodes
```

## Quick start

```python
from pathlib import Path

from labelscope import render

img = render(Path("examples/epl1-55x34.txt").read_bytes())
img.save("epl1.png", optimize=True, compress_level=9)
```

## CLI

```bash
labelscope render examples/epl1-55x34.txt -o epl1.png --dpi 203
labelscope validate examples/epl1-55x34.txt
labelscope info examples/epl1-55x34.txt
labelscope render examples/epl2-55x34.txt --show
```

## Supported EPL2 commands

- Setup: `N`, `R`, `q`, `Q`, `S`, `D`, `ZT`, `ZB`, `P`
- Text: `A` (fonts 1–5, rotations 0/1/2/3, multipliers, reverse video)
- 1D barcodes: `B` (Code 128 subset B forced via BWIPP `^104`, UPC-A, EAN-13)
- 2D barcodes: `b` (QR: Model 1/2, ECC L/M/Q/H, magnification)

Full command reference: [`docs/epl2-reference.md`](./docs/epl2-reference.md).
Project spec: [`contexto.md`](./contexto.md).

## License

Apache 2.0. © 2026 Xpertik. Bundled DejaVu Sans Mono ships under its own
permissive license — see `labelscope/core/_fonts/DejaVuSansMono-LICENSE.txt`.
