# labelscope

SDK y visor en Python para previsualizar etiquetas de impresoras térmicas a partir de su código fuente, sin necesidad de enviarlas a la impresora física. El foco inicial es **EPL2**, con arquitectura preparada para agregar **ZPL** (y potencialmente TSPL, DPL) en el futuro.

## Contexto y motivación

El proyecto nace de la necesidad de debuggear y previsualizar etiquetas EPL2 generadas para impresoras Zebra (ZD410) y compatibles en flujos de trabajo de ClassicAlpaca / ClassicalAlpacaPeru. Hoy no existe un equivalente libre y local de Labelary (que solo soporta ZPL) para EPL2.

El SDK debe poder recibir un string EPL2 y devolver una imagen (`PIL.Image`) fiel a lo que imprimiría físicamente la etiqueta, respetando:
- Dimensiones de la etiqueta (comandos `q`, `Q`) y densidad en dots por mm (203 dpi ≈ 8 dots/mm por defecto).
- Posicionamiento absoluto (x, y en dots) de cada elemento.
- Rotación (0°, 90°, 180°, 270°).
- Escalado horizontal y vertical de texto y barcodes.
- Múltiples copias (`P` command) solo como metadata del render, no como duplicación visual.

## Nombre y scope

- **Nombre del paquete**: `labelscope`
- **Nombre del repo**: `labelscope`
- **Org GitHub**: xpertik
- **Licencia**: **Apache 2.0**

El nombre es intencionalmente agnóstico del lenguaje de impresión para permitir crecer a ZPL/TSPL sin renombrar.

## Arquitectura propuesta

```
labelscope/
├── labelscope/
│   ├── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── canvas.py        # Wrapper sobre Pillow; maneja dots, mm, DPI
│   │   ├── geometry.py      # Conversiones dots↔mm, rotación, bounding boxes
│   │   ├── fonts.py         # Registro de fuentes bitmap-like (DejaVu Mono por defecto)
│   │   └── barcodes.py      # Wrapper sobre treepoem / python-barcode
│   ├── epl2/
│   │   ├── __init__.py
│   │   ├── parser.py        # Tokenizer + parser line-based
│   │   ├── commands.py      # Clases/dataclasses por cada comando EPL2
│   │   └── renderer.py      # Ejecuta el AST sobre un Canvas
│   ├── zpl/                 # (futuro) misma estructura que epl2/
│   └── cli.py               # CLI opcional: `labelscope render input.epl -o out.png`
├── tests/
│   ├── fixtures/            # archivos .epl de muestra
│   └── snapshots/           # PNGs de referencia para regression tests
├── examples/
├── pyproject.toml
├── README.md
└── CLAUDE.md                # este archivo
```

### Decisiones clave

1. **Pillow como backend de render**. No SVG, no Cairo. Pillow produce raster directo que coincide con lo que la impresora genera físicamente.
2. **DPI configurable**, con 203 como default (cubre ZD410 y la mayoría de impresoras desktop). Soportar también 300 dpi para modelos industriales.
3. **Parser separado del renderer**. El parser produce una lista de `Command` (dataclasses) y el renderer los aplica sobre un `Canvas`. Esto facilita testing y permite reutilizar el parser para análisis/linting.
4. **Fuentes**: EPL2 define fuentes bitmap 1-5 con métricas específicas. Aproximar con TTF monoespaciada (DejaVu Sans Mono) escalada según la tabla del manual Zebra EPL2. Documentar que es una aproximación, no pixel-perfect.
5. **Barcodes**: `treepoem` como primera opción (cubre casi todas las simbologías EPL2 vía BWIPP). Fallback a `python-barcode` para casos simples si queremos evitar la dependencia de Ghostscript.

## Comandos EPL2 a soportar en el MVP

Prioridad 1 (cubre ~80% de etiquetas reales):
- `N` — clear image buffer
- `q` — label width (dots)
- `Q` — label height + gap
- `A` — ASCII text
- `B` — barcode
- `LO` — line draw (black)
- `LW` — line draw (white / erase)
- `X` — box draw
- `P` — print (solo capturamos count como metadata)

Prioridad 2:
- `GW` — direct graphic write (raster bytes)
- `GG` — print graphic from memory
- `GM` — store graphic in memory
- `D` — density
- `R` — reference point
- `ZT` / `ZB` — print orientation (top/bottom)
- `I` — character set / codepage

Prioridad 3 (nice-to-have):
- `FK`, `FS`, `FE`, `FI`, `FR` — form storage
- `V` — variable input (prompt)
- `C` — counter
- `o` — offset commands

## API pública propuesta

```python
from labelscope.epl2 import Renderer

renderer = Renderer(dpi=203)
image = renderer.render(epl_source)  # returns PIL.Image
image.save("preview.png")

# O directo desde archivo
image = renderer.render_file("label.epl")

# Con opciones
image = renderer.render(
    epl_source,
    dpi=300,
    background="white",
    show_grid=False,
)
```

CLI:
```bash
labelscope render label.epl -o preview.png --dpi 203
labelscope render label.epl --show   # abre en viewer del OS
labelscope validate label.epl        # parsea sin renderizar, reporta errores
```

## Stack técnico

- **Python**: 3.10+ (uso de `match`/`case` en el parser)
- **Dependencias core**:
  - `Pillow` (render)
  - `treepoem` (barcodes, requiere Ghostscript instalado)
- **Dev**:
  - `pytest` + `pytest-regressions` (snapshot tests de imágenes)
  - `ruff` (lint + format)
  - `mypy` (type checking)
- **Build**: `hatchling` o `pdm-backend` vía `pyproject.toml`

## Estado actual

Proyecto en fase de planificación. No hay código aún. Pasos inmediatos:

1. [ ] `git init` y crear estructura de carpetas
2. [ ] `pyproject.toml` con metadata y deps
3. [ ] Esqueleto de `core/canvas.py` y `core/geometry.py`
4. [ ] Parser EPL2 con comandos de Prioridad 1
5. [ ] Renderer básico: `N`, `q`, `Q`, `A`, `LO`, `X`
6. [ ] Tests con 3-5 etiquetas fixture reales (de ClassicAlpaca)
7. [ ] Agregar barcodes (`B`)
8. [ ] Agregar gráficos raster (`GW`)
9. [ ] CLI
10. [ ] README con ejemplos y publicación a PyPI

## Contexto del autor

Jhonatan trabaja con impresoras Zebra ZD410 en ClassicAlpaca y ClassicalAlpacaPeru. Tiene código EPL2 real generado previamente (UPC-A para productos, etiquetas de envío) que puede servir como fixtures de prueba. Stack habitual: Django 5.2, Python, Ubuntu para desarrollo. Prefiere convenciones claras y estructura desde el día uno (ej. módulo `config` en Django).

## Convenciones de código

- Type hints en todo el código público.
- Dataclasses para representar comandos del AST.
- Docstrings estilo Google.
- Nombres de variables y comentarios en inglés (código) — README y docs de usuario pueden tener versión en español.
- Los comandos EPL2 se modelan 1:1 como clases con el nombre del comando (`ACommand`, `BCommand`, etc.) para que el mapeo con el manual Zebra sea trivial.

## Referencias

- Manual EPL2 de Zebra: "EPL2 Programmer's Manual" (buscar en zebra.com/manuals)
- BWIPP (Barcode Writer in Pure PostScript): http://bwipp.terryburton.co.uk/
- Labelary (inspiración, solo ZPL): http://labelary.com/
- Pillow docs: https://pillow.readthedocs.io/

## Notas para Claude Code

- Antes de escribir código del parser, pedir al usuario 2-3 archivos `.epl` reales como fixtures — es más eficiente que adivinar casos.
- El renderer debe ser **determinístico**: misma entrada → misma imagen bit-a-bit. Esto habilita snapshot testing confiable.
- No asumir que los clientes tienen Ghostscript instalado; `treepoem` debe ser dependencia opcional (`labelscope[barcodes]`).
- Cuando se agregue ZPL, el `core/` ya debe estar generalizado — evitar hardcodear supuestos de EPL2 (ej. orden de comandos, origen del sistema de coordenadas) en `core/`.
