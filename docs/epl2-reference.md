# EPL2 Command Reference — labelscope

> Scoped reference for the labelscope MVP renderer. Source: Zebra "Eltron EPL Programming Guide" (part 14245L-003 Rev. A, 12/16/13).
> Covers only the commands needed for MVP + adjacent context (fonts, codepages, barcodes).
> For commands NOT in this doc, consult the full manual at `/epl2-pm-en.pdf` (local copy of the Zebra PDF).

## Table of Contents

- [Coordinate system and units](#coordinate-system-and-units)
- [Program structure](#program-structure)
- Commands (P1 MVP)
  - [`N` — Clear Image Buffer](#n--clear-image-buffer)
  - [`R` — Set Reference Point](#r--set-reference-point)
  - [`q` — Set Label Width](#q--set-label-width)
  - [`Q` — Set Form Length](#q--set-form-length)
  - [`Z` — Print Direction (`ZT` / `ZB`)](#z--print-direction-zt--zb)
  - [`S` — Speed Select](#s--speed-select)
  - [`D` — Density](#d--density)
  - [`A` — ASCII Text](#a--ascii-text)
  - [`B` — Bar Code (1D)](#b--bar-code-1d)
  - [`b` — 2D Bar Code (QR / PDF417 / Data Matrix / Aztec / MaxiCode)](#b--2d-bar-code-qr--pdf417--data-matrix--aztec--maxicode)
  - [`P` — Print](#p--print)
- [Bitmap fonts (1–5)](#bitmap-fonts-15)
- [Code pages and character sets (`I` command context)](#code-pages-and-character-sets-i-command-context)
- [Barcode symbology map](#barcode-symbology-map)
- [Print orientation summary (`ZB` / `ZT`)](#print-orientation-summary-zb--zt)
- [Referenced but deferred (not in MVP)](#referenced-but-deferred-not-in-mvp)
- [Known ambiguities / gaps](#known-ambiguities--gaps)

---

## Coordinate system and units

- **Unit**: dots. Conversion to physical length depends on print head resolution:
  - 203 dpi → 8 dots/mm (Zebra ZD410, our MVP target).
  - 300 dpi → ~11.8 dots/mm.
- **Origin (0,0)**: top-left of the image buffer after the active `R` (reference-point) and `Z` (print-direction) commands are applied. X grows to the right, Y grows downward.
- **Canvas size**: defined by `q` (width in dots, after `R`) and `Q` (form length in dots + gap/black-line thickness). Minimum blank margin of 0.04 in (1 mm) is recommended by the manual (p. 140).
- **Text Y coordinate**: the manual defines `A`/`B` Y-start as the top-left of the character/barcode cell (see `A` p. 44, `B` p. 53). Pixel-exact baseline offset is not specified — flagged in [R9](#r9).
- **`R` interaction with `q`**: Sending `R` after `q` resets the image buffer to the full print-head width and applies the `R` offset, effectively nullifying `q` (p. 137, 143). In the MVP fixtures, every file starts with `R0,0` before `q`, so the two settings compose cleanly.

## Program structure

A typical EPL2 label program, as observed in all 7 fixtures:

```
R0,0              ; set reference point (optional, defaults to 0,0)
N                 ; clear image buffer
Q<h>,<gap>        ; set form length + gap
q<w>              ; set label width
S<n>              ; speed (no-op for renderer)
D<n>              ; density (no-op for renderer; only 3/7 fixtures)
ZB                ; print bottom-first (only 3/7 fixtures)
A...,"..."        ; one or more text fields
B...,"..."        ; one or more 1D barcodes (optional)
b...,"..."        ; one or more 2D barcodes (optional)
P<n>[,<m>]        ; print n copies
```

Lines terminate with LF or CRLF (both accepted — [R10](#r10)). Blank lines are ignored. Comments start with `;` (manual p. 176, not seen in fixtures).

---

## Commands

### `N` — Clear Image Buffer

**Syntax**: `N`

**Parameters**: none.

**Notes for renderer**:
- Reset canvas to white (all bits = 0).
- Must be issued after the configuration commands (`q`, `Q`, `R`, `Z`, `S`, `D`) and before any draw command (`A`, `B`, `b`, `X`, `LO`, etc.).
- Do NOT use `N` inside a stored form sequence (`FS…FE`). Not relevant to MVP (we do not implement stored forms).

**Gotchas**:
- The manual recommends sending a leading LF before `N` to flush the command buffer — irrelevant to the renderer, but real-world captures may contain it.

**Manual reference**: p. 122.

---

### `R` — Set Reference Point

**Syntax**: `Rp1,p2`

**Parameters**:

| Param | Meaning | Unit |
|------|---------|------|
| `p1` | Horizontal (left) margin | dots |
| `p2` | Vertical (top) margin | dots |

**Notes for renderer**:
- Shifts the origin of all subsequent coordinates by `(p1, p2)`.
- Forces the image buffer to the full print-head width, overriding `q`. In practice, MVP fixtures always send `R0,0` before `q`, so the override is a no-op.
- Must be applied at parse time or at draw time consistently. Recommended: store `ref_point` in render state and add it to every `(x, y)` in `A`/`B`/`b`/`X`/`LO`/`LW` before rasterizing.

**Gotchas**:
- If non-zero `R` appears, it does NOT rotate content — it only translates it. Combine with `Z` for orientation.

**Manual reference**: p. 143.

---

### `q` — Set Label Width

**Syntax**: `qp1`

**Parameters**:

| Param | Meaning | Unit |
|------|---------|------|
| `p1` | Printable label width | dots |

**Notes for renderer**:
- Sets canvas width in dots.
- If `R` follows `q`, the `q` value is overridden (see `R`).
- Label is center-aligned on center-aligned printers; left-aligned on left-aligned printers (p. 137). The ZD410 is left-aligned; the MVP renderer should treat `q` as the full canvas width with origin at the left edge.

**Gotchas**:
- Accepted values are not spelled out as a numeric range in the manual; the practical cap is the print head width (e.g. 832 dots / 104 mm for ZD410 4" models). The renderer should accept any positive integer and let the fixture dictate sanity.

**Manual reference**: p. 137.

---

### `Q` — Set Form Length

**Syntax**: `Qp1,p2[,±p3]`

**Parameters**:

| Param | Meaning | Unit / Accepted values |
|------|---------|------------------------|
| `p1` | Label length (distance edge-to-edge, or feed distance in continuous mode) | 0–65535 dots |
| `p2` | Gap length (default) or black-line thickness (prefix `B`) or `0` for continuous | 16–240 dots (203 dpi); 18–240 (300 dpi) |
| `p3` | Offset length (for black-line mode; optional for gap/continuous). Positive only. | dots |

**Notes for renderer**:
- `p1` is the **label** length (canvas height).
- `p2` is the gap between labels (stock/liner), NOT part of the printable area — so canvas height = `p1`, not `p1 + p2`.
- `p3` is not used in any MVP fixture; parse but ignore.
- `Q` forces the printer to recalculate and reformat the image buffer (p. 139). Must be applied before `N`/draw commands.

**Gotchas**:
- The manual's examples show `Q100,24+24` where `+24` is `p3`. Our fixtures only use the 2-arg form (`Q270,24`).
- Dimensional sanity check from explore: `q` × `Q` matches nominal label size within ~10 dots (~1.25 mm) — confirms canvas height = `p1` only.

**Manual reference**: p. 139–141.

---

### `Z` — Print Direction (`ZT` / `ZB`)

**Syntax**: `Zp1` → in practice written as `ZT` or `ZB`.

**Parameters**:

| Param | Accepted values |
|------|-----------------|
| `p1` | `T` = print from top of image buffer (default) • `B` = print from bottom |

**Notes for renderer**:
- `ZT` (default): content rasterized top-first; operator views the printed label right-side-up.
- `ZB`: content rasterized bottom-first; effectively a 180° rotation of the entire image buffer.
- **Recommended implementation**: accumulate all draw commands into the logical canvas, then at `P` time rotate the canvas 180° if `ZB` was set. Do NOT translate coordinates command-by-command (fragile with reverse-video boxes and rotated text).
- Must be applied BEFORE draw commands per manual's example (p. 171).

**Gotchas**:
- The manual's note reads "The top of the image buffer prints first and is viewed by the operator as printing upside down" (p. 170) — this is a printer-mechanism statement, NOT a visual flip of `ZT`. Empirically: `ZT` = right-side-up, `ZB` = flipped 180°.
- 3 of 7 MVP fixtures (epl5/6/7, the 38x25 mm labels) use `ZB`.

**Manual reference**: p. 170–171.

---

### `S` — Speed Select

**Syntax**: `Sp1`

**Parameters**:

| Param | Meaning |
|------|---------|
| `p1` | Speed value per printer model table (e.g. GK420: `2`=2 ips, `3`=3 ips, `4`=4 ips, `5`=5 ips). Full table on p. 144. |

**Notes for renderer**:
- **Parse-only / no-op**. Speed affects physical printing (ribbon drag, head timing) but does NOT affect the bit buffer.
- Must not raise a parse error.

**Gotchas**:
- All 7 MVP fixtures send `S2` (2 ips). Value range is model-dependent (`0`–`6` in the manual's examples).

**Manual reference**: p. 144.

---

### `D` — Density

**Syntax**: `Dp1`

**Parameters**:

| Param | Meaning | Accepted values |
|------|---------|-----------------|
| `p1` | Print head heat/darkness | 0–15 (0 = lightest, 15 = darkest) |

**Notes for renderer**:
- **Parse-only / no-op**. Density controls heat applied to the print head; the bit buffer is unaffected.
- If we ever add photo-realistic rendering (ink bleed simulation) we could use `p1`, but not in MVP.

**Gotchas**:
- 3 of 7 fixtures use `D14` (very dark). Must not raise a parse error.

**Manual reference**: p. 88.

---

### `A` — ASCII Text

**Syntax**: `Ap1,p2,p3,p4,p5,p6,p7,"DATA"`

**Parameters**:

| Param | Meaning | Accepted values |
|------|---------|-----------------|
| `p1` | Horizontal start (X) | dots |
| `p2` | Vertical start (Y) | dots |
| `p3` | Rotation | `0` = 0°, `1` = 90° CW, `2` = 180°, `3` = 270° CW (Asian printers also: `4`–`7` with horizontal-to-vertical character arrangement — not MVP) |
| `p4` | Font selection | `1`–`5` = built-in bitmap fonts (see [Bitmap fonts](#bitmap-fonts-15)); `6`,`7` = numeric-only; `A`–`Z` / `a`–`z` = soft fonts (not MVP); `8`,`9` = Asian (not MVP) |
| `p5` | Horizontal multiplier | `1`–`6`, `8` |
| `p6` | Vertical multiplier | `1`–`9` |
| `p7` | Reverse image flag | `N` = normal; `R` = reverse video (white text on filled black rectangle sized to the text bbox) |
| `DATA` | Fixed text in double quotes | Empty `""` is legal. Embedded `"` must be escaped as `\"`; literal backslash as `\\`. |

**Notes for renderer**:
- `p5`/`p6` scale the bitmap glyph by integer multipliers (pixel doubling, not TTF scaling).
- `p7 = R`: draw a filled black rectangle the exact width × height of the post-multiplier text, then draw the glyphs in WHITE on top. The rectangle must rotate together with the text when `p3` ≠ 0 ([R7](#r7)).
- Empty string: skip drawing, no error ([R6](#r6)).
- `data` may contain `Vnn` / `Cn` / `TD` / `TT` tokens interleaved with quoted literals (variables, counters, RTC). None of the MVP fixtures use them — parse them only if we later see them.
- `data` may also contain simple expressions `Vnn+n` or `Vnn-Vmm` (p. 48) — out of scope for MVP.

**Gotchas**:
- The manual recommends using `LE` (line-draw-XOR) over `p7=R` for reverse video "because it provides the best size, position, and centering" (p. 45). Real fixtures still use `p7=R` — we MUST support it.
- Decoding of the data bytes is NOT UTF-8. See [R1](#r1) and [Code pages](#code-pages-and-character-sets-i-command-context).

**Example from fixture `epl1-55x34.txt`**:
```
A22,8,0,2,1,1,N,"Alpaca Cable Fingerless Gloves"
A375,38,0,4,1,1,R,"O/S"                            ; reverse-video "O/S" tag
A400,120,1,2,1,1,N,"RN-145804"                     ; rotated 90° CW
```

**Manual reference**: p. 43–49.

---

### `B` — Bar Code (1D)

**Syntax**: `Bp1,p2,p3,p4,p5,p6,p7,p8,"DATA"`

**Parameters**:

| Param | Meaning | Accepted values |
|------|---------|-----------------|
| `p1` | Horizontal start (X) | dots |
| `p2` | Vertical start (Y) | dots |
| `p3` | Rotation | `0`/`1`/`2`/`3` (as `A`) |
| `p4` | Barcode selector | see [Barcode symbology map](#barcode-symbology-map) |
| `p5` | Narrow bar width | dots, 1–10 (varies by symbology) |
| `p6` | Wide bar width | dots, 2–30 (varies by symbology) |
| `p7` | Bar code height | dots |
| `p8` | Print human-readable (HRI) | `B` = yes, `N` = no |
| `DATA` | Barcode content, double-quoted. Must match symbology's data rules. | Backslash escapes as in `A`. |

**Notes for renderer**:
- Delegate rasterization to `treepoem` (BWIPP wrapper). Map `p4` → BWIPP name as per the symbology table below.
- Pass `p5` as the narrow-bar module width to BWIPP (`inkspread` / module-width option name depends on symbology). Wide bar `p6` is the "wide" stroke where the symbology supports variable ratios.
- `p7` sets the bar height in dots; apply as BWIPP's `height` option in mm (convert: `height_mm = p7 / (dpi/25.4)`).
- `p8 = B` → render HRI with BWIPP's default HRI font. `p8 = N` → suppress HRI.
- For Code 128 specifically (`p4 = 1B`, mode B), pass `parse=true` and force mode-B via BWIPP options if auto-select produces different bars ([R5](#r5)).

**Gotchas**:
- `DATA` hyphens may be used as visual separators in some symbologies and are stripped (see Bar Code Table Notes p. 54). Code 128 does NOT strip hyphens.
- `ASCII 06` (0x06) delimits variable-length fields in some symbologies — not seen in MVP.

**Example from fixture `epl1-55x34.txt`**:
```
B180,130,0,1B,1,2,35,N,"W1A/1000260"
;       x=180 y=130 rot=0 symbology=1B(Code128B) narrow=1 wide=2 height=35 HRI=N
```

**Manual reference**: p. 52–57 (general + Code 128). RSS-14 family on p. 58–61.

---

### `b` — 2D Bar Code (QR / PDF417 / Data Matrix / Aztec / MaxiCode)

**Syntax (QR Code — the only 2D symbology in MVP fixtures)**: `bp1,p2,p3[,p4][,p5][,p6][,p7][,p8]"DATA"`

**Parameters** (QR):

| Param | Prefix | Meaning | Accepted values | Default |
|------|--------|---------|-----------------|---------|
| `p1` | — | Horizontal start (X) | dots | — |
| `p2` | — | Vertical start (Y) | dots | — |
| `p3` | — | Symbology selector | `Q` = QR | — |
| `p4` | `m` | Code model | `1`, `2` | `2` |
| `p5` | `s` | Scale factor (module magnification) | `1`–`99` | `3` |
| `p6` | `e` | Error-correction level | `L`, `M`, `Q`, `H` | `M` |
| `p7` | `i` | Data input mode | `A` = auto, `M` = manual (first DATA char selects N/A/K/B) | `A` |
| `p8` | `D` | Append symbol (multi-QR chaining) | sub-params `c`, `d`, `p` | off |
| `DATA` | — | Payload | quoted; reserved chars `"` and `/` escaped with `\` | — |

**Notes for renderer**:
- `p4`–`p8` are optional, can appear in any order before `"DATA"`, and are identified by their PREFIX CHAR (`m`, `s`, `e`, `i`, `D`). Commas between them are NOT required (p. 83).
- MVP fixtures (epl1, epl2, epl4) use the bare `b<x>,<y>,Q,"<data>"` form → all defaults: model 2, magnification 3, ECC M, auto data input.
- Delegate to `treepoem` with BWIPP name `qrcode`. Magnification → module size in dots (`p5 = s × module_unit_dots`).
- The `b` command ALSO encodes Aztec, Data Matrix, MaxiCode, PDF417 — selected by `p3`. NOT in MVP fixtures. See manual pages 62–82 if we need to add them.

**Gotchas**:
- The manual says "Japanese printer models only" for the QR form (p. 83) — but empirically the ZD410 prints QR with this exact syntax. Treat the restriction as a documentation gap and not a hard rule ([R12](#r12)).
- Data reserved characters are `"` and `/`. If a URL contains `/`, the fixtures we have simply embed them without escaping and the printer accepts it. BWIPP's `qrcode` accepts `/` as-is. Do NOT pre-escape.

**Example from fixture `epl1-55x34.txt`**:
```
b52,130,Q,"https://classicalpaca.com/help/qr/?s=ht&m=b&v=0XF&k=5"
```

**Manual reference**: p. 83–84 (QR). Aztec p. 62, Aztec Mesa p. 66, Data Matrix p. 68, MaxiCode p. 72, PDF417 p. 76.

---

### `P` — Print

**Syntax**: `Pp1[,p2]`

**Parameters**:

| Param | Meaning | Accepted values |
|------|---------|-----------------|
| `p1` | Number of label sets | 1–65535 |
| `p2` | Number of copies per label (for use with counters) | 1–65535 |

**Notes for renderer**:
- Marks the end of the label program. For our preview renderer: finalize the canvas and emit a PIL `Image`.
- For MVP we render ONE label image regardless of `p1`/`p2`. We may later emit a multi-image preview.
- Do NOT use inside stored forms (`FS…FE`) — use `PA` instead. Not MVP.

**Gotchas**:
- Must be parsed (not skipped) to mark "end of program". Fixtures send `P1` or `P1,1`.

**Manual reference**: p. 135.

---

## Bitmap fonts (1–5)

Cell dimensions (width × height, in dots) from the `A` command p4 table (p. 44). `cpi` = characters per inch, `pts` = approximate point size.

| Font | 203 dpi cell (W×H) | 203 dpi cpi / pts | 300 dpi cell (W×H) | 300 dpi cpi / pts | Notes |
|-----:|:-------------------|:------------------|:-------------------|:------------------|:------|
| 1 | 8 × 12 | 20.3 cpi, 6 pt | 12 × 20 | 25 cpi, 4 pt | Fixed pitch |
| 2 | 10 × 16 | 16.9 cpi, 7 pt | 16 × 28 | 18.75 cpi, 6 pt | Fixed pitch |
| 3 | 12 × 20 | 14.5 cpi, 10 pt | 20 × 36 | 15 cpi, 8 pt | Fixed pitch |
| 4 | 14 × 24 | 12.7 cpi, 12 pt | 24 × 44 | 12.5 cpi, 10 pt | Fixed pitch |
| 5 | 32 × 48 | 5.6 cpi, 24 pt | 48 × 80 | 6.25 cpi, 21 pt | Fixed pitch; **UPPERCASE ONLY** (manual p. 45) |
| 6, 7 | 14 × 19 | numeric only | 14 × 19 | numeric only | Not seen in MVP fixtures |
| 8, 9 | — | — | — | — | Asian printers only — OUT OF SCOPE |
| A–Z, a–z | — | — | — | — | Soft fonts (downloadable) — OUT OF SCOPE |

**Implementation note**: these are Zebra's bitmap glyphs. Pixel-exact match requires shipping or regenerating the glyph tables ([R2](#r2)). The MVP decision (from explore) is approach (c): render TTF (DejaVu Sans Mono or similar) into a locked-width cell that enforces the EPL2 (W × H) metrics.

---

## Code pages and character sets (`I` command context)

The `I` command (not in MVP but relevant to [R1](#r1)) controls how data bytes are interpreted.

**Syntax**: `Ip1,p2,p3`

| Param | Meaning |
|-------|---------|
| `p1` | Data bits: `7` or `8` |
| `p2` | Codepage/language selector (e.g. `0` = DOS 437, `1` = DOS 850, `A` = Windows 1252) |
| `p3` | KDU country code (8-bit only, e.g. `001` = USA) |

**Default**: `I8,0,001` → **8-bit data, DOS CP437, USA** (manual p. 113).

**Implication for the renderer**:
- Raw bytes in quoted text MUST be decoded as **CP437** (or Latin-1 as a close-enough fallback), NOT UTF-8.
- Authors writing fixtures in UTF-8 will see multi-byte characters byte-split and rendered as CP437 glyphs (example: `–` (EN DASH, U+2013 = EF BF BD sequence depending on encoding) prints as `COo` or similar garbage on the physical printer — see fixture epl2).
- The MVP renderer MUST reproduce this behavior: feed the raw bytes through CP437 to get the glyph indices, do NOT interpret UTF-8.
- See manual Appendix D, "Code Pages for EPL Programming" (p. 337–874), for per-codepage character maps. CP437 map starts on p. 855.

**Manual reference**: `I` command p. 112. Appendix D starts p. 337.

---

## Barcode symbology map

Maps observed and common EPL2 selector characters (`p4` of `B`, or `p3` of `b`) to BWIPP / treepoem symbology names.

| EPL2 selector | Symbology | BWIPP / treepoem name | In MVP? | Notes |
|---------------|-----------|------------------------|:-------:|-------|
| `1B` | Code 128 mode B (forced) | `code128` with `parse=true` and mode-B option | **YES** | All 1D barcodes in MVP fixtures. Zebra forces subset B — override BWIPP's auto-select ([R5](#r5)). |
| `Q` (on `b`) | QR Code | `qrcode` | **YES** | 3/7 fixtures use this. |
| `1` | Code 128 auto A/B/C | `code128` (auto) | no | Default auto-mode. |
| `1A` | Code 128 mode A | `code128` mode A | no | |
| `1C` | Code 128 mode C | `code128` mode C | no | |
| `1D` | Code 128 with Deutsche Post check digit | `code128` + custom | no | Specialized. |
| `1E` | UCC/EAN 128 | `gs1-128` | no | |
| `0` | Code 128 UCC SSCC | `sscc18` (subset) | no | |
| `3` | Code 39 standard/extended | `code39` / `code39ext` | no | |
| `3C` | Code 39 with check digit | `code39` `includecheck` | no | |
| `9` | Code 93 | `code93` | no | |
| `K` | Codabar | `rationalizedCodabar` | no | |
| `E80` | EAN-8 | `ean8` | no | |
| `E30` | EAN-13 | `ean13` | no | |
| `UA0` | UPC-A | `upca` | no | |
| `UE0` | UPC-E | `upce` | no | |
| `2` | Interleaved 2 of 5 | `interleaved2of5` | no | |
| `2C` | ITF with mod-10 check digit | `interleaved2of5` + check | no | |
| `P` | Postnet | `postnet` | no | |
| `PL` | Planet | `planet` | no | |
| `J` | Japanese Postnet | `japanpost` | no | |
| `L` | Plessey (MSI-1) | `msi` | no | |
| `M` | MSI-3 | `msi` | no | |
| `2G` | German Post Code | custom | no | |
| `R14` / `RL` / `RS` / `RT` | RSS-14 family | `databaromni` / `databarlimited` / `databarstacked` / `databartruncated` | no | G-series/3842/2844 only. |
| `Q` (on `b`) | QR Code | `qrcode` | **YES** | See `b` command. |
| (other `b` selectors) | Aztec, Data Matrix, MaxiCode, PDF417 | `azteccode`, `datamatrix`, `maxicode`, `pdf417` | no | Specific syntaxes — consult manual. |

**Manual reference**: Table 1 p. 53. RSS-14 p. 58. 2D selectors p. 62–84.

---

## Print orientation summary (`ZB` / `ZT`)

Empirical behavior on ZD410 (203 dpi):

| Command | Effect on rendered canvas | Observed operator-facing result |
|---------|---------------------------|---------------------------------|
| `ZT` (default) | No transform. | Label reads right-side-up. |
| `ZB` | Rotate final canvas 180°. | Label reads right-side-up (compensates for how the printer pulls stock from the spool — the "bottom" of the bitmap exits the print head first). |

Equivalent to: draw everything in the logical (q × Q) buffer, then rotate 180° before returning the `PIL.Image` IF `ZB` was set.

**Interaction with `A p3` rotation**: `ZB` and the per-element rotation (`A`'s `p3`, `B`'s `p3`, etc.) COMPOSE. Example: `ZB` + `A ... 1 ...` = an `A` rotated 90° CW in logical space, plus the whole canvas flipped 180° at end = the text appears rotated 270° CW to the operator. Renderer should apply per-element rotation first (in logical space) and the ZB flip last.

---

## Referenced but deferred (not in MVP)

Brief notes for commands that appear in `contexto.md` / `explore` but are NOT exercised by the 7 MVP fixtures. Ship support when we have a fixture that demands them.

| Command | Purpose | Manual page | MVP action |
|---------|---------|:----------:|------------|
| `LO` | Line Draw Black: `LOx,y,w,h` — fill black rect. | 118 | If encountered: log a warning, draw the rect, continue. Easy add when needed. |
| `LW` | Line Draw White: `LWx,y,w,h` — erase (fill white) rect. | 120 | Same as `LO` but white. |
| `LE` | Line Draw XOR (reverse video rectangle). | 117 | Preferred by manual over `A…,R`; not in fixtures. Easy add. |
| `LS` | Line Draw Diagonal. | 119 | Rarely used — implement on demand. |
| `X` | Box Draw: `Xx,y,thick,xend,yend` — hollow rectangle. | 168 | Not seen because fixtures use `A…,R` for reverse-video boxes. Add when shipping-label fixtures appear. |
| `GW` | Direct Graphic Write (inline PCX/raw bitmap). | 110 | Requires PCX decoder — deferred. |
| `GG` | Print stored graphic by name. | 105 | Requires `GM` store support — deferred. |
| `GM` | Store Graphic (load PCX into printer memory). | 108 | Deferred together with `GG`/`GW`. |
| `FK` | Delete stored form. | 102 | We do not implement stored forms. Skip at parse time. |
| `FS` | Begin Store Form. | 104 | Skip block until `FE`. |
| `FE` | End Store Form. | 100 | Companion to `FS`. |
| `FR` | Retrieve stored form. | 103 | Deferred. |
| `FI` | Print form information (diagnostic). | 101 | Ignore. |
| `V` | Define variable (for stored forms). | 164 | Deferred with stored forms. |
| `C` | Counter. | 85 | Deferred with stored forms. |
| `I` | Character set selection. | 112 | Parse-only in MVP (respect default CP437). Full implementation = switch decoder at runtime. |
| `o` | Cancel software options. | 123 | Ignore for MVP. |
| `ZT` | Print direction top (default). | 170 | Handled together with `ZB`. |

If a user ships a fixture that uses a deferred command:
1. Renderer logs a `UnsupportedCommand` warning (name + source line).
2. Renderer SHOULD skip it (not crash). For `FS…FE` blocks, skip everything until the matching `FE`.
3. File a follow-up task citing which commands were hit.

---

## Known ambiguities / gaps

Documented here so the design phase doesn't re-derive them.

### R1 — Codepage / UTF-8 handling

The manual (p. 113) defaults to `I8,0,001` = 8-bit CP437. Source files may be authored in UTF-8. The physical printer reads bytes, so a UTF-8 en-dash `–` (bytes `0xE2 0x80 0x93`) prints as 3 CP437 glyphs (looks like `â\u0080\u0093` → rendered as `COo`-ish).

**Manual is unambiguous on encoding** (CP437 by default). The gap is that the manual doesn't explicitly warn UTF-8 authors. **MVP decision**: renderer MUST decode input bytes as CP437 (or Latin-1 fallback), NOT UTF-8. Document in README.

### R2 — Fonts 1–5 exact glyph bitmaps

Cell dimensions are specified (p. 44) but per-glyph bitmaps are NOT in the manual. Zebra's actual font files may or may not be redistributable.

**MVP decision** (from explore §6 R2): render any monospace TTF (DejaVu Sans Mono) into a locked-size cell that enforces the (W × H) metrics. Snapshot tests baseline against our own output.

### R3 — `A p7=R` reverse video

Manual says "R = reverse image" without specifying whether the background rectangle exactly hugs the character cell bounds or extends slightly. Empirically (from JPEGs), the rectangle hugs the exact (W × multiplier × len) × (H × multiplier) text bbox.

**MVP decision**: draw the rectangle as the exact bounding box of the scaled glyphs, no padding.

### R4 — `ZB` coordinate model

Manual does not state whether draw commands issued AFTER `ZB` use pre-flip or post-flip coordinates. Cross-reference with fixtures (`A22,8` appears in both `ZT` and `ZB` fixtures at visually similar positions) strongly suggests **pre-flip** (logical) coordinates.

**MVP decision**: treat all draw-command coordinates as logical; apply the 180° flip only once at `P` time.

### R5 — Code 128 subset-B forcing

Manual shows `1B` as "Code 128 mode B". BWIPP's `code128` auto-selects the optimal subset, which may encode the same payload differently at the bit level. Our goal is bit-buffer fidelity — same scan output, not identical bars.

**MVP decision**: pass `parse=true` to BWIPP. Bar-level drift vs. the physical printout is acceptable as long as a scanner reads the same payload. Document as a known visual-diff source.

### R6 — Empty strings

Fixtures (epl6, epl7) contain `A…,N,""`. Manual does not explicitly say this is legal. Empirically it is (the physical label has a blank gap).

**MVP decision**: parser accepts `""`, renderer draws nothing.

### R7 — Reverse-video + rotation

Manual shows `A…,R` examples at rotation 0 only. No example combines `p3 ≠ 0` with `p7 = R`.

**MVP decision**: the black background rectangle rotates together with the text (they're drawn as a single unit in the logical glyph raster, then rotated). Write a test fixture if we ever see rotated reverse-video in the wild.

### R8 — `S` and `D` semantics for a software renderer

Speed and density affect physical mechanics, not the bit buffer.

**MVP decision**: parse-only no-op, no warning.

### R9 — `A` Y-coordinate origin

Manual calls `p2` "Vertical start position (Y) in dots" without specifying whether it's the top of the character cell or a font baseline. Reading p. 44 in context ("Total character size is W × H dots"), it is consistent with **top-left of the character cell**.

**MVP decision**: treat `(p1, p2)` as the top-left of the scaled cell. Confirm with a fixture-driven alignment test (`A`-then-`B` on the same Y) once the renderer runs.

### R10 — Line endings

Manual's examples use `↵` (LF). Real-world EPL2 often uses CRLF from Windows-based label designers.

**MVP decision**: parser accepts both LF and CRLF. Internally strip trailing `\r` before tokenizing.

### R11 — Non-zero `R` offset

All MVP fixtures send `R0,0`. If a production fixture sends `R100,50`, every X/Y in subsequent commands must be offset by +100/+50.

**MVP decision**: store `ref_point` in render state, add it at draw time. Test with a synthetic fixture.

### R12 — QR Code "Japanese printers only" clause

Manual p. 83 restricts the `b…Q` form to Japanese models. Empirically the ZD410 (a US/global model) prints QR from this exact syntax with no error.

**MVP decision**: the restriction is a manual gap (likely documentation lag — QR support was added to the general firmware line). Treat `b…Q` as universally valid.

### R13 — Manual vs. real printer firmware drift

The PDF is from 2013 (Rev. A, 12/16/13). The ZD410 launched later (2014+). Minor syntax details (default QR parameters, Code 128 subset defaults, reverse-video rectangle padding) may have silently shifted. When in doubt, favor the observed behavior of the 7 MVP fixtures over strict manual compliance.
