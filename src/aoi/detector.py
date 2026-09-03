import fitz
from typing import List, Optional, Tuple
from shapely.geometry import Polygon, box
from src.domain.aoi import AOI
from src.domain.enums import AOIDetectionMethod, GeometryType
from src.config.logging import logger

def detect_aoi_from_pdf(pdf_path: str, document_id: str, page_num: int = 1) -> AOI:
    """Detect the true enquiry Area of Interest (AOI) boundary from a PDF map.
    
    UK Utility Maps (LSBUD, WWU, SGN, UKPN, ESP, Cadent, etc.) represent the enquiry
    site boundary as a Magenta/Purple dashed circle/polygon or a distinct Red search boundary.
    This detector prioritizes:
    1. Magenta / Purple dashed circular / polygonal enquiry boundaries.
    2. Red dashed search boundaries in the map canvas.
    3. Distinct vector boundary rectangles (excluding header/footer logos).
    4. Central map canvas focus fallback.
    """
    try:
        doc = fitz.open(pdf_path)
        if page_num < 1 or page_num > len(doc):
            raise IndexError("Page number out of bounds")
            
        page = doc[page_num - 1]
        pw, ph = page.rect.width, page.rect.height
        drawings = page.get_drawings()
        
        magenta_candidates = []
        red_dashed_candidates = []
        other_vector_candidates = []
        
        for d in drawings:
            raw_c = d.get("color") or d.get("fill")
            rect_box = d.get("rect")
            if not rect_box or not raw_c or len(raw_c) < 3:
                continue
                
            r, g, b = raw_c[:3]
            if max(r, g, b) <= 1.0:
                r, g, b = r * 255.0, g * 255.0, b * 255.0
                
            w, h = rect_box.width, rect_box.height
            x0, y0, x1, y1 = rect_box.x0, rect_box.y0, rect_box.x1, rect_box.y1
            dashes = d.get("dashes")
            has_dashes = bool(dashes and dashes != "[] 0")
            num_items = len(d.get("items", []))
            
            # Filter out tiny symbols (< 25pt) and whole-page frames (> 92% width/height)
            if w < 25 or h < 25 or w > pw * 0.92 or h > ph * 0.92:
                continue
                
            # Filter out extreme footer / legend / header margin areas
            if y0 > ph * 0.90 or y1 < ph * 0.04:
                continue
                
            # 1. Check for Magenta / Violet / Purple Enquiry Boundary (e.g. RGB 205, 0, 205)
            if r > 150 and g < 110 and b > 150:
                score = (100 if has_dashes else 80) + (20 if num_items >= 10 else 0)
                magenta_candidates.append((score, rect_box, "MAGENTA_DASHED" if has_dashes else "MAGENTA_VECTOR"))
                continue
                
            # 2. Check for Red Dashed Boundary
            if r > 170 and g < 90 and b < 90:
                if has_dashes or num_items >= 4:
                    if y0 < ph * 0.85:
                        red_dashed_candidates.append((50, rect_box, "RED_DASHED"))
                elif 40 < w < pw * 0.70 and 40 < h < ph * 0.70 and y0 > ph * 0.08 and y1 < ph * 0.85:
                    other_vector_candidates.append((20, rect_box, "RED_RECT"))

        chosen_rect = None
        detect_method = AOIDetectionMethod.NATIVE_VECTOR
        confidence = 0.98

        if magenta_candidates:
            magenta_candidates.sort(key=lambda x: x[0], reverse=True)
            chosen_rect = magenta_candidates[0][1]
            confidence = 0.99
            logger.info(f"Detected Magenta Dashed AOI on page {page_num}: bbox={[chosen_rect.x0, chosen_rect.y0, chosen_rect.x1, chosen_rect.y1]}")
        elif red_dashed_candidates:
            red_dashed_candidates.sort(key=lambda x: x[0], reverse=True)
            chosen_rect = red_dashed_candidates[0][1]
            confidence = 0.95
            logger.info(f"Detected Red Dashed AOI on page {page_num}: bbox={[chosen_rect.x0, chosen_rect.y0, chosen_rect.x1, chosen_rect.y1]}")
        elif other_vector_candidates:
            other_vector_candidates.sort(key=lambda x: x[0], reverse=True)
            chosen_rect = other_vector_candidates[0][1]
            confidence = 0.90
            logger.info(f"Detected Vector AOI boundary on page {page_num}: bbox={[chosen_rect.x0, chosen_rect.y0, chosen_rect.x1, chosen_rect.y1]}")

        if chosen_rect:
            poly = box(chosen_rect.x0, chosen_rect.y0, chosen_rect.x1, chosen_rect.y1)
            return AOI(
                aoi_id=f"AOI-{document_id}-P{page_num}",
                document_id=document_id,
                page_num=page_num,
                geometry_type=GeometryType.POLYGON,
                method=detect_method,
                coordinates=list(poly.exterior.coords),
                bbox=[chosen_rect.x0, chosen_rect.y0, chosen_rect.x1, chosen_rect.y1],
                confidence=confidence,
                is_valid=True
            )

        # 3. Central search zone fallback if explicit vector boundary line is absent
        cx, cy = pw / 2.0, ph / 2.0
        w_half, h_half = min(pw * 0.25, 160.0), min(ph * 0.25, 160.0)
        center_box = box(cx - w_half, cy - h_half, cx + w_half, cy + h_half)
        
        logger.info(f"Defaulting to central map focus AOI on page {page_num}")
        return AOI(
            aoi_id=f"AOI-{document_id}-P{page_num}",
            document_id=document_id,
            page_num=page_num,
            geometry_type=GeometryType.POLYGON,
            method=AOIDetectionMethod.FALLBACK,
            coordinates=list(center_box.exterior.coords),
            bbox=[cx - w_half, cy - h_half, cx + w_half, cy + h_half],
            confidence=0.80,
            is_valid=True
        )
    except Exception as e:
        logger.error(f"Error detecting AOI for {pdf_path}: {e}")
        return AOI(
            aoi_id=f"AOI-{document_id}-ERR",
            document_id=document_id,
            page_num=page_num,
            geometry_type=GeometryType.POLYGON,
            method=AOIDetectionMethod.FALLBACK,
            confidence=0.0,
            is_valid=False
        )
