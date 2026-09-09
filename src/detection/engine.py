import os
from typing import List, Optional
from shapely.geometry import box
from src.domain.document import Document
from src.domain.aoi import AOI
from src.domain.warning import WarningDefinition
from src.domain.legend import LegendProfile, LegendFeature
from src.domain.detection import DetectedCandidate
from src.domain.enums import DetectionMethod, Severity, GeometryType
from src.pdf.extractor import extract_page_vector_paths, extract_text_blocks_in_aoi
from src.vector.analyzer import filter_drawings_by_style
from src.vector.geometry import drawing_to_shapely
from src.spatial.engine import spatial_engine
from src.config.logging import logger


def _match_feature_to_warning(
    feat: LegendFeature,
    warning_defs: List[WarningDefinition]
) -> Optional[WarningDefinition]:
    """Find matching active HIGH warning definition for this legend feature."""
    if not warning_defs:
        return None
    feat_id = feat.feature_id.upper()
    feat_code = feat.warning_code.upper()
    feat_desc = feat.description.upper()

    for w in warning_defs:
        if w.severity != Severity.HIGH:
            continue
        w_code = w.warning_code.upper()
        w_text = w.business_warning_text.upper()

        # 1. Exact or substring code match
        if feat_code in w_code or w_code in feat_code:
            return w

        # 2. Key semantic indicators match
        # Gas High Pressure / Intermediate Pressure / LHP
        if ("HP" in feat_id or "HIGH PRESSURE" in feat_desc) and ("HIGH PRESSURE" in w_text or "HP" in w_text):
            return w
        if ("IP" in feat_id or "INTERMEDIATE" in feat_desc) and ("INTERMEDIATE" in w_text or "LHP" in w_text):
            return w

        # Electricity High Voltage
        if ("HV" in feat_id or "11KV" in feat_id or "33KV" in feat_id or "HIGH VOLTAGE" in feat_desc) and (
            "HV" in w_text or "HIGH VOLTAGE" in w_text or "11KV" in w_text or "33KV" in w_text
            or "66KV" in w_text or "132KV" in w_text or "UNDERGROUND CABLE" in w_text
        ):
            return w

        # Water Trunk Main
        if "TRUNK" in feat_id and "TRUNK" in w_text:
            return w

    return None


def detect_independent_warnings(
    pdf_path: str,
    document: Document,
    aoi: AOI,
    warning_definitions: List[WarningDefinition],
    legend_profile: Optional[LegendProfile]
) -> List[DetectedCandidate]:
    """Perform independent spatial QA scan inside the AOI boundary.

    Pipeline:
    1. Strictly filter for active HIGH warning definitions from warnings_list.xlsx.
       If the utility has no active HIGH warnings, return immediately (automatic pass).
    2. For each matching high-hazard legend feature, filter vector drawings by style.
    3. Exclude dashed/dotted lines to avoid misidentifying the AOI enquiry boundary itself.
    4. Convert each matched drawing to a Shapely geometry (line, polygon, curve).
    5. Spatially test whether the geometry intersects or is within the AOI + tolerance buffer.
    6. Return typed DetectedCandidate list with Severity.HIGH for downstream reconciliation.
    """
    candidates: List[DetectedCandidate] = []

    # If utility has no active high warnings, or no legend / pdf, exit immediately.
    # Per operational safety requirement: utilities with no warnings pass automatically.
    if not warning_definitions or not legend_profile or not os.path.exists(pdf_path):
        return candidates

    cand_counter = 1

    for page_idx in range(1, document.page_count + 1):
        drawings = extract_page_vector_paths(pdf_path, page_idx)

        # Extract all text labels inside AOI for label cross-check
        aoi_text_labels: List[str] = []
        if aoi.bbox:
            try:
                aoi_text_labels = [t.upper() for t in
                                   extract_text_blocks_in_aoi(pdf_path, page_idx, aoi.bbox)]
            except Exception:
                aoi_text_labels = []

        for feat in legend_profile.features:
            # Strictly match against registered HIGH warning definitions
            wdef = _match_feature_to_warning(feat, warning_definitions)
            if not wdef:
                # Feature is not a registered HIGH warning for this utility; skip!
                # Do NOT synthesize fake medium warnings.
                continue


            # Filter drawings by legend stroke color and width.
            # Crucially exclude_dashed=True so the magenta AOI boundary itself
            # (which can be red on some providers) is never confused with a utility line.
            matched_drawings = filter_drawings_by_style(
                drawings=drawings,
                target_rgb=feat.color.rgb,
                min_width=feat.stroke.min_width_pt,
                max_width=feat.stroke.max_width_pt,
                tolerance=feat.color.tolerance,
                exclude_dashed=True
            )

            # Text label booster: also check AOI text for feature labels
            text_match_boost = False
            if feat.text_labels and aoi_text_labels:
                for lbl in feat.text_labels:
                    if any(lbl.upper() in t for t in aoi_text_labels):
                        text_match_boost = True
                        break

            for md in matched_drawings:
                geom = drawing_to_shapely(md)
                if geom is None or geom.is_empty:
                    continue

                is_intersecting, dist = spatial_engine.check_intersection(
                    geom, aoi, tolerance_pt=aoi.tolerance_pt
                )

                # If warning requires AOI intersection, only record if intersecting
                if wdef.aoi_required and not is_intersecting:
                    continue

                rect = md.get("rect")
                bbox = [rect.x0, rect.y0, rect.x1, rect.y1] if rect else [0, 0, 0, 0]

                # Confidence: boost to 0.99 if text label inside AOI also matches
                confidence = 0.99 if text_match_boost else 0.96

                cand = DetectedCandidate(
                    candidate_id=f"CAND-{document.document_id}-{cand_counter:04d}",
                    document_id=document.document_id,
                    page_num=page_idx,
                    warning_code=wdef.warning_code,
                    business_warning_text=wdef.business_warning_text,
                    severity=wdef.severity,
                    detection_method=DetectionMethod.VECTOR_ANALYSIS,
                    geometry_type=wdef.geometry_type,
                    bbox=bbox,
                    confidence=confidence,
                    intersects_aoi=is_intersecting,
                    aoi_distance_pt=dist,
                    evidence_ids=[]
                )
                candidates.append(cand)
                cand_counter += 1

            # If no vector drawings matched, but text label strongly indicates this asset
            # inside the AOI, record a text-evidence candidate
            if text_match_boost and not any(
                c.warning_code == wdef.warning_code for c in candidates
                if c.document_id == document.document_id
            ):
                if aoi.bbox:
                    ax0, ay0, ax1, ay1 = aoi.bbox
                    cand = DetectedCandidate(
                        candidate_id=f"CAND-{document.document_id}-{cand_counter:04d}",
                        document_id=document.document_id,
                        page_num=page_idx,
                        warning_code=wdef.warning_code,
                        business_warning_text=wdef.business_warning_text,
                        severity=wdef.severity,
                        detection_method=DetectionMethod.TEXT_LABEL,
                        geometry_type=wdef.geometry_type,
                        bbox=[ax0, ay0, ax1, ay1],
                        confidence=0.85,
                        intersects_aoi=True,
                        aoi_distance_pt=0.0,
                        evidence_ids=[]
                    )
                    candidates.append(cand)
                    cand_counter += 1

    logger.info(f"Independent detection found {len(candidates)} candidates for {document.document_id}")
    return candidates
