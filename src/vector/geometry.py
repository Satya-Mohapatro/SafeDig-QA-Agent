from typing import List, Dict, Any, Tuple, Optional
from shapely.geometry import (
    LineString, Polygon, Point, MultiLineString,
    GeometryCollection, box
)
from shapely.ops import unary_union

def drawing_to_shapely(drawing: Dict[str, Any]) -> Optional[Any]:
    """Convert a PyMuPDF drawing dict to a Shapely geometry.
    
    Handles:
    - 'l': line segments (p1 -> p2)
    - 're': rectangle primitives
    - 'c': bezier curves (approximated as direct p1->p4 chord for spatial filtering)
    - 'qu': quad/quadrilateral path
    
    For multi-segment paths, returns MultiLineString to allow
    accurate AOI spatial intersection checks.
    """
    items = drawing.get("items", [])
    rect = drawing.get("rect")

    if not items:
        # Fall back to drawing rect bbox
        if rect:
            return box(rect.x0, rect.y0, rect.x1, rect.y1)
        return None

    lines = []
    for it in items:
        cmd = it[0]
        try:
            if cmd == "l":  # line segment (p1, p2)
                p1, p2 = it[1], it[2]
                if (p1.x, p1.y) != (p2.x, p2.y):  # skip degenerate points
                    lines.append(LineString([(p1.x, p1.y), (p2.x, p2.y)]))
            elif cmd == "re":  # rectangle
                r = it[1]
                if r.width > 0 and r.height > 0:
                    lines.append(box(r.x0, r.y0, r.x1, r.y1).boundary)
            elif cmd == "c":  # bezier curve - sample 4 evenly-spaced chord points
                p1, cp1, cp2, p4 = it[1], it[2], it[3], it[4]
                # De Casteljau approximation at t=0, 0.33, 0.67, 1.0
                def bezier(t):
                    mt = 1 - t
                    x = mt**3*p1.x + 3*mt**2*t*cp1.x + 3*mt*t**2*cp2.x + t**3*p4.x
                    y = mt**3*p1.y + 3*mt**2*t*cp1.y + 3*mt*t**2*cp2.y + t**3*p4.y
                    return (x, y)
                pts = [bezier(t) for t in [0, 0.25, 0.5, 0.75, 1.0]]
                lines.append(LineString(pts))
            elif cmd == "qu":  # quadrilateral
                quad = it[1]
                pts = [(quad.ul.x, quad.ul.y), (quad.ur.x, quad.ur.y),
                       (quad.lr.x, quad.lr.y), (quad.ll.x, quad.ll.y)]
                lines.append(Polygon(pts).boundary)
        except Exception:
            continue

    if not lines:
        if rect:
            return box(rect.x0, rect.y0, rect.x1, rect.y1)
        return None

    valid_lines = [l for l in lines if l is not None and not l.is_empty]
    if len(valid_lines) == 1:
        return valid_lines[0]
    elif len(valid_lines) > 1:
        try:
            return unary_union(valid_lines)
        except Exception:
            return MultiLineString([l for l in valid_lines if isinstance(l, LineString)])

    return None
