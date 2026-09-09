"""AOI (Area of Interest / Dig-Site Boundary) Detector.

Pipeline (per spec):
  PDF
   ├── Stage 1: PDF vector analysis  → explicit dashed / solid-stroke boundary
   ├── Stage 2: CV contour analysis  → raster-image boundary (red/magenta shapes in embedded image)
   └── Stage 3: Map-region detection → content-based map canvas inference
           ↓
     MAP_REGION DETECTOR   (excludes legend, footer, header)
           ↓
     DIG_BOUNDARY DETECTOR
      ├── circle (64-point circular poly → GeometryType.CIRCLE)
      ├── rectangle / polygon (vector or CV)
           ↓
      AOI GEOMETRY
           ↓
      AOI VALIDATOR (bounds, area, legend exclusion)
           ↓
      FINAL DIG_AOI

Detection priority (per spec §8):
  1. PDF vector dashed boundary  (colour-agnostic, scored)
  2. PDF vector solid-stroke coloured boundary (red/magenta)
  3. CV raster contour of red/magenta shape in rendered image
  4. Map-region fallback  (content-derived, NOT hardcoded page fraction)
"""

import math
import pymupdf
import cv2
import numpy as np
from typing import List, Optional, Tuple, Dict, Any
from shapely.geometry import Polygon, Point, box
from src.domain.aoi import AOI
from src.domain.enums import AOIDetectionMethod, GeometryType
from src.config.logging import logger


# ---------------------------------------------------------------------------
# Coordinate helpers
# ---------------------------------------------------------------------------

def _unrotated_to_visual(rect: pymupdf.Rect, rotation: int,
                          mediabox: pymupdf.Rect) -> pymupdf.Rect:
    """Map unrotated drawing coordinates → visual/rendered page coordinates."""
    mw, mh = mediabox.width, mediabox.height
    if rotation == 0:
        return pymupdf.Rect(rect)
    elif rotation == 90:
        r = pymupdf.Rect(mh - rect.y1, rect.x0, mh - rect.y0, rect.x1)
        r.normalize()
        return r
    elif rotation == 180:
        r = pymupdf.Rect(mw - rect.x1, mh - rect.y1, mw - rect.x0, mh - rect.y0)
        r.normalize()
        return r
    elif rotation == 270:
        r = pymupdf.Rect(rect.y0, mw - rect.x1, rect.y1, mw - rect.x0)
        r.normalize()
        return r
    return pymupdf.Rect(rect)


# ---------------------------------------------------------------------------
# Stage 3 helper: derive MAP_REGION from vector frame or text-block analysis
# ---------------------------------------------------------------------------

def _find_vector_map_frame(page: pymupdf.Page) -> Optional[List[float]]:
    """Scan drawings on page for an explicit rectangular map frame / viewport.
    
    Engineering maps (e.g. SGN, NGED, WWU, Welsh Water, Thames Water) draw explicit viewport
    borders separating map cartography from the legend, header, and footer.
    Supports both rectangle drawing primitives and orthogonal 4-line boundary frames.
    """
    mediabox = page.mediabox
    mw, mh = mediabox.width, mediabox.height
    page_area = mw * mh
    drawings = page.get_drawings()
    candidates = []
    
    h_lines = []  # (y, x0, x1)
    v_lines = []  # (x, y0, y1)
    
    for d in drawings:
        dashes = d.get("dashes")
        if dashes and str(dashes).strip() not in ("", "[] 0", "[]"):
            continue  # ignore dashed lines
            
        r = d.get("rect")
        if not r:
            continue
            
        area = r.width * r.height
        # A map frame viewport occupies between 25% and 92% of the page area
        if 0.25 * page_area <= area <= 0.92 * page_area:
            items = d.get("items", [])
            is_rect = any(it[0] in ('re', 'qu') for it in items) or len(items) == 4
            if is_rect:
                candidates.append((area, [r.x0, r.y0, r.x1, r.y1]))
                
        # Collect long solid horizontal and vertical lines (CAD viewport borders like Clean_Water.pdf)
        if r.width >= 0.50 * mw and r.height <= 3.5:
            h_lines.append((r.y0, r.x0, r.x1))
        elif r.height >= 0.40 * mh and r.width <= 3.5:
            v_lines.append((r.x0, r.y0, r.y1))
            
    # Check if orthogonal lines form an enclosed viewport
    if len(h_lines) >= 2 and len(v_lines) >= 2:
        top_h = min(h_lines, key=lambda l: l[0])
        candidate_bottoms = [l for l in h_lines if 0.50 * mh < l[0] < 0.95 * mh]
        if candidate_bottoms:
            bottom_h = min(candidate_bottoms, key=lambda l: l[0])
            left_v = min(v_lines, key=lambda l: l[0])
            right_v = max(v_lines, key=lambda l: l[0])
            
            x0 = max(left_v[0], min(top_h[1], bottom_h[1]))
            y0 = top_h[0]
            x1 = min(right_v[0], max(top_h[2], bottom_h[2]))
            y1 = bottom_h[0]
            
            line_box_area = (x1 - x0) * (y1 - y0)
            if 0.25 * page_area <= line_box_area <= 0.92 * page_area:
                candidates.append((line_box_area, [x0, y0, x1, y1]))
                
    if candidates:
        # Sort by area ascending: pick the SMALLEST qualifying frame.
        # The tightest inner viewport (map cartography area) is always smaller
        # than any decorative outer border. Both may qualify under the 25-92% rule,
        # but the inner viewport is the correct reference for AOI derivation.
        candidates.sort(key=lambda x: x[0])
        best_box = candidates[0][1]
        logger.info(f"Detected explicit vector map frame: [{best_box[0]:.1f}, {best_box[1]:.1f}, {best_box[2]:.1f}, {best_box[3]:.1f}]")
        return best_box
        
    return None

def _find_raster_map_frame(page: pymupdf.Page) -> Optional[List[float]]:
    """Detect complete 4-sided cartographic box on raster maps (e.g. BT.pdf)."""
    try:
        mw, mh = page.mediabox.width, page.mediabox.height
        mat = pymupdf.Matrix(1.0, 1.0)
        pix = page.get_pixmap(matrix=mat, colorspace=pymupdf.csGRAY)
        arr = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width)
        
        # 1. Bottom separator (legend separator)
        sep_y = None
        for y in range(int(mh * 0.50), int(mh * 0.85)):
            if np.sum(arr[y, :] < 80) > mw * 0.65:
                sep_y = y
                break
                
        if not sep_y:
            return None
            
        # 2. Top border (between 4% and 20% of mh)
        top_y = None
        for y in range(int(mh * 0.04), int(mh * 0.20)):
            if np.sum(arr[y, int(mw * 0.15):int(mw * 0.85)] < 80) > (mw * 0.70) * 0.80:
                top_y = y
                break
                
        # 3. Left and Right borders
        left_x = None
        y_start = (top_y or int(mh * 0.10)) + 50
        y_end = sep_y - 50
        span = y_end - y_start
        for x in range(int(mw * 0.02), int(mw * 0.15)):
            if np.sum(arr[y_start:y_end, x] < 80) > span * 0.80:
                left_x = x
                break
                
        right_x = None
        for x in range(int(mw * 0.98), int(mw * 0.85), -1):
            if np.sum(arr[y_start:y_end, x] < 80) > span * 0.80:
                right_x = x
                break
                
        if top_y and left_x and right_x and sep_y:
            logger.info(f"Detected complete raster cartographic frame: [{left_x:.1f}, {top_y:.1f}, {right_x:.1f}, {sep_y:.1f}]")
            return [float(left_x), float(top_y), float(right_x), float(sep_y)]
        elif sep_y:
            logger.info(f"Detected raster legend separator at y={sep_y:.1f}")
            return [mw * 0.02, mh * 0.03, mw * 0.97, float(sep_y - 2)]
    except Exception as e:
        logger.debug(f"Error finding raster map frame: {e}")
    return None

def _derive_map_region(page: pymupdf.Page) -> List[float]:
    """Derive the actual map-canvas bounding box.
    
    1. First checks for an explicit vector map frame viewport.
    2. Falls back to text block analysis (excluding legend/footer/header).
    3. Uses classical raster map frame analysis for raster plans.
    
    Returns [x0, y0, x1, y1] in unrotated (mediabox) coordinates.
    """
    # 1. Check for explicit vector map frame
    vec_frame = _find_vector_map_frame(page)
    if vec_frame:
        return vec_frame

    mediabox = page.mediabox
    mw, mh = mediabox.width, mediabox.height
    rotation = page.rotation
    pw, ph = page.rect.width, page.rect.height   # visual dimensions

    is_landscape = mw > mh

    # Get text blocks in visual space
    blocks = page.get_text("blocks")  # (x0, y0, x1, y1, text, block_no, block_type)

    if not blocks:
        # Check for raster map frame first (e.g. BT.pdf)
        r_frame = _find_raster_map_frame(page)
        if r_frame:
            return r_frame
            
        # No text at all — return default canvas.
        if is_landscape:
            return [mw * 0.01, mh * 0.02, mw * 0.82, mh * 0.97]
        else:
            return [mw * 0.02, mh * 0.03, mw * 0.97, mh * 0.82]

    # In visual space, identify footer and legend regions
    # Footer = bottom 25% of visual height; legend = right 28% for landscape
    footer_thresh_visual = ph * 0.75      # anything below this y is footer
    legend_thresh_visual = pw * 0.72      # anything to right of this x is legend (landscape)
    header_thresh_visual = ph * 0.05      # anything above this y is header

    # Collect y_tops of blocks that are in the "middle" (candidate footer boundary)
    middle_block_tops = []
    right_block_lefts = []

    for b in blocks:
        bx0_v, by0_v, bx1_v, by1_v = b[0], b[1], b[2], b[3]
        text = b[4].strip()
        if not text:
            continue

        # Header blocks: skip
        if by1_v < header_thresh_visual:
            continue

        # Footer blocks (in bottom 25%): record their top as the footer boundary
        if by0_v > footer_thresh_visual:
            middle_block_tops.append(by0_v)

        # Legend blocks for landscape (right 28%): record their left
        if is_landscape and bx0_v > legend_thresh_visual:
            right_block_lefts.append(bx0_v)

    # The map canvas ends just before the topmost footer block
    # Convert visual top-of-footer → unrotated coordinate
    if middle_block_tops:
        footer_top_visual = min(middle_block_tops)  # topmost footer block
        # Add 2pt buffer
        footer_top_visual = max(footer_top_visual - 2.0, ph * 0.50)
    else:
        footer_top_visual = ph * 0.82  # safe default

    # Also check if a physical raster map frame is detected
    r_frame = _find_raster_map_frame(page)
    if r_frame and r_frame[3] < footer_top_visual:
        footer_top_visual = max(ph * 0.50, r_frame[3] - 2.0)
        logger.info(f"Clamping footer top to raster map frame: y1={footer_top_visual:.1f}")

    if is_landscape and right_block_lefts:
        legend_left_visual = min(right_block_lefts)
        legend_left_visual = max(legend_left_visual - 2.0, pw * 0.50)
    else:
        legend_left_visual = pw * 0.82 if is_landscape else pw * 0.97

    # Convert visual canvas bounds → unrotated (mediabox) coordinates
    # For rotation=0: visual == unrotated
    # For rotation=90: visual_x → un_y, visual_y → un_x (approx)
    # We use a simplified approach: compute the unrotated rect of the visual canvas rect
    vis_canvas = pymupdf.Rect(
        pw * 0.01,
        header_thresh_visual,
        legend_left_visual,
        footer_top_visual
    )

    if rotation == 0:
        un = vis_canvas
    elif rotation == 90:
        # visual(x,y) → unrotated: x_un = y_vis, y_un = mh - x_vis
        un = pymupdf.Rect(
            vis_canvas.y0,
            mh - vis_canvas.x1,
            vis_canvas.y1,
            mh - vis_canvas.x0
        )
        un.normalize()
    elif rotation == 180:
        un = pymupdf.Rect(
            mw - vis_canvas.x1,
            mh - vis_canvas.y1,
            mw - vis_canvas.x0,
            mh - vis_canvas.y0
        )
        un.normalize()
    elif rotation == 270:
        un = pymupdf.Rect(
            vis_canvas.y0,
            mw - vis_canvas.x1,
            vis_canvas.y1,
            mw - vis_canvas.x0
        )
        un.normalize()
    else:
        un = vis_canvas

    logger.debug(
        f"MAP_REGION derived: unrotated=[{un.x0:.1f},{un.y0:.1f},{un.x1:.1f},{un.y1:.1f}] "
        f"(footer_top_visual={footer_top_visual:.1f}, legend_left_visual={legend_left_visual:.1f})"
    )

    return [un.x0, un.y0, un.x1, un.y1]


# ---------------------------------------------------------------------------
# Circle detection helper
# ---------------------------------------------------------------------------

def _detect_circle_from_items(items: List[Any]) -> Optional[Tuple[float, float, float]]:
    """If drawing items form a circular polygon, return (cx, cy, radius).

    A circle drawn as 64 line-segments ('l' commands) is the standard
    representation from mapping software (NGED, UKPN, WWU, SGN, etc.).
    We collect all endpoint coordinates and fit a circle by computing
    the centroid and mean radius.

    Returns None if shape does not pass circularity threshold.
    """
    pts = []
    for it in items:
        if it[0] == 'l':
            pts.append((it[1].x, it[1].y))
            pts.append((it[2].x, it[2].y))
        elif it[0] == 'c':   # bezier — sample endpoints
            pts.append((it[1].x, it[1].y))
            pts.append((it[4].x, it[4].y))

    if len(pts) < 8:
        return None

    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    cx = (min(xs) + max(xs)) / 2.0
    cy = (min(ys) + max(ys)) / 2.0
    radii = [math.hypot(p[0] - cx, p[1] - cy) for p in pts]
    avg_r = sum(radii) / len(radii)
    min_r = min(radii)
    max_r = max(radii)

    if avg_r < 5.0:
        return None  # degenerate

    # Circularity check: all radii within 15% of mean
    if max_r - min_r > avg_r * 0.15:
        return None

    # Aspect ratio of bounding box must be close to 1.0
    rx = (max(xs) - min(xs)) / 2.0
    ry = (max(ys) - min(ys)) / 2.0
    aspect = rx / (ry or 1.0)
    if not (0.85 < aspect < 1.15):
        return None

    return (cx, cy, avg_r)


def _circle_to_coords(cx: float, cy: float, r: float,
                       n_pts: int = 64) -> List[Tuple[float, float]]:
    """Generate polygon approximation of a circle with n_pts points."""
    coords = []
    for i in range(n_pts):
        theta = 2.0 * math.pi * i / n_pts
        coords.append((cx + r * math.cos(theta), cy + r * math.sin(theta)))
    coords.append(coords[0])  # close
    return coords


# ---------------------------------------------------------------------------
# Stage 1: Vector boundary detection (dashed + solid)
# ---------------------------------------------------------------------------

def _score_vector_drawings(drawings: List[Dict], rotation: int,
                             mediabox: pymupdf.Rect,
                             page_rect: pymupdf.Rect
                             ) -> List[Tuple[int, Dict, pymupdf.Rect, pymupdf.Rect]]:
    """Score all vector drawings as potential AOI boundaries.

    Returns list of (score, drawing_dict, raw_unrotated_rect, visual_rect)
    sorted descending by score.
    """
    pw, ph = page_rect.width, page_rect.height
    candidates = []

    for d in drawings:
        raw_rect = d.get("rect")
        if not raw_rect:
            continue

        dashes = d.get("dashes")
        has_dashes = bool(dashes and str(dashes).strip() not in ("", "[] 0", "[]"))
        items = d.get("items", [])
        num_items = len(items)
        width_pt = d.get("width") or 0.0

        # Map unrotated → visual for size/position filtering
        vis_rect = _unrotated_to_visual(raw_rect, rotation, mediabox)
        vw, vh = vis_rect.width, vis_rect.height
        vx0, vy0, vx1, vy1 = vis_rect.x0, vis_rect.y0, vis_rect.x1, vis_rect.y1

        # --- Size filters (applied in visual space) ---
        if vw < 25 or vh < 25:
            continue  # too tiny (legend swatch)
        if vw > pw * 0.96 and vh > ph * 0.96:
            continue  # full-page border — skip

        # --- Position filters ---
        # Skip drawings entirely in the top 4% (header) or bottom 20% (legend/footer)
        if vy1 < ph * 0.04 or vy0 > ph * 0.82:
            continue
        if vx1 < pw * 0.01 or vx0 > pw * 0.88:
            continue

        # --- Colour analysis ---
        raw_c = d.get("color") or d.get("fill")
        is_red = False
        is_magenta = False
        is_yellow = False
        color_score = 0
        if raw_c and len(raw_c) >= 3:
            max_v = max(raw_c)
            scale = 255.0 if max_v <= 1.0 else 1.0
            rc = raw_c[0] * scale
            gc = raw_c[1] * scale
            bc = raw_c[2] * scale
            # Magenta/Purple (UKPN, SGN, Cadent, WWU)
            if rc > 140 and gc < 100 and bc > 140:
                is_magenta = True
                color_score = 50
            # Yellow/Gold (NGED/WPD)
            elif rc > 180 and gc > 150 and bc < 80:
                is_yellow = True
                color_score = 40
            # Red (GTC site boundary, some water)
            elif rc > 160 and gc < 90 and bc < 90:
                is_red = True
                color_score = 35

        # --- Score calculation ---
        if has_dashes:
            # Primary detection path: dashed boundary
            score = 100  # base
            score += min(num_items * 2, 80)   # more segments → more complex shape
            score += min(int(vw + vh), 200)    # larger = more likely site boundary
            if width_pt >= 1.5:
                score += 20
            if num_items >= 16:
                score += 30  # likely circle/polygon
            score += color_score
        else:
            # Secondary: solid-stroke coloured boundary
            # Only consider if clearly coloured (red/magenta) and reasonably large
            if not (is_red or is_magenta):
                continue  # solid non-coloured drawings are not AOI boundaries
            score = 70   # lower base than dashed
            score += min(num_items * 1, 40)
            score += min(int(vw + vh), 150)
            if width_pt >= 1.5:
                score += 15
            if num_items >= 4:
                score += 20  # closed shape
            score += color_score

        candidates.append((score, d, raw_rect, vis_rect))

    candidates.sort(key=lambda x: x[0], reverse=True)
    return candidates


# ---------------------------------------------------------------------------
# Stage 2: CV raster contour detection
# ---------------------------------------------------------------------------

def _detect_boundary_via_cv(page: pymupdf.Page,
                              map_region: List[float],
                              pw: float, ph: float
                              ) -> Optional[Tuple[List[Tuple[float, float]], str]]:
    """Detect a red or magenta dig-site boundary in the rendered page image.

    Returns (polygon_coords_in_pdf_pts, colour_label) or None if nothing
    passes the quality filters.

    Polygon coords are in UNROTATED (mediabox) PDF point space.
    """
    dpi = 150  # sufficient for contour detection without huge memory use
    scale = dpi / 72.0  # pts → pixels

    pix = page.get_pixmap(dpi=dpi, alpha=False)
    img_arr = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w, 3)
    img_bgr = cv2.cvtColor(img_arr, cv2.COLOR_RGB2BGR)
    img_hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)

    ih, iw = img_bgr.shape[:2]

    # Map-region pixel bounds (clip search to avoid legend/footer)
    mr_x0 = int(max(0, map_region[0] * scale))
    mr_y0 = int(max(0, map_region[1] * scale))
    mr_x1 = int(min(iw, map_region[2] * scale))
    mr_y1 = int(min(ih, map_region[3] * scale))

    results = []

    for colour, h_lo, h_hi, s_lo, v_lo, k_size, label in [
        # (colour, H_lo, H_hi, S_lo, V_lo, k_size, label)
        ("red_low",  0,  12, 110, 100, 7, "red"),
        ("red_high", 168, 180, 110, 100, 7, "red"),
        ("magenta", 138, 168, 90, 90, 9, "magenta"),
        ("yellow",   18,  38, 75, 75, 15, "yellow"),
        ("orange",   10,  20, 90, 90, 11, "orange"),
    ]:
        mask = cv2.inRange(img_hsv, (h_lo, s_lo, v_lo), (h_hi, 255, 255))

        # Restrict mask to map region
        full_mask = np.zeros_like(mask)
        if mr_x1 > mr_x0 and mr_y1 > mr_y0:
            full_mask[mr_y0:mr_y1, mr_x0:mr_x1] = mask[mr_y0:mr_y1, mr_x0:mr_x1]
        else:
            full_mask = mask

        # Morphological clean-up with adaptive kernel for dashed boundaries
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (k_size, k_size))
        full_mask = cv2.morphologyEx(full_mask, cv2.MORPH_CLOSE, kernel)
        full_mask = cv2.morphologyEx(full_mask, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3)))

        cnts, _ = cv2.findContours(full_mask, cv2.RETR_EXTERNAL,
                                    cv2.CHAIN_APPROX_SIMPLE)
        if not cnts:
            continue

        # Score contours: largest area that is not nearly full-image
        for cnt in cnts:
            area_px = cv2.contourArea(cnt)
            total_px = ih * iw
            if area_px < total_px * 0.005:
                continue   # too small (< 0.5% of image)
            if area_px > total_px * 0.90:
                continue   # covers almost whole page

            x, y, w, h = cv2.boundingRect(cnt)
            aspect = w / (h or 1.0)
            if aspect < 0.2 or aspect > 5.0:
                continue   # very thin strip — not a site boundary

            peri = cv2.arcLength(cnt, True)
            approx = cv2.approxPolyDP(cnt, 0.018 * peri, True)
            # Convert pixel approx polygon → PDF pts (unrotated)
            poly_pts = []
            for pt in approx:
                px_x, px_y = pt[0][0], pt[0][1]
                pdf_x = px_x / scale
                pdf_y = px_y / scale
                poly_pts.append((pdf_x, pdf_y))

            if len(poly_pts) >= 3:
                results.append((area_px, poly_pts, label))

    if not results:
        return None

    # Pick the best contour: largest area
    results.sort(key=lambda x: x[0], reverse=True)
    _, best_pts, best_label = results[0]

    return (best_pts, best_label)


# ---------------------------------------------------------------------------
# AOI Validator
# ---------------------------------------------------------------------------

def _validate_aoi(bbox: List[float], map_region: List[float],
                   mw: float, mh: float) -> Tuple[bool, str]:
    """Validate the detected AOI bbox.

    Returns (is_valid, reason_string).
    """
    x0, y0, x1, y1 = bbox
    w = x1 - x0
    h = y1 - y0

    if w <= 0 or h <= 0:
        return False, "AOI has zero or negative dimensions"

    area = w * h
    page_area = mw * mh
    if area < page_area * 0.001:
        return False, f"AOI area too small ({area:.0f} pt² < 0.1% of page)"

    if area > page_area * 0.93:
        return False, f"AOI covers > 93% of page — likely includes legend/footer"

    # Check it is inside page bounds
    if x0 < -5 or y0 < -5 or x1 > mw + 5 or y1 > mh + 5:
        return False, f"AOI extends outside page bounds"

    # Check it is inside (or substantially overlapping) map_region
    mr_x0, mr_y0, mr_x1, mr_y1 = map_region
    overlap_x = max(0.0, min(x1, mr_x1) - max(x0, mr_x0))
    overlap_y = max(0.0, min(y1, mr_y1) - max(y0, mr_y0))
    overlap = overlap_x * overlap_y
    if overlap < area * 0.50:
        return False, (f"AOI overlaps less than 50% with map region "
                       f"(map_region={[round(v,1) for v in map_region]})")

    return True, "OK"


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def detect_aoi_from_pdf(pdf_path: str, document_id: str, page_num: int = 1) -> AOI:
    """Detect the true enquiry Area of Interest (AOI) boundary from a PDF map.

    Detection priority:
    1. PDF vector dashed boundary (colour-agnostic, scored)
    2. PDF vector solid-stroke coloured boundary (red/magenta)
    3. CV raster contour of red/magenta shape in rendered image
    4. Map-region fallback  (content-derived, NOT hardcoded page fraction)

    Circles drawn as 64 line-segments are detected and emitted as
    GeometryType.CIRCLE with center/radius preserved.
    """
    try:
        doc = pymupdf.open(pdf_path)
        if page_num < 1 or page_num > len(doc):
            raise IndexError("Page number out of bounds")

        page = doc[page_num - 1]
        rotation = page.rotation
        mediabox = page.mediabox
        mw, mh = mediabox.width, mediabox.height
        pw, ph = page.rect.width, page.rect.height   # visual dimensions

        # ── Stage 3 first: derive the map region (needed by all stages) ─────
        map_region = _derive_map_region(page)
        mr_x0, mr_y0, mr_x1, mr_y1 = map_region

        # ── Stage 1: Vector drawings ──────────────────────────────────────────
        drawings = page.get_drawings()
        scored = _score_vector_drawings(drawings, rotation, mediabox, page.rect)

        chosen_drawing = None
        chosen_raw_rect = None
        chosen_vis_rect = None
        chosen_score = 0
        vector_source = None

        if scored:
            best_score, best_d, best_raw, best_vis = scored[0]
            # Accept if score is meaningfully above background noise
            if best_score >= 120:
                chosen_drawing = best_d
                chosen_raw_rect = best_raw
                chosen_vis_rect = best_vis
                chosen_score = best_score
                has_dashes = bool(best_d.get("dashes") and
                                   str(best_d.get("dashes", "")).strip()
                                   not in ("", "[] 0", "[]"))
                vector_source = "dashed_vector_boundary" if has_dashes else "solid_vector_boundary"
                logger.info(
                    f"Vector boundary AOI on page {page_num} "
                    f"(score={best_score}, source={vector_source}, rot={rotation}): "
                    f"unrotated=[{best_raw.x0:.1f},{best_raw.y0:.1f},"
                    f"{best_raw.x1:.1f},{best_raw.y1:.1f}]"
                )

        # ── Build AOI from vector boundary ────────────────────────────────────
        if chosen_drawing is not None:
            items = chosen_drawing.get("items", [])

            # Check if the shape is a circle
            circle = _detect_circle_from_items(items)

            if circle:
                cx, cy, r = circle
                # bbox and coordinates stay in unrotated mediabox space
                # (used for spatial intersection with plant-data drawings)
                coords = _circle_to_coords(cx, cy, r)
                bbox = [cx - r, cy - r, cx + r, cy + r]
                geometry_type = GeometryType.CIRCLE

                # Convert circle center to VISUAL (rendered-page) coordinates so
                # crops.py can draw the overlay correctly even on rotated pages.
                # PyMuPDF renders get_pixmap() in visual orientation; the
                # coordinate_transformer just scales pt→px with no rotation.
                if rotation != 0:
                    vis_bbox = _unrotated_to_visual(
                        pymupdf.Rect(cx - r, cy - r, cx + r, cy + r),
                        rotation, mediabox
                    )
                    cx_vis = (vis_bbox.x0 + vis_bbox.x1) / 2.0
                    cy_vis = (vis_bbox.y0 + vis_bbox.y1) / 2.0
                else:
                    cx_vis, cy_vis = cx, cy

                valid, reason = _validate_aoi(bbox, map_region, mw, mh)
                confidence = 0.99 if valid else 0.55
                evidence = [
                    f"Circular dashed/vector boundary detected ({len(items)} segments)",
                    f"Circle center=({cx:.1f},{cy:.1f}), radius={r:.1f}pt (unrotated)",
                    f"Circle center visual=({cx_vis:.1f},{cy_vis:.1f}) (rotation={rotation}°)",
                    f"Source: {vector_source}",
                    f"Validation: {reason}",
                ]

                logger.info(
                    f"Circle AOI on page {page_num}: center=({cx:.1f},{cy:.1f}), "
                    f"radius={r:.1f}pt, visual_center=({cx_vis:.1f},{cy_vis:.1f}), "
                    f"rotation={rotation}, valid={valid}"
                )
                return AOI(
                    aoi_id=f"AOI-{document_id}-P{page_num}",
                    document_id=document_id,
                    page_num=page_num,
                    geometry_type=geometry_type,
                    method=AOIDetectionMethod.NATIVE_VECTOR,
                    coordinates=coords,
                    bbox=bbox,
                    confidence=confidence,
                    is_valid=valid,
                    map_region=map_region,
                    source=vector_source,
                    evidence=evidence,
                    circle_center=[cx_vis, cy_vis],   # visual coords for rendering
                    circle_radius=r,
                )

            else:
                # Non-circular vector polygon/rectangle
                raw = chosen_raw_rect
                bbox = [raw.x0, raw.y0, raw.x1, raw.y1]
                poly = box(raw.x0, raw.y0, raw.x1, raw.y1)
                coords = list(poly.exterior.coords)
                geometry_type = GeometryType.POLYGON

                valid, reason = _validate_aoi(bbox, map_region, mw, mh)
                confidence = 0.97 if valid else 0.55
                evidence = [
                    f"Vector boundary polygon detected ({len(items)} items)",
                    f"Source: {vector_source}",
                    f"Validation: {reason}",
                ]

                logger.info(
                    f"Polygon AOI on page {page_num} "
                    f"bbox=[{raw.x0:.1f},{raw.y0:.1f},{raw.x1:.1f},{raw.y1:.1f}], valid={valid}"
                )
                return AOI(
                    aoi_id=f"AOI-{document_id}-P{page_num}",
                    document_id=document_id,
                    page_num=page_num,
                    geometry_type=geometry_type,
                    method=AOIDetectionMethod.NATIVE_VECTOR,
                    coordinates=coords,
                    bbox=bbox,
                    confidence=confidence,
                    is_valid=valid,
                    map_region=map_region,
                    source=vector_source,
                    evidence=evidence,
                )

        # ── Stage 2: CV raster contour ────────────────────────────────────────
        logger.info(
            f"No vector boundary found on page {page_num} — "
            f"trying CV raster contour detection"
        )
        cv_result = _detect_boundary_via_cv(page, map_region, pw, ph)

        if cv_result:
            poly_pts, colour_label = cv_result
            if len(poly_pts) >= 3:
                shapely_poly = Polygon(poly_pts)
                if shapely_poly.is_valid and shapely_poly.area > 0:
                    bounds = shapely_poly.bounds  # (minx, miny, maxx, maxy)
                    bbox = list(bounds)

                    valid, reason = _validate_aoi(bbox, map_region, mw, mh)
                    confidence = 0.88 if valid else 0.45
                    evidence = [
                        f"CV raster contour: {colour_label} boundary detected",
                        f"Contour vertices: {len(poly_pts)}",
                        f"Validation: {reason}",
                    ]
                    logger.info(
                        f"CV contour AOI on page {page_num}: colour={colour_label}, "
                        f"bbox=[{bbox[0]:.1f},{bbox[1]:.1f},{bbox[2]:.1f},{bbox[3]:.1f}], "
                        f"valid={valid}"
                    )
                    return AOI(
                        aoi_id=f"AOI-{document_id}-P{page_num}",
                        document_id=document_id,
                        page_num=page_num,
                        geometry_type=GeometryType.POLYGON,
                        method=AOIDetectionMethod.CV_CONTOUR,
                        coordinates=poly_pts,
                        bbox=bbox,
                        confidence=confidence,
                        is_valid=valid,
                        map_region=map_region,
                        source="cv_contour",
                        evidence=evidence,
                    )

        # ── Stage 3 Fallback: MAP_REGION ──────────────────────────────────────
        # Per spec §6: if no explicit dig-site boundary found, DIG_AOI = MAP_REGION
        # NOT the full page, NOT a hardcoded fraction — the content-derived map region.
        canvas_box = box(mr_x0, mr_y0, mr_x1, mr_y1)
        bbox = [mr_x0, mr_y0, mr_x1, mr_y1]
        coords = list(canvas_box.exterior.coords)

        evidence = [
            "No explicit dig-site boundary found (vector or raster)",
            f"AOI set to MAP_REGION derived from text-block analysis",
            f"Map region excludes legend/footer/header",
        ]

        logger.info(
            f"MAP_REGION fallback AOI on page {page_num}: "
            f"bbox=[{mr_x0:.1f},{mr_y0:.1f},{mr_x1:.1f},{mr_y1:.1f}]"
        )
        return AOI(
            aoi_id=f"AOI-{document_id}-P{page_num}",
            document_id=document_id,
            page_num=page_num,
            geometry_type=GeometryType.POLYGON,
            method=AOIDetectionMethod.FALLBACK,
            coordinates=coords,
            bbox=bbox,
            confidence=0.75,
            is_valid=True,
            map_region=map_region,
            source="map_region_fallback",
            evidence=evidence,
        )

    except Exception as e:
        logger.error(f"Error detecting AOI for {pdf_path}: {e}", exc_info=True)
        return AOI(
            aoi_id=f"AOI-{document_id}-ERR",
            document_id=document_id,
            page_num=page_num,
            geometry_type=GeometryType.POLYGON,
            method=AOIDetectionMethod.FALLBACK,
            confidence=0.0,
            is_valid=False,
            source="error",
            evidence=[f"Exception: {e}"],
        )
