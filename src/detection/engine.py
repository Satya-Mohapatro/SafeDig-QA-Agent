import os
from typing import List, Optional
from shapely.geometry import box
from src.domain.document import Document
from src.domain.aoi import AOI
from src.domain.warning import WarningDefinition
from src.domain.legend import LegendProfile
from src.domain.detection import DetectedCandidate
from src.domain.enums import DetectionMethod, Severity, GeometryType
from src.pdf.extractor import extract_page_vector_paths, extract_text_blocks_in_aoi
from src.vector.analyzer import filter_drawings_by_style
from src.vector.geometry import drawing_to_shapely
from src.spatial.engine import spatial_engine
from src.config.logging import logger


def detect_independent_warnings(
    pdf_path: str,
    document: Document,
    aoi: AOI,
    warning_definitions: List[WarningDefinition],
    legend_profile: Optional[LegendProfile]
) -> List[DetectedCandidate]:
    """Perform independent spatial QA scan inside the AOI boundary.

    Pipeline:
    1. For each legend feature (asset type), filter all vector drawings by stroke color and width.
    2. Exclude dashed/dotted lines to avoid misidentifying the AOI enquiry boundary itself.
    3. Convert each matched drawing to a Shapely geometry (line, polygon, curve).
    4. Spatially test whether the geometry intersects or is within the AOI + tolerance buffer.
    5. Optionally confirm detection by checking text labels inside the AOI.
    6. Return a typed DetectedCandidate list for downstream reconciliation.
    """
    candidates: List[DetectedCandidate] = []

    if not legend_profile or not os.path.exists(pdf_path):
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
            # Find matching warning definition
            matching_wdefs = [
                w for w in warning_definitions
                if feat.warning_code in w.warning_code or w.warning_code in feat.warning_code
            ]
            if not matching_wdefs:
                wdef = WarningDefinition(
                    warning_code=feat.warning_code,
                    provider=legend_profile.provider,
                    utility_type=legend_profile.utility_type,
                    business_warning_text=feat.description,
                    severity=Severity.HIGH if ("HP" in feat.feature_id or "HV" in feat.feature_id
                                               or "TRUNK" in feat.feature_id) else Severity.MEDIUM,
                    geometry_type=feat.geometry_type,
                    aoi_required=True
                )
            else:
                wdef = matching_wdefs[0]

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
