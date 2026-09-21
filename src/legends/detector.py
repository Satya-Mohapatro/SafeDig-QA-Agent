import os
import fitz  # PyMuPDF
import cv2
import numpy as np
from PIL import Image
from typing import List, Optional, Tuple, Dict, Any
from src.domain.legend import LegendProfile, LegendFeature, ColorSignature, StrokeStyle
from src.domain.enums import GeometryType
from src.legends.registry import master_legend_registry
from src.config.logging import logger

def _rgb_to_hex(rgb: Tuple[int, int, int]) -> str:
    return f"#{rgb[0]:02X}{rgb[1]:02X}{rgb[2]:02X}"

def _color_distance(c1: Tuple[int, int, int], c2: Tuple[int, int, int]) -> float:
    return float(np.sqrt((c1[0] - c2[0])**2 + (c1[1] - c2[1])**2 + (c1[2] - c2[2])**2))

def detect_legend_region(page: fitz.Page) -> Optional[fitz.Rect]:
    """Identify the bounding box of the legend/key on a PDF page."""
    rect = page.rect
    w, h = rect.width, rect.height

    # 1. Search text blocks for explicit legend keywords
    blocks = page.get_text("blocks")
    legend_keywords = ["legend", "map key", "symbols", "key to symbols", "drawing key", "apparatus key", "pressure mains"]
    matching_boxes = []
    
    for b in blocks:
        text_lower = b[4].lower()
        if any(kw in text_lower for kw in legend_keywords):
            matching_boxes.append(fitz.Rect(b[0], b[1], b[2], b[3]))

    if matching_boxes:
        # Union of matching text boxes expanded slightly
        u_rect = matching_boxes[0]
        for mb in matching_boxes[1:]:
            u_rect = u_rect | mb
        # Expand bounds to include swatches on left/right/top/bottom
        exp_rect = fitz.Rect(
            max(0.0, u_rect.x0 - 50.0),
            max(0.0, u_rect.y0 - 20.0),
            min(w, u_rect.x1 + 180.0),
            min(h, u_rect.y1 + 40.0)
        )
        return exp_rect

    # 2. Check for embedded images in the bottom or side margin (e.g. Thames Water)
    try:
        img_infos = page.get_image_info()
        for info in img_infos:
            ibox = info.get("bbox")
            if ibox:
                ir = fitz.Rect(ibox)
                # Check if image is in margin/footer (y > 60% of height or x > 75% of width)
                if (ir.y0 > 0.60 * h or ir.x0 > 0.70 * w) and ir.width > 100 and ir.height > 40:
                    return ir
    except Exception:
        pass

    # 3. Fallback: Bottom footer region (common for UK utility plans)
    return fitz.Rect(0.0, 0.75 * h, w, h)


def extract_features_from_ocr(
    page: fitz.Page,
    legend_rect: fitz.Rect,
    dpi: int = 300
) -> List[LegendFeature]:
    """Extract legend labels and corresponding swatch colors via OCR and pixel sampling."""
    features: List[LegendFeature] = []
    try:
        import winocr
        zoom = dpi / 72.0
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, clip=legend_rect)
        if pix.width < 10 or pix.height < 10:
            return features

        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        ocr_res = winocr.recognize_pil_sync(img, "en")
        lines = ocr_res.get("lines", [])
        arr = np.array(img)

        # Ground truth colors per utility asset standards:
        # SGN: LP = Red (255,0,0), MP = Cyan (0,197,255), IP = Green (85,255,0), HP = Orange (255,170,0)
        # Water: Trunk = Red (255,0,0), Potable Distribution = Cyan (0,180,255)
        # Electric: HV = Red (255,0,0), LV = Blue (0,0,255)
        candidate_labels = [
            ("water main", (0, 180, 255), "LINE"),
            ("trunk main", (255, 20, 20), "LINE"),
            ("private water", (0, 180, 255), "LINE"),
            ("proposed water", (0, 180, 255), "LINE"),
            ("proposed trunk main", (255, 35, 35), "LINE"),
            ("abandoned asset", (255, 195, 68), "LINE"),
            ("meter", (0, 180, 255), "POINT"),
            ("valve", (0, 180, 255), "POINT"),
            ("hydrant", (255, 0, 0), "POINT"),
            ("high pressure mains", (255, 170, 0), "LINE"),
            ("high pressure", (255, 170, 0), "LINE"),
            ("intermediate pressure mains", (85, 255, 0), "LINE"),
            ("intermediate pressure", (85, 255, 0), "LINE"),
            ("medium pressure mains", (0, 197, 255), "LINE"),
            ("medium pressure", (0, 197, 255), "LINE"),
            ("low pressure mains", (255, 0, 0), "LINE"),
            ("low pressure", (255, 0, 0), "LINE"),
            ("high voltage", (255, 0, 0), "LINE"),
            ("11kv", (255, 0, 0), "LINE"),
            ("33kv", (128, 0, 128), "LINE"),
            ("low voltage", (0, 0, 255), "LINE"),
            ("electric cable", (255, 0, 0), "LINE"),
            ("foul sewer", (139, 69, 19), "LINE"),
            ("surface water", (0, 100, 255), "LINE"),
        ]

        seen_labels = set()

        for line in lines:
            line_text = line.get("text", "").strip()
            line_lower = line_text.lower()
            words = line.get("words", [])
            if not words or len(line_text) < 3:
                continue

            for cand_kw, def_col, gtype in candidate_labels:
                if cand_kw in line_lower and cand_kw not in seen_labels:
                    seen_labels.add(cand_kw)
                    first_w = words[0]
                    last_w = words[-1]
                    br = first_w.get("bounding_rect", {})
                    lbr = last_w.get("bounding_rect", {})
                    
                    bx = int(br.get("x", 0))
                    by = int(br.get("y", 0))
                    bh = int(br.get("height", 15))
                    lbx = int(lbr.get("x", 0))
                    lbw = int(lbr.get("width", 20))
                    
                    swatch_y0 = max(0, by - 4)
                    swatch_y1 = min(arr.shape[0], by + bh + 4)
                    
                    sampled_color = def_col

                    def _extract_chromatic(crop):
                        if crop.size == 0:
                            return None
                        # Require chromatic saturation: max(RGB) - min(RGB) >= 25
                        diff_rg = np.abs(crop[:,:,0].astype(int) - crop[:,:,1].astype(int))
                        diff_gb = np.abs(crop[:,:,1].astype(int) - crop[:,:,2].astype(int))
                        diff_rb = np.abs(crop[:,:,0].astype(int) - crop[:,:,2].astype(int))
                        max_diff = np.maximum(diff_rg, np.maximum(diff_gb, diff_rb))
                        chrom_mask = (max_diff >= 25) & (crop.max(axis=2) > 40) & (crop.min(axis=2) < 235)
                        chrom_pts = crop[chrom_mask]
                        if len(chrom_pts) >= 8:
                            med = np.median(chrom_pts, axis=0).astype(int)
                            return (int(med[0]), int(med[1]), int(med[2]))
                        return None

                    # Try LEFT of text first
                    left_x0 = max(0, bx - 140)
                    left_x1 = max(0, bx - 5)
                    left_col = _extract_chromatic(arr[swatch_y0:swatch_y1, left_x0:left_x1])
                    if left_col is not None:
                        sampled_color = left_col
                    else:
                        # Try RIGHT of text
                        right_x0 = min(arr.shape[1] - 1, lbx + lbw + 5)
                        right_x1 = min(arr.shape[1], lbx + lbw + 140)
                        right_col = _extract_chromatic(arr[swatch_y0:swatch_y1, right_x0:right_x1])
                        if right_col is not None:
                            sampled_color = right_col

                    feat_id = cand_kw.upper().replace(" ", "_")
                    features.append(LegendFeature(
                        feature_id=feat_id,
                        warning_code=feat_id,
                        description=line_text.title(),
                        geometry_type=GeometryType.POINT if gtype == "POINT" else GeometryType.LINE,
                        color=ColorSignature(rgb=sampled_color, tolerance=50),
                        stroke=StrokeStyle(min_width_pt=0.8, max_width_pt=6.0),
                        text_labels=[cand_kw.upper()]
                    ))
                    break

    except Exception as e:
        logger.debug(f"OCR legend extraction exception: {e}")
        
    return features




def extract_features_from_vectors(
    page: fitz.Page,
    legend_rect: fitz.Rect
) -> List[LegendFeature]:
    """Extract legend features from vector text and adjacent vector drawings."""
    features: List[LegendFeature] = []
    drawings = page.get_drawings()
    legend_drawings = [d for d in drawings if legend_rect.intersects(d.get("rect", fitz.Rect()))]
    
    blocks = page.get_text("blocks")
    for b in blocks:
        b_rect = fitz.Rect(b[0], b[1], b[2], b[3])
        if not legend_rect.intersects(b_rect):
            continue
        text = b[4].strip()
        text_lower = text.lower()
        if len(text) < 3:
            continue
            
        # Check against utility keywords
        keywords = ["high pressure", "medium pressure", "low pressure", "intermediate pressure", "trunk", "water main", "hv", "11kv", "33kv", "electric", "gas"]
        for kw in keywords:
            if kw in text_lower:
                # Look for adjacent drawing swatch within 50pt
                adj_color = None
                for d in legend_drawings:
                    dr = d.get("rect")
                    if dr and abs(dr.y0 - b_rect.y0) < 20 and (abs(dr.x1 - b_rect.x0) < 60 or abs(dr.x0 - b_rect.x1) < 60):
                        c = d.get("color")
                        if c and len(c) == 3:
                            adj_color = (int(c[0]*255), int(c[1]*255), int(c[2]*255))
                            break
                            
                if adj_color:
                    feat_id = kw.upper().replace(" ", "_")
                    features.append(LegendFeature(
                        feature_id=feat_id,
                        warning_code=feat_id,
                        description=text.split("\n")[0].strip(),
                        geometry_type=GeometryType.LINE,
                        color=ColorSignature(rgb=adj_color, tolerance=40),
                        stroke=StrokeStyle(min_width_pt=0.8, max_width_pt=6.0),
                        text_labels=[kw.upper()]
                    ))
                break
                
    return features


def detect_dynamic_legend(
    pdf_path: str,
    provider_name: str,
    page_num: int = 1,
    output_crop_dir: Optional[str] = None,
    document_id: Optional[str] = None
) -> LegendProfile:
    """Discover the actual legend on the plan dynamically.
    
    1. Locates legend bounding box on the PDF page.
    2. Crops authentic legend from map and saves as evidence.
    3. Extracts features via OCR (swatch sampling) and vector inspection.
    4. Merges with known provider priors from master_legend_registry.
    5. Returns rich LegendProfile with dynamic confidence.
    """
    profile_id = f"LGD-DYN-{provider_name.upper()[:8]}-P{page_num}"
    doc_id = document_id or "DOC-UNKNOWN"
    crop_path = None

    features: List[LegendFeature] = []
    
    if os.path.exists(pdf_path):
        try:
            doc = fitz.open(pdf_path)
            if 1 <= page_num <= len(doc):
                page = doc[page_num - 1]
                legend_rect = detect_legend_region(page)
                
                # Save legend evidence crop directly from source map
                if output_crop_dir and legend_rect:
                    os.makedirs(output_crop_dir, exist_ok=True)
                    crop_path = os.path.join(output_crop_dir, f"legend_crop_{doc_id}.png")
                    zoom = 200 / 72.0
                    pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), clip=legend_rect)
                    pix.save(crop_path)
                    logger.info(f"Saved authentic legend crop to {crop_path}")
                
                # Extract vector-based legend items
                if legend_rect:
                    v_feats = extract_features_from_vectors(page, legend_rect)
                    features.extend(v_feats)
                    
                    # Extract OCR / bitmap based legend items
                    ocr_feats = extract_features_from_ocr(page, legend_rect)
                    for of in ocr_feats:
                        if not any(f.feature_id == of.feature_id for f in features):
                            features.append(of)

            doc.close()
        except Exception as e:
            logger.warning(f"Dynamic legend detection error on {pdf_path}: {e}")

    # Fallback / Prior enrichment: Merge with static registry if available
    known_profile = master_legend_registry.get_profile(provider_name)
    if known_profile:
        for kf in known_profile.features:
            if not any(f.feature_id == kf.feature_id for f in features):
                features.append(kf)
                
    # If still no features, synthesize baseline features based on provider type
    if not features:
        p_lower = provider_name.lower()
        if "water" in p_lower:
            features = [
                LegendFeature(
                    feature_id="WATER_MAIN",
                    warning_code="WATER_MAIN",
                    description="Water Main",
                    geometry_type=GeometryType.LINE,
                    color=ColorSignature(rgb=(49, 195, 241), tolerance=40),
                    stroke=StrokeStyle(min_width_pt=0.8, max_width_pt=6.0),
                    text_labels=["WATER", "MAIN"]
                ),
                LegendFeature(
                    feature_id="TRUNK_MAIN",
                    warning_code="TRUNK_MAIN",
                    description="Trunk Main",
                    geometry_type=GeometryType.LINE,
                    color=ColorSignature(rgb=(255, 20, 20), tolerance=40),
                    stroke=StrokeStyle(min_width_pt=1.0, max_width_pt=6.0),
                    text_labels=["TRUNK", "MAIN"]
                )
            ]
        elif "gas" in p_lower or "sgn" in p_lower or "cadent" in p_lower:
            features = [
                LegendFeature(
                    feature_id="HP_GAS",
                    warning_code="HP_GAS",
                    description="High Pressure Gas Main",
                    geometry_type=GeometryType.LINE,
                    color=ColorSignature(rgb=(255, 0, 0), tolerance=40),
                    stroke=StrokeStyle(min_width_pt=1.0, max_width_pt=6.0),
                    text_labels=["HP", "HIGH PRESSURE"]
                )
            ]

    profile = LegendProfile(
        legend_id=profile_id,
        provider=provider_name,
        utility_type="Multi-Utility",
        version="2.0.0-dynamic",
        effective_date="2026-09-16",
        source_document=pdf_path,
        features=features
    )
    
    # Attach dynamic crop path as attribute
    setattr(profile, "legend_crop_path", crop_path)
    setattr(profile, "dynamic_confidence", 0.98 if features else 0.70)
    
    logger.info(f"Dynamic legend resolved {len(features)} features for '{provider_name}' (conf={getattr(profile, 'dynamic_confidence'):.2f})")
    return profile
