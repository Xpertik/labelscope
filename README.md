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

## Examples

Render a committed fixture via the `Renderer` class:

```python
from pathlib import Path

from labelscope import Renderer

renderer = Renderer(dpi=203)
img = renderer.render_file(Path("examples/epl1-55x34.txt"))
img.save("my_label.png", optimize=True, compress_level=9)
```

Render from an in-memory EPL2 string (useful when generating labels in
your app):

```python
from labelscope import Renderer

source = (
    "N\n"
    "q430\n"
    "Q270,24\n"
    'A22,8,0,3,1,1,N,"Hello labelscope"\n'
    'B52,60,0,1B,2,2,40,N,"SKU-00042"\n'
    "P1,1\n"
)
Renderer().render(source).save("hello.png", optimize=True, compress_level=9)
```

CLI, against the bundled fixtures:

```bash
labelscope render examples/epl1-55x34.txt -o preview.png
labelscope validate examples/epl2-55x34.txt
labelscope info examples/epl3-55x34.txt
```

### Supported fixtures

Real-world labels committed under `examples/` (size is `width_mm x height_mm`):

- `epl1-55x34.txt` — Alpaca garment tag: text + Code 128 + QR.
- `epl2-55x34.txt` — Multi-line garment tag with tri-color copy.
- `epl3-55x34.txt` — Yarn 6-pack tag with enlarged Code 128.
- `epl4-55x44.txt` — Rotated (portrait) garment tag with QR.
- `epl5-38x25.txt` — Compact `ZB` (bottom-fed) label, narrow web.
- `epl6-38x25.txt` — Compact `ZB` variant with short Code 128 payload.
- `epl7-38x25.txt` — Text-only compact `ZB` label.

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
