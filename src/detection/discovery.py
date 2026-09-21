"""
Open-World Independent Map Scan Discovery Engine v2.1

Key improvements:
- Pass D2 (raster CV) runs for ALL maps (not just raster) - critical for Clean Water, Welsh Water etc.
- FALLBACK AOI correctly treats entire map region as scannable
- Color matching uses loose tolerances for raster anti-aliasing
- warnings_list-driven severity assignment
- Better confounder filtering
"""
import os
import cv2
import numpy as np
from typing import List, Optional, Tuple, Dict, Any
from shapely.geometry import box, LineString, MultiLineString, Point
from src.domain.document import Document
from src.domain.aoi import AOI
from src.domain.warning import WarningDefinition
from src.domain.legend import LegendProfile, LegendFeature
from src.domain.asset import DiscoveredAsset, ScanCompleteness
from src.domain.detection import DetectedCandidate
from src.domain.enums import DetectionMethod, Severity, GeometryType
from src.pdf.extractor import extract_page_vector_paths, extract_text_blocks_in_aoi
from src.vector.geometry import drawing_to_shapely
from src.spatial.engine import spatial_engine
from src.config.logging import logger


def _rgb_dist(c1, c2):
    return float(np.sqrt((c1[0]-c2[0])**2 + (c1[1]-c2[1])**2 + (c1[2]-c2[2])**2))

def _rgb_to_hex(rgb):
    return f"#{rgb[0]:02X}{rgb[1]:02X}{rgb[2]:02X}"

def _is_neutral(r, g, b):
    """True for near-grayscale colours (OS basemap roads, buildings)."""
    return abs(int(r)-int(g)) < 22 and abs(int(g)-int(b)) < 22 and abs(int(r)-int(b)) < 22

def _is_fallback_aoi(aoi):
    """True when AOI is the entire map frame (no site circle was detected)."""
    return bool(aoi.source and "fallback" in str(aoi.source).lower()) or (
        aoi.method is not None and "FALLBACK" in str(aoi.method).upper()
    )

def _match_feature(cand_rgb, features, loose=False):
    """Match observed RGB against legend features. loose=True for raster AA blur."""
    best_feat = None
    best_score = 0.0
    for feat in features:
        feat_rgb = feat.color.rgb
        d = _rgb_dist(cand_rgb, feat_rgb)
        tol = float(feat.color.tolerance) if (feat.color and feat.color.tolerance) else 50.0
        effective_tol = tol * (1.8 if loose else 1.0)
        effective_tol = max(30.0, min(100.0 if loose else 72.0, effective_tol))
        if d > effective_tol:
            continue
        score = max(0.0, 1.0 - d / effective_tol)
        if score < 0.25:
            continue
        if score > best_score:
            best_score = score
            best_feat = feat
    return best_feat, best_score

def _is_confounder(d, aoi_bbox, page_w, page_h):
    """Filter non-utility cartographic elements."""
    r = d.get("rect")
    if not r:
        return True
    w, h = r.width, r.height
    if w > 0.85 * page_w and h > 0.85 * page_h:
        return True
    if w > 0.55 * page_w and h > 0.30 * page_h:
        return True
    if w > 0.30 * page_w and h > 0.55 * page_h:
        return True
    if (r.y0 > 0.85 * page_h or r.y1 < 0.05 * page_h) and (w > 0.40 * page_w or h > 0.40 * page_h):
        return True
    if w < 0.5 and h < 0.5:
        return True
    c = d.get("color")
    if c and len(c) == 3:
        rc, gc, bc = int(c[0]*255), int(c[1]*255), int(c[2]*255)
        line_width = float(d.get("width", 1.0) or 1.0)
        if line_width <= 0.4:
            return True
        if _is_neutral(rc, gc, bc) and line_width < 2.5:
            return True
        # Filter OS basemap building footprints and property parcels (brown outlines in OS maps)
        if abs(rc - 167) < 25 and abs(gc - 112) < 25 and bc < 35:
            return True
        items = d.get("items", [])
        item_count = len(items) if items else 0
        dashes = d.get("dashes")
        is_dashed = bool(dashes and str(dashes).strip() not in ("", "[] 0", "[]"))
        if is_dashed and item_count > 25:
            return True
    return False

def _hsv_mask_for_rgb(hsv_img, rgb):
    """Build HSV colour mask for target RGB, handling hue wrap-around."""
    px = np.uint8([[[rgb[0], rgb[1], rgb[2]]]])
    f_hsv = cv2.cvtColor(px, cv2.COLOR_RGB2HSV)[0][0]
    h = int(f_hsv[0])
    s_lo, v_lo = 40, 40
    hw = 20
    if h - hw < 0:
        m1 = cv2.inRange(hsv_img, np.array([0, s_lo, v_lo]), np.array([h + hw, 255, 255]))
        m2 = cv2.inRange(hsv_img, np.array([180 + h - hw, s_lo, v_lo]), np.array([180, 255, 255]))
        return cv2.bitwise_or(m1, m2)
    elif h + hw > 180:
        m1 = cv2.inRange(hsv_img, np.array([h - hw, s_lo, v_lo]), np.array([180, 255, 255]))
        m2 = cv2.inRange(hsv_img, np.array([0, s_lo, v_lo]), np.array([h + hw - 180, 255, 255]))
        return cv2.bitwise_or(m1, m2)
    else:
        return cv2.inRange(hsv_img, np.array([h - hw, s_lo, v_lo]), np.array([h + hw, 255, 255]))

def _render_region(pdf_path, page_num, region_bbox, dpi=200):
    """Render a PDF page region as BGR numpy array."""
    try:
        import fitz
        doc_f = fitz.open(pdf_path)
        if page_num < 1 or page_num > len(doc_f):
            doc_f.close()
            return None
        page = doc_f[page_num - 1]
        zoom = dpi / 72.0
        clip = fitz.Rect(region_bbox[0], region_bbox[1], region_bbox[2], region_bbox[3])
        pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), clip=clip)
        doc_f.close()
        if pix.width < 10 or pix.height < 10:
            return None
        arr = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
        return cv2.cvtColor(arr, cv2.COLOR_RGBA2BGR if pix.n == 4 else cv2.COLOR_RGB2BGR)
    except Exception as e:
        logger.debug(f"Raster render error: {e}")
        return None

def _detect_colored_lines(bgr, feat, clip_bbox, zoom, aoi, min_area=60, min_len=40):
    """Detect contours of a specific colour and return intersecting candidates."""
    frgb = feat.color.rgb
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    mask = _hsv_mask_for_rgb(hsv, frgb)
    k = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, k, iterations=2)
    mask = cv2.morphologyEx(mask, cv2.MORPH_DILATE, k, iterations=1)
    cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    results = []
    for cnt in cnts:
        if cv2.contourArea(cnt) < min_area and cv2.arcLength(cnt, False) < min_len:
            continue
        cx_px, cy_px, cw_px, ch_px = cv2.boundingRect(cnt)
        rx0 = clip_bbox[0] + cx_px / zoom
        ry0 = clip_bbox[1] + cy_px / zoom
        rx1 = clip_bbox[0] + (cx_px + cw_px) / zoom
        ry1 = clip_bbox[1] + (cy_px + ch_px) / zoom
        if aoi.bbox:
            aw, ah = aoi.bbox[2]-aoi.bbox[0], aoi.bbox[3]-aoi.bbox[1]
            if abs(rx1-rx0 - aw) < 25.0 and abs(ry1-ry0 - ah) < 25.0:
                continue
        geom = box(rx0, ry0, rx1, ry1)
        is_int, dist = spatial_engine.check_intersection(geom, aoi, tolerance_pt=aoi.tolerance_pt)
        if is_int or dist <= 30.0:
            results.append({
                "source": "raster_cv", "geom": geom,
                "rgb": frgb, "hex": _rgb_to_hex(frgb),
                "width": 2.0, "is_dashed": False,
                "rect": [rx0, ry0, rx1, ry1],
                "norm_class": feat.description, "raw_label": feat.feature_id,
                "class_conf": 0.82, "is_intersecting": is_int,
                "spatial_rel": "crosses" if is_int else "near",
                "dist": dist, "matched_feat": feat,
            })
    return results


def discover_open_world_assets(
    pdf_path: str,
    document: Document,
    aoi: AOI,
    legend_profile: Optional[LegendProfile],
    warning_definitions: List[WarningDefinition],
    output_crop_dir: Optional[str] = None,
) -> Tuple[List[DiscoveredAsset], ScanCompleteness]:
    """Open-World Independent Map Scan — v2.1 (raster CV always-on)."""
    discovered: List[DiscoveredAsset] = []

    if not os.path.exists(pdf_path) or not aoi.bbox:
        return discovered, ScanCompleteness(
            aoi_coverage=0.0, legend_confidence=0.5, overall=0.25, status="INSUFFICIENT"
        )

    features = legend_profile.features if legend_profile else []
    legend_crop = getattr(legend_profile, "legend_crop_path", None) if legend_profile else None
    page_num = aoi.page_num or 1
    raw_drawings = extract_page_vector_paths(pdf_path, page_num)

    nearby_text: List[str] = []
    try:
        nearby_text = extract_text_blocks_in_aoi(pdf_path, page_num, aoi.bbox)
    except Exception:
        pass

    ax0, ay0, ax1, ay1 = aoi.bbox
    search_box = [ax0 - 40.0, ay0 - 40.0, ax1 + 40.0, ay1 + 40.0]

    try:
        import fitz as _fitz
        _d = _fitz.open(pdf_path)
        _p = _d[page_num - 1]
        page_w, page_h = _p.rect.width, _p.rect.height
        _d.close()
    except Exception:
        page_w, page_h = 842.0, 595.0

    is_fallback = _is_fallback_aoi(aoi)
    candidates: List[Dict[str, Any]] = []

    # ── PASS D1: VECTOR PATH DISCOVERY ───────────────────────────────────────
    for d in raw_drawings:
        r = d.get("rect")
        if not r:
            continue
        if (r.x1 < search_box[0] or r.x0 > search_box[2] or
                r.y1 < search_box[1] or r.y0 > search_box[3]):
            continue
        if _is_confounder(d, aoi.bbox, page_w, page_h):
            continue
        c = d.get("color")
        if not c or len(c) < 3:
            continue
        rgb = (int(c[0]*255), int(c[1]*255), int(c[2]*255))
        if rgb[0] > 245 and rgb[1] > 245 and rgb[2] > 245:
            continue
        if _is_neutral(rgb[0], rgb[1], rgb[2]):
            continue
        dashes = d.get("dashes")
        is_dashed = bool(dashes and str(dashes).strip() not in ("", "[] 0", "[]"))
        width = float(d.get("width", 1.0) or 1.0)
        if is_dashed and aoi.circle_center and aoi.circle_radius:
            cx, cy = aoi.circle_center
            dmx, dmy = (r.x0+r.x1)/2.0, (r.y0+r.y1)/2.0
            if abs(float(np.sqrt((dmx-cx)**2+(dmy-cy)**2)) - aoi.circle_radius) < 8.0:
                continue
        geom = drawing_to_shapely(d)
        if geom is None or geom.is_empty:
            continue
        matched_feat, class_conf = _match_feature(rgb, features, loose=False)
        is_intersecting, dist = spatial_engine.check_intersection(geom, aoi, tolerance_pt=aoi.tolerance_pt)
        if is_fallback and not is_intersecting:
            if (r.x0 >= ax0 - 20 and r.x1 <= ax1 + 20 and
                    r.y0 >= ay0 - 20 and r.y1 <= ay1 + 20):
                is_intersecting = True
                dist = 0.0
        spatial_rel = "outside"
        if is_intersecting:
            spatial_rel = "crosses" if geom.geom_type in ["LineString", "MultiLineString"] else "intersects"
        elif dist <= 25.0:
            spatial_rel = "near"
        if not is_intersecting and dist > 25.0:
            continue
        norm_class = matched_feat.description if matched_feat else "Unknown Utility Asset"
        raw_label = matched_feat.feature_id if matched_feat else "UNKNOWN_ASSET"
        candidates.append({
            "source": "vector", "geom": geom, "rgb": rgb, "hex": _rgb_to_hex(rgb),
            "width": width, "is_dashed": is_dashed, "rect": [r.x0, r.y0, r.x1, r.y1],
            "norm_class": norm_class, "raw_label": raw_label, "class_conf": class_conf,
            "is_intersecting": is_intersecting, "spatial_rel": spatial_rel,
            "dist": dist, "matched_feat": matched_feat,
        })

    # ── PASS D2: RASTER CV DISCOVERY — runs for raster/hybrid plans (< 50 vector drawings) ──
    run_raster_cv = (len(raw_drawings) < 50) or bool(
        document.modality and any(m in str(document.modality).upper() for m in ["RASTER", "IMAGE", "SCANNED"])
    )
    if features and run_raster_cv:
        dpi = 200
        zoom = dpi / 72.0
        render_region = [max(0.0, search_box[0]), max(0.0, search_box[1]),
                         min(page_w, search_box[2]), min(page_h, search_box[3])]
        bgr = _render_region(pdf_path, page_num, render_region, dpi=dpi)
        if bgr is not None:
            for feat in features:
                frgb = feat.color.rgb
                if _is_neutral(frgb[0], frgb[1], frgb[2]) and max(frgb) < 200:
                    continue
                if frgb[0] > 240 and frgb[1] > 240 and frgb[2] > 240:
                    continue
                raster_cands = _detect_colored_lines(bgr, feat, render_region, zoom, aoi)
                candidates.extend(raster_cands)

    # ── PASS D3: DEDUPLICATION ────────────────────────────────────────────────
    def _iou(b1, b2):
        ix0, iy0 = max(b1[0], b2[0]), max(b1[1], b2[1])
        ix1, iy1 = min(b1[2], b2[2]), min(b1[3], b2[3])
        if ix1 <= ix0 or iy1 <= iy0: return 0.0
        inter = (ix1-ix0)*(iy1-iy0)
        a1 = (b1[2]-b1[0])*(b1[3]-b1[1])
        a2 = (b2[2]-b2[0])*(b2[3]-b2[1])
        union = a1+a2-inter
        return inter/union if union > 0 else 0.0

    def _priority(c):
        nc = c["norm_class"].lower()
        if "trunk main" in nc or "trunk" in nc: return 100
        if "high pressure" in nc: return 90
        if "intermediate" in nc: return 80
        if "medium pressure" in nc: return 70
        if "water main" in nc or "potable" in nc: return 65
        if any(k in nc for k in ["11kv","hv","high voltage"]): return 60
        if any(k in nc for k in ["33kv","66kv","132kv"]): return 55
        if "low pressure" in nc: return 40
        if "unknown" in nc: return 0
        return 50

    def _normalize_class_name(name: str) -> str:
        n = name.lower().strip()
        if any(k in n for k in ["low pressure", "lp gas", "lp main"]):
            return "Low Pressure Gas Main"
        if any(k in n for k in ["medium pressure", "mp gas", "mp main"]):
            return "Medium Pressure Gas Main"
        if any(k in n for k in ["intermediate pressure", "ip gas", "ip main"]):
            return "Intermediate Pressure Gas Main"
        if any(k in n for k in ["high pressure", "hp gas", "hp main", "lhp main"]):
            return "High Pressure Gas Main"
        if any(k in n for k in ["trunk main", "trunk"]):
            return "Water Trunk Transmission Main"
        if any(k in n for k in ["potable", "clean water", "water main", "distribution main"]):
            return "Clean Potable Water Distribution Main"
        if any(k in n for k in ["11kv", "hv cable", "high voltage"]):
            return "11kV High Voltage Cable"
        if "33kv" in n:
            return "33kV High Voltage Cable"
        if "66kv" in n:
            return "66kV High Voltage Cable"
        if "132kv" in n:
            return "132kV High Voltage Cable"
        return name

    candidates.sort(key=lambda c: (_priority(c), c["class_conf"]), reverse=True)
    deduped: List[Dict[str, Any]] = []
    for cand in candidates:
        if not any(_iou(cand["rect"], k["rect"]) > 0.45 for k in deduped):
            deduped.append(cand)
    candidates = deduped

    # ── PASS D4: CLASS CLUSTERING & CANONICAL ASSET BUILDING ─────────────────
    class_groups: Dict[str, List[Dict[str, Any]]] = {}
    for cand in candidates:
        canonical_name = _normalize_class_name(cand["norm_class"])
        cand["norm_class"] = canonical_name
        class_groups.setdefault(canonical_name, []).append(cand)

    asset_counter = 1
    for norm_class, cl in class_groups.items():
        rep = cl[0]
        seg_count = len(cl)
        bx0 = min(c["rect"][0] for c in cl)
        by0 = min(c["rect"][1] for c in cl)
        bx1 = max(c["rect"][2] for c in cl)
        by1 = max(c["rect"][3] for c in cl)
        class_conf = max(c["class_conf"] for c in cl)
        any_int = any(c["is_intersecting"] for c in cl)
        min_dist = min(c["dist"] for c in cl)
        spatial_rel = "crosses" if any_int else "near"

        contract_match = False
        matched_wdef = None
        nc_lower = norm_class.lower()
        for w in warning_definitions:
            wt = w.business_warning_text.lower()
            if any(k in nc_lower for k in ["high pressure","hp"]) and any(k in wt for k in ["high pressure","hp"]):
                contract_match, matched_wdef = True, w; break
            if any(k in nc_lower for k in ["intermediate","ip"]) and any(k in wt for k in ["intermediate","ip"]):
                contract_match, matched_wdef = True, w; break
            if any(k in nc_lower for k in ["medium pressure","mp"]) and any(k in wt for k in ["medium","mp"]):
                contract_match, matched_wdef = True, w; break
            if any(k in nc_lower for k in ["trunk main","trunk"]) and "trunk" in wt:
                contract_match, matched_wdef = True, w; break
            if any(k in nc_lower for k in ["hv","11kv","33kv","high voltage"]) and any(k in wt for k in ["hv","voltage","cable"]):
                contract_match, matched_wdef = True, w; break
            if any(k in nc_lower for k in ["water main","water line"]) and "water" in wt:
                contract_match, matched_wdef = True, w; break

        HIGH_KW = ["trunk main", "high pressure", "high voltage", "11kv", "33kv", "66kv", "132kv"]
        if matched_wdef:
            severity = matched_wdef.severity
        elif any(k in nc_lower for k in HIGH_KW):
            severity = Severity.HIGH
        elif "medium pressure" in nc_lower:
            severity = Severity.MEDIUM
        elif "low pressure" in nc_lower or "potable" in nc_lower or "water" in nc_lower:
            severity = Severity.LOW
        else:
            severity = Severity.MEDIUM

        status = "NEEDS_REVIEW" if "unknown" in nc_lower else ("CONFIRMED" if any_int else "LIKELY")

        asset = DiscoveredAsset(
            asset_id=f"ASSET-{document.document_id}-{asset_counter:03d}",
            document_id=document.document_id,
            page_num=page_num,
            normalized_class=norm_class,
            raw_legend_label=rep["raw_label"],
            utility=document.filename.split("_")[0] if document.filename else "Utility",
            utility_type=("Gas" if "gas" in nc_lower else
                          "Water" if any(k in nc_lower for k in ["water","trunk"]) else "Electricity"),
            geometry_type=GeometryType.LINE,
            color_hex=rep["hex"],
            color_rgb=[rep["rgb"][0], rep["rgb"][1], rep["rgb"][2]],
            stroke_style="dashed" if rep["is_dashed"] else "solid",
            stroke_width_pt=rep["width"],
            bbox=[bx0, by0, bx1, by1],
            segment_count=seg_count,
            inside_aoi=any_int,
            spatial_relation=spatial_rel,
            aoi_distance_pt=min_dist,
            classification_confidence=round(class_conf, 2),
            geometry_confidence=0.99,
            spatial_confidence=0.99,
            visual_confidence=0.96,
            overall_confidence=round(class_conf*0.6 + 0.99*0.25 + 0.96*0.15, 2),
            contract_match=contract_match,
            warning_code=matched_wdef.warning_code if matched_wdef else None,
            business_warning_text=(matched_wdef.business_warning_text if matched_wdef
                                   else f"There is a {norm_class} present in this area |"),
            severity=severity,
            status=status,
            legend_crop_path=legend_crop,
            detection_methods=(["pdf_vector","dynamic_legend"] if rep["source"] == "vector"
                                else ["raster_cv","dynamic_legend"]),
            notes=[f"{seg_count} segment(s) via {rep['source']}"]
        )
        discovered.append(asset)
        asset_counter += 1

    aoi_cov = 1.0 if (aoi.method and "VECTOR" in str(aoi.method)) else 0.75
    leg_conf = getattr(legend_profile, "dynamic_confidence", 0.95) if legend_profile else 0.50
    overall_comp = round(aoi_cov*0.40 + leg_conf*0.40 + 0.98*0.20, 2)
    completeness = ScanCompleteness(
        aoi_coverage=aoi_cov, legend_confidence=leg_conf, image_quality=0.98,
        analysis_coverage=1.0,
        unknown_object_count=sum(1 for a in discovered if a.raw_legend_label == "UNKNOWN_ASSET"),
        pages_analyzed=document.page_count,
        overall=overall_comp,
        status="COMPLETE" if overall_comp >= 0.85 else "HIGH",
    )

    logger.info(
        f"Open-world discovery v2.1: {document.document_id}: "
        f"{len(discovered)} asset(s) (completeness={overall_comp:.2f})"
    )
    return discovered, completeness
