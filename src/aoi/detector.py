import pymupdf
from typing import List, Optional, Tuple
from shapely.geometry import Polygon, box
from src.domain.aoi import AOI
from src.domain.enums import AOIDetectionMethod, GeometryType
from src.config.logging import logger


def _visual_to_unrotated(rect: pymupdf.Rect, rotation: int, mediabox: pymupdf.Rect) -> pymupdf.Rect:
    """Convert visual (rendered) page coordinates to unrotated (mediabox) coordinates.

    PyMuPDF's get_drawings() always returns coordinates in the UNROTATED mediabox space.
    However, size filters (pw, ph) compare against the VISUAL page.rect dimensions.
    
    This helper converts a rect from the visual/rendered space back to unrotated space,
    so that visual-based filters remain consistent with drawing coordinates.
    """
    mw, mh = mediabox.width, mediabox.height
    if rotation == 0:
        return pymupdf.Rect(rect)
    elif rotation == 90:
        # visual → unrotated: x_un = y_vis, y_un = mh - x_vis (for rect: swap & mirror)
        return pymupdf.Rect(rect.y0, mh - rect.x1, rect.y1, mh - rect.x0)
    elif rotation == 180:
        return pymupdf.Rect(mw - rect.x1, mh - rect.y1, mw - rect.x0, mh - rect.y0)
    elif rotation == 270:
        return pymupdf.Rect(mw - rect.y1, rect.x0, mw - rect.y0, rect.x1)
    return pymupdf.Rect(rect)


def _unrotated_to_visual(rect: pymupdf.Rect, rotation: int, mediabox: pymupdf.Rect) -> pymupdf.Rect:
    """Convert unrotated (mediabox) drawing coordinates to visual/rendered page coordinates.

    PyMuPDF's get_drawings() returns coords in unrotated space.
    This maps them into the visual page space so size & position filters
    (using page.rect width/height) work correctly.
    """
    mw, mh = mediabox.width, mediabox.height
    if rotation == 0:
        return pymupdf.Rect(rect)
    elif rotation == 90:
        # unrotated (x,y) → visual: x_vis = mh - y_un, y_vis = x_un
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


def detect_aoi_from_pdf(pdf_path: str, document_id: str, page_num: int = 1) -> AOI:
    """Detect the true enquiry Area of Interest (AOI) boundary from a PDF map.

    Detection Priority:
    1. ANY DASHED LINE that forms the dig-site boundary — colour-agnostic approach,
       scored by: is dashed, has many vertices (circular), is in the map canvas area,
       and is not a tiny legend swatch or a full-page border.
       Common colours: magenta/purple (UKPN, SGN), yellow (NGED/WPD), red (some providers).
    2. If no dashed boundary found → use the WHOLE map canvas as AOI
       (excluding header, footer, and legend panels — based on content density).
       This ensures no assets are ever missed when an explicit boundary is absent.
    """
    try:
        doc = pymupdf.open(pdf_path)
        if page_num < 1 or page_num > len(doc):
            raise IndexError("Page number out of bounds")

        page = doc[page_num - 1]
        rotation = page.rotation
        mediabox = page.mediabox
        # Visual (rendered) page dimensions:
        pw, ph = page.rect.width, page.rect.height

        drawings = page.get_drawings()

        dashed_boundary_candidates = []

        for d in drawings:
            raw_rect = d.get("rect")
            if not raw_rect:
                continue

            dashes = d.get("dashes")
            has_dashes = bool(dashes and str(dashes).strip() not in ("", "[] 0", "[]"))
            if not has_dashes:
                continue

            num_items = len(d.get("items", []))
            width_pt = d.get("width") or 0.0

            # Map the unrotated drawing rect → visual page coords for size/position filtering
            vis_rect = _unrotated_to_visual(raw_rect, rotation, mediabox)
            vw, vh = vis_rect.width, vis_rect.height
            vx0, vy0, vx1, vy1 = vis_rect.x0, vis_rect.y0, vis_rect.x1, vis_rect.y1

            # --- Size filters ---
            # Skip tiny legend swatches (< 30pt in either dimension)
            if vw < 30 or vh < 30:
                continue
            # Skip full-page borders (> 95% of visual dimensions)
            if vw > pw * 0.95 or vh > ph * 0.95:
                continue

            # --- Position filters ---
            # Skip drawings entirely inside header (top 5%) or footer/legend (bottom 20%)
            # The map canvas occupies roughly the top 5% to bottom 78% on A4 portrait,
            # or left 5% to right 75% on A4 landscape.
            if vy1 < ph * 0.04 or vy0 > ph * 0.82:
                continue
            if vx1 < pw * 0.01 or vx0 > pw * 0.85:
                continue

            # --- Scoring ---
            # Higher scores for more circular (more items), clearly dashed, and larger
            score = 0
            score += 100  # base: it is dashed
            score += min(num_items * 2, 80)   # more vertices → more circular
            score += min(int(vw + vh), 200)    # larger bounding box preferred
            if width_pt >= 1.5:
                score += 20   # thicker boundary lines preferred
            if num_items >= 16:
                score += 30   # very likely a circle/polygon boundary

            # Colour bonus (known providers)
            raw_c = d.get("color") or d.get("fill")
            if raw_c and len(raw_c) >= 3:
                rc, gc, bc = [v * 255 for v in raw_c[:3]]
                # Magenta/Purple (UKPN, SGN, Cadent, National Gas)
                if rc > 140 and gc < 100 and bc > 140:
                    score += 50
                # Yellow/Gold (NGED/WPD)
                elif rc > 180 and gc > 180 and bc < 80:
                    score += 40
                # Red (some water/other providers)
                elif rc > 180 and gc < 80 and bc < 80:
                    score += 30

            dashed_boundary_candidates.append((score, raw_rect, vis_rect))

        chosen_raw_rect = None
        chosen_vis_rect = None
        confidence = 0.99
        detect_method = AOIDetectionMethod.NATIVE_VECTOR

        if dashed_boundary_candidates:
            dashed_boundary_candidates.sort(key=lambda x: x[0], reverse=True)
            best = dashed_boundary_candidates[0]
            chosen_raw_rect = best[1]
            chosen_vis_rect = best[2]
            logger.info(
                f"Detected dashed boundary AOI on page {page_num} "
                f"(score={best[0]}, rot={rotation}): "
                f"unrotated_bbox=[{chosen_raw_rect.x0:.1f},{chosen_raw_rect.y0:.1f},"
                f"{chosen_raw_rect.x1:.1f},{chosen_raw_rect.y1:.1f}] "
                f"visual_bbox=[{chosen_vis_rect.x0:.1f},{chosen_vis_rect.y0:.1f},"
                f"{chosen_vis_rect.x1:.1f},{chosen_vis_rect.y1:.1f}]"
            )

        if chosen_raw_rect:
            # Use UNROTATED coordinates for bbox (same space as get_drawings() paths)
            poly = box(chosen_raw_rect.x0, chosen_raw_rect.y0,
                       chosen_raw_rect.x1, chosen_raw_rect.y1)
            return AOI(
                aoi_id=f"AOI-{document_id}-P{page_num}",
                document_id=document_id,
                page_num=page_num,
                geometry_type=GeometryType.POLYGON,
                method=detect_method,
                coordinates=list(poly.exterior.coords),
                bbox=[chosen_raw_rect.x0, chosen_raw_rect.y0,
                      chosen_raw_rect.x1, chosen_raw_rect.y1],
                confidence=confidence,
                is_valid=True
            )

        # ── FALLBACK: No dashed boundary found ───────────────────────────────
        # Per user requirement: use the WHOLE MAP CANVAS as AOI.
        # We estimate the map canvas by excluding the header (top ~5%),
        # footer/legend panel (bottom ~22%), and any right-side legend block (right ~28%).
        # All in unrotated (mediabox) coordinates so intersection with drawings works correctly.
        mw, mh = mediabox.width, mediabox.height

        # Determine map canvas bounds in unrotated space depending on page orientation
        # Portrait (mh > mw): header top 5%, footer bottom 20%, right panel right 5%
        # Landscape (mw > mh): header left 5%, legend panel right 22%, bottom footer 20%
        if mh >= mw:
            # Portrait orientation (unrotated)
            canvas_x0 = mw * 0.02
            canvas_y0 = mh * 0.05
            canvas_x1 = mw * 0.95
            canvas_y1 = mh * 0.80
        else:
            # Landscape orientation (unrotated)
            canvas_x0 = mw * 0.01
            canvas_y0 = mh * 0.02
            canvas_x1 = mw * 0.78
            canvas_y1 = mh * 0.95

        canvas_box = box(canvas_x0, canvas_y0, canvas_x1, canvas_y1)

        logger.info(
            f"No dashed boundary found — using WHOLE MAP CANVAS as AOI on page {page_num}: "
            f"bbox=[{canvas_x0:.1f},{canvas_y0:.1f},{canvas_x1:.1f},{canvas_y1:.1f}]"
        )
        return AOI(
            aoi_id=f"AOI-{document_id}-P{page_num}",
            document_id=document_id,
            page_num=page_num,
            geometry_type=GeometryType.POLYGON,
            method=AOIDetectionMethod.FALLBACK,
            coordinates=list(canvas_box.exterior.coords),
            bbox=[canvas_x0, canvas_y0, canvas_x1, canvas_y1],
            confidence=0.75,
            is_valid=True
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
            is_valid=False
        )
