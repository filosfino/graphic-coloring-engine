# Graphic Coloring Engine
Automatic text coloring for 2d graphic designs

`Text` elements should have enough contrast with their background. To be recognized as a text, this library uses [WCAG standard](https://www.w3.org/TR/WCAG20/#contrast-ratiodef) for color contrast calculation.

[![lint & test](https://github.com/filosfino/graphic-coloring-engine/actions/workflows/python-package.yml/badge.svg?branch=main)](https://github.com/filosfino/graphic-coloring-engine/actions/workflows/python-package.yml)
[![publish](https://github.com/filosfino/graphic-coloring-engine/actions/workflows/python-publish.yml/badge.svg?branch=main)](https://github.com/filosfino/graphic-coloring-engine/actions/workflows/python-publish.yml)

## Usage
```
poetry add graphic-coloring-engine
```

```python
from graphic-coloring-engine.core import ColoringEngine

# construct your layout

engine = ColoringEngine(layout, seed, constants)
color_schemes = engine.colorize()
```

## How
1. Collision map is calculated for all elements.
2. Collect usable colors for uncolorized elements, which could be from either colorized elements on canvas or external passed in colors.
3. For those elements need to be colorized, try colors one by one with minimum contrast constraints with elements it collides. Constraints can be passed from external.
4. Output certin amount of color schemes.
