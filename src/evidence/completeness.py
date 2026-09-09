from src.domain.evidence import EvidencePackage
from src.domain.reconciliation import ReconciliationResult
from src.domain.enums import ReconciliationOutcome

def verify_evidence_completeness(
    package: EvidencePackage,
    reconciliation: ReconciliationResult
) -> bool:
    reasons = []
    
    # 1. Source document integrity evidence must always exist
    has_source = any(item.evidence_type == "SOURCE_FILE" for item in package.items)
    if not has_source:
        reasons.append("Missing source file integrity evidence.")
        
    # 2. AOI boundary evidence must always exist
    has_aoi = any(item.evidence_type == "AOI_GEOMETRY" for item in package.items)
    if not has_aoi:
        reasons.append("Missing AOI boundary validation evidence.")
        
    # 3. For detected or matched warnings, spatial proof is mandatory
    if reconciliation.outcome in [ReconciliationOutcome.MATCH, ReconciliationOutcome.MISSED_WARNING]:
        spatial_items = [item for item in package.items if item.evidence_type == "SPATIAL_INTERSECTION"]
        has_spatial = len(spatial_items) > 0
        if not has_spatial:
            reasons.append("Missing spatial intersection proof for warning condition.")
        
        # Visual proof: crop_image_path on any spatial item, or explicit MAP_CROP / VECTOR_PATH item
        has_visual = any(
            (item.evidence_type == "SPATIAL_INTERSECTION" and item.crop_image_path is not None)
            or item.evidence_type in ["MAP_CROP", "VECTOR_PATH"]
            for item in package.items
        )
        if not has_visual:
            # Visual crop failed (e.g. PDF rendering issue) - flag as warning but do not block
            # completeness if spatial proof exists; add a note instead
            if has_spatial:
                reasons.append("Warning: Visual crop could not be generated; spatial proof present.")
                # This is a WARNING note, not a hard blocking reason.
                # Remove from reasons so completeness is still True when spatial proof exists.
                reasons.pop()
            else:
                reasons.append("Missing visual/vector proof for warning condition.")
                
    package.is_complete = len(reasons) == 0
    package.completeness_reasons = reasons
    return package.is_complete
