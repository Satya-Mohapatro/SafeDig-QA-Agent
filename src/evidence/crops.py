import os
import cv2
import numpy as np
from typing import Optional, List, Any
from src.domain.enums import GeometryType
from src.pdf.renderer import render_page_to_image
from src.spatial.coordinates import coordinate_transformer
from src.config.logging import logger

def generate_evidence_crop(
    pdf_path: str,
    page_num: int,
    bbox_pt: List[float],
    output_crop_path: str,
    dpi: int = 300,
    margin_px: int = 50
) -> Optional[str]:
    """Generate high-resolution visual crop of detected hazard candidate with contextual margin."""
    try:
        temp_page_img = output_crop_path + "_page.png"
        rendered = render_page_to_image(pdf_path, page_num, temp_page_img, dpi=dpi)
        if not rendered or not os.path.exists(temp_page_img):
            return None
            
        img = cv2.imread(temp_page_img)
        if img is None:
            return None
            
        h_img, w_img = img.shape[:2]
        
        # Convert PDF points bbox to pixel bbox
        x0_pt, y0_pt, x1_pt, y1_pt = bbox_pt
        x0, y0 = coordinate_transformer.pdf_to_pixel(x0_pt, y0_pt, dpi=dpi)
        x1, y1 = coordinate_transformer.pdf_to_pixel(x1_pt, y1_pt, dpi=dpi)
        
        # Apply margin and bounds clamping
        crop_x0 = max(0, min(x0, x1) - margin_px)
        crop_y0 = max(0, min(y0, y1) - margin_px)
        crop_x1 = min(w_img, max(x0, x1) + margin_px)
        crop_y1 = min(h_img, max(y0, y1) + margin_px)
        
        if crop_x1 <= crop_x0 or crop_y1 <= crop_y0:
            return None
            
        crop = img[crop_y0:crop_y1, crop_x0:crop_x1].copy()
        
        # Draw highlight box on the crop
        box_x0 = max(0, min(x0, x1) - crop_x0)
        box_y0 = max(0, min(y0, y1) - crop_y0)
        box_x1 = min(crop.shape[1] - 1, max(x0, x1) - crop_x0)
        box_y1 = min(crop.shape[0] - 1, max(y0, y1) - crop_y0)
        
        # Draw dual-layer highlight box (thick outer glow + inner sharp red)
        cv2.rectangle(crop, (box_x0 - 1, box_y0 - 1), (box_x1 + 1, box_y1 + 1), (0, 0, 180), 3)
        cv2.rectangle(crop, (box_x0, box_y0), (box_x1, box_y1), (0, 0, 255), 2)
        
        os.makedirs(os.path.dirname(output_crop_path), exist_ok=True)
        cv2.imwrite(output_crop_path, crop)
        
        if os.path.exists(temp_page_img):
            os.remove(temp_page_img)
            
        return output_crop_path
    except Exception as e:
        logger.error(f"Error generating evidence crop: {e}")
        return None


def generate_aoi_map_render(
    pdf_path: str,
    page_num: int,
    aoi_bbox_pt: Optional[List[float]],
    output_image_path: str,
    dpi: int = 300,
    aoi: Optional[Any] = None
) -> Optional[str]:
    """Render full PDF page with highlighted red AOI boundary and site badge.
    
    Accurately renders:
    - True circle (cv2.circle) when aoi.geometry_type == CIRCLE
    - True polygon (cv2.polylines) when aoi.geometry_type == POLYGON
    - True rectangle (cv2.rectangle) when aoi is rectangular or fallback
    """
    try:
        os.makedirs(os.path.dirname(output_image_path), exist_ok=True)
        rendered = render_page_to_image(pdf_path, page_num, output_image_path, dpi=dpi)
        if not rendered or not os.path.exists(output_image_path):
            return None
            
        img = cv2.imread(output_image_path)
        if img is None:
            return output_image_path
            
        h, w = img.shape[:2]
        drawn = False
        badge_x, badge_y = None, None
        
        # 1. Circle rendering
        is_circle = (
            aoi is not None
            and (
                getattr(aoi, "geometry_type", None) == GeometryType.CIRCLE
                or str(getattr(aoi, "geometry_type", "")).endswith("CIRCLE")
            )
            and getattr(aoi, "circle_center", None)
            and getattr(aoi, "circle_radius", None)
        )
        is_polygon = (
            aoi is not None
            and (
                getattr(aoi, "geometry_type", None) == GeometryType.POLYGON
                or str(getattr(aoi, "geometry_type", "")).endswith("POLYGON")
            )
            and getattr(aoi, "coordinates", None)
            and len(aoi.coordinates) >= 3
            and getattr(aoi, "source", "") != "map_region_fallback"
        )

        if is_circle:
            cx_pt, cy_pt = aoi.circle_center
            r_pt = aoi.circle_radius
            cx_px, cy_px = coordinate_transformer.pdf_to_pixel(cx_pt, cy_pt, dpi=dpi)
            r_px = int(round(r_pt * (dpi / 72.0)))
            
            # Outer dark red glow + inner vibrant red
            cv2.circle(img, (cx_px, cy_px), r_px + 2, (0, 0, 160), 6)
            cv2.circle(img, (cx_px, cy_px), r_px, (0, 0, 255), 4)
            drawn = True
            badge_x = cx_px
            badge_y = cy_px - r_px
            
        # 2. Polygon rendering
        elif is_polygon:
            pts_px = []
            for pt in aoi.coordinates:
                px_x, px_y = coordinate_transformer.pdf_to_pixel(pt[0], pt[1], dpi=dpi)
                pts_px.append([int(px_x), int(px_y)])
            pts_arr = np.array(pts_px, dtype=np.int32).reshape((-1, 1, 2))
            
            cv2.polylines(img, [pts_arr], True, (0, 0, 160), 6)
            cv2.polylines(img, [pts_arr], True, (0, 0, 255), 4)
            drawn = True
            min_y_idx = int(np.argmin([p[1] for p in pts_px]))
            badge_x = pts_px[min_y_idx][0]
            badge_y = pts_px[min_y_idx][1]
            
        # 3. Rectangle boundary (fallback or rectangular AOI)
        elif aoi_bbox_pt and len(aoi_bbox_pt) == 4:
            x0_pt, y0_pt, x1_pt, y1_pt = aoi_bbox_pt
            x0, y0 = coordinate_transformer.pdf_to_pixel(x0_pt, y0_pt, dpi=dpi)
            x1, y1 = coordinate_transformer.pdf_to_pixel(x1_pt, y1_pt, dpi=dpi)
            bx0 = max(0, min(w - 1, min(x0, x1)))
            by0 = max(0, min(h - 1, min(y0, y1)))
            bx1 = max(0, min(w - 1, max(x0, x1)))
            by1 = max(0, min(h - 1, max(y0, y1)))
            
            cv2.rectangle(img, (bx0 - 2, by0 - 2), (bx1 + 2, by1 + 2), (0, 0, 180), 6)
            cv2.rectangle(img, (bx0, by0), (bx1, by1), (0, 0, 255), 4)
            drawn = True
            badge_x = bx0
            badge_y = by0
            
        if drawn and badge_x is not None and badge_y is not None:
            label = "AOI SITE BOUNDARY"
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.7
            thickness = 2
            (tw, th), baseline = cv2.getTextSize(label, font, font_scale, thickness)
            
            label_y = max(th + 6, badge_y - 8)
            label_x = min(w - tw - 10, max(5, badge_x - tw // 2 if is_circle else badge_x))
            
            # Tag background
            cv2.rectangle(
                img,
                (label_x - 4, label_y - th - 4),
                (label_x + tw + 4, label_y + baseline + 2),
                (0, 0, 220),
                -1
            )
            # Tag text
            cv2.putText(
                img,
                label,
                (label_x, label_y),
                font,
                font_scale,
                (255, 255, 255),
                thickness,
                cv2.LINE_AA
            )
            
            cv2.imwrite(output_image_path, img)
            
        return output_image_path
    except Exception as e:
        logger.error(f"Error generating AOI map render: {e}")
        return None
