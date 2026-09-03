from typing import List, Dict, Any, Tuple, Optional
import math

def normalize_color_to_rgb(color: Any) -> Optional[Tuple[int, int, int]]:
    """Normalize a PyMuPDF color value to an (R, G, B) integer tuple (0-255).
    
    Handles:
    - None / missing -> None
    - float (greyscale 0.0-1.0)
    - 1-tuple (greyscale)
    - 3-tuple (RGB 0-1 floats or 0-255 ints)
    - 4-tuple (CMYK 0-1 floats)
    """
    if color is None:
        return None
    if isinstance(color, (int, float)):
        val = int(round(color * 255)) if color <= 1.0 else int(color)
        return (val, val, val)
    if isinstance(color, (list, tuple)):
        if len(color) == 1:
            val = int(round(color[0] * 255)) if color[0] <= 1.0 else int(color[0])
            return (val, val, val)
        elif len(color) == 3:
            # PyMuPDF always returns 0.0-1.0 float triples for RGB
            if all(0.0 <= c <= 1.0 for c in color):
                return (int(round(color[0] * 255)),
                        int(round(color[1] * 255)),
                        int(round(color[2] * 255)))
            else:
                return (int(color[0]), int(color[1]), int(color[2]))
        elif len(color) == 4:
            # CMYK: all values 0.0-1.0
            c, m, y, k = color
            r = int(round(255 * (1.0 - c) * (1.0 - k)))
            g = int(round(255 * (1.0 - m) * (1.0 - k)))
            b = int(round(255 * (1.0 - y) * (1.0 - k)))
            return (r, g, b)
    return None

def color_distance(rgb1: Tuple[int,int,int], rgb2: Tuple[int,int,int]) -> float:
    """Perceptual-weighted Euclidean distance in RGB space."""
    r1, g1, b1 = rgb1
    r2, g2, b2 = rgb2
    # Weighted by human eye sensitivity (ITU-R BT.709 luma coefficients)
    dr = (r1 - r2) * 0.2126
    dg = (g1 - g2) * 0.7152
    db = (b1 - b2) * 0.0722
    return math.sqrt(dr*dr + dg*dg + db*db)

def match_stroke_color(
    stroke_color: Any,
    target_rgb: Tuple[int, int, int],
    tolerance: int = 35
) -> bool:
    """Check if a raw PyMuPDF stroke color matches the target within tolerance.
    
    Uses perceptual-weighted RGB distance. Tolerance is in 0-255 space.
    """
    rgb = normalize_color_to_rgb(stroke_color)
    if rgb is None:
        return False
    dist = color_distance(rgb, target_rgb)
    return dist <= tolerance

def filter_drawings_by_style(
    drawings: List[Dict[str, Any]],
    target_rgb: Tuple[int, int, int],
    min_width: float = 0.4,
    max_width: float = 12.0,
    tolerance: int = 40,
    exclude_dashed: bool = False
) -> List[Dict[str, Any]]:
    """Filter PyMuPDF drawings list by stroke color and line width.
    
    Args:
        drawings: list of drawing dicts from page.get_drawings()
        target_rgb: target stroke color as (R, G, B) ints 0-255
        min_width: minimum line width in points to include
        max_width: maximum line width in points to include
        tolerance: color match tolerance in perceptual RGB space
        exclude_dashed: if True, skip dashed/dotted drawings (e.g. to avoid picking AOI boundary itself)
    """
    matched = []
    for d in drawings:
        color = d.get("color") or d.get("fill")
        if not color:
            continue

        w_val = d.get("width")
        width = float(w_val) if w_val is not None else 1.0

        if not (min_width <= width <= max_width):
            continue

        if exclude_dashed:
            dashes = d.get("dashes")
            if dashes and dashes != "[] 0":
                continue

        if match_stroke_color(color, target_rgb, tolerance):
            matched.append(d)
    return matched
