import os
from typing import List, Optional, Any
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
    legend_profile: Optional[LegendProfile],
    discovered_assets: Optional[List[Any]] = None
) -> List[DetectedCandidate]:
    """Perform independent open-world spatial QA scan inside the AOI boundary.
    
    Uses discovery.py to locate all physical assets (vector and raster), matches them
    against dynamic on-map legend features, deduplicates them, and maps high-risk assets
    to DetectedCandidate objects for policy gating and reconciliation.
    """
    if discovered_assets is None:
        from src.detection.discovery import discover_open_world_assets
        discovered_assets, _ = discover_open_world_assets(
            pdf_path=pdf_path,
            document=document,
            aoi=aoi,
            legend_profile=legend_profile,
            warning_definitions=warning_definitions
        )
    
    candidates: List[DetectedCandidate] = []
    cand_counter = 1
    
    for a in discovered_assets:
        # Only keep assets intersecting or crossing AOI
        if not a.inside_aoi:
            continue
            
        # Only active HIGH severity hazards (or contractual HIGH warnings) block policy
        # Per warnings_list.xlsx, Medium severity assets (e.g. Medium Pressure Gas) do not block release
        is_hazard = (
            (a.contract_match and a.severity in [Severity.HIGH, Severity.CRITICAL])
            or a.severity in [Severity.HIGH, Severity.CRITICAL]
            or any(kw in a.normalized_class.lower() for kw in [
                "trunk main", "high pressure", "11kv", "33kv", "132kv", "high voltage"
            ])
        )
        if not is_hazard:
            continue
            
        cand = DetectedCandidate(
            candidate_id=f"CAND-{document.document_id}-{cand_counter:04d}",
            document_id=document.document_id,
            page_num=a.page_num,
            warning_code=a.warning_code or a.raw_legend_label or a.normalized_class.upper().replace(" ", "_"),
            business_warning_text=a.business_warning_text or f"There is a {a.normalized_class} in this area |",
            severity=a.severity if a.severity != Severity.UNKNOWN else Severity.HIGH,
            detection_method=DetectionMethod.VECTOR_ANALYSIS,
            geometry_type=a.geometry_type,
            bbox=a.bbox,
            confidence=a.classification_confidence,
            intersects_aoi=True,
            aoi_distance_pt=a.aoi_distance_pt,
            evidence_ids=[]
        )
        candidates.append(cand)
        cand_counter += 1

    logger.info(f"Independent discovery mapped {len(candidates)} reportable candidate(s) for {document.document_id}")
    return candidates

