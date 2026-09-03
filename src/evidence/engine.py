import os
from typing import List, Optional
from src.domain.document import Document
from src.domain.aoi import AOI
from src.domain.reconciliation import ReconciliationResult
from src.domain.evidence import EvidenceItem, EvidencePackage
from src.domain.enums import ReconciliationOutcome
from .crops import generate_evidence_crop
from .completeness import verify_evidence_completeness
from src.config.settings import settings
from src.config.logging import logger

def build_evidence_package(
    pdf_path: str,
    document: Optional[Document],
    aoi: Optional[AOI],
    reconciliation: ReconciliationResult,
    output_dir: Optional[str] = None
) -> EvidencePackage:
    # Guard: if no document, return a minimal package (e.g., for excluded rows)
    if document is None:
        return EvidencePackage(
            package_id=f"PKG-{reconciliation.document_id}-EXCLUDED",
            document_id=reconciliation.document_id,
            items=[],
            is_complete=True  # No validation needed for excluded rows
        )
    
    ev_dir = output_dir or os.path.join(settings.output_dir, "evidence")
    os.makedirs(ev_dir, exist_ok=True)
    
    pkg_id = f"PKG-{document.document_id}"
    items: List[EvidenceItem] = []
    item_counter = 1
    
    # 1. Source file SHA-256 integrity evidence
    items.append(EvidenceItem(
        evidence_id=f"E-{document.document_id}-{item_counter:04d}",
        document_id=document.document_id,
        page_num=1,
        evidence_type="SOURCE_FILE",
        description=f"Source file {document.filename} verified with SHA-256 hash",
        data={"sha256": document.sha256, "page_count": document.page_count, "modality": document.modality.value}
    ))
    item_counter += 1
    
    # 2. AOI geometry evidence & visual overview crop
    aoi_crop_path = os.path.join(ev_dir, f"aoi_overview_{document.document_id}.png")
    aoi_crop_generated = False
    if os.path.exists(pdf_path):
        from .crops import generate_aoi_map_render
        aoi_bbox = aoi.bbox if aoi else None
        p_num = aoi.page_num if aoi else 1
        res = generate_aoi_map_render(pdf_path, p_num, aoi_bbox, aoi_crop_path)
        aoi_crop_generated = res is not None and os.path.exists(aoi_crop_path)

    if aoi is not None:
        items.append(EvidenceItem(
            evidence_id=f"E-{document.document_id}-{item_counter:04d}",
            document_id=document.document_id,
            page_num=aoi.page_num,
            evidence_type="AOI_GEOMETRY",
            description=f"AOI established via {aoi.method.value} with confidence {aoi.confidence:.2f}",
            data={"method": aoi.method.value, "bbox": aoi.bbox, "is_valid": aoi.is_valid,
                  "confidence": aoi.confidence},
            crop_image_path=aoi_crop_path if aoi_crop_generated else None
        ))
        item_counter += 1
    elif aoi_crop_generated:
        items.append(EvidenceItem(
            evidence_id=f"E-{document.document_id}-{item_counter:04d}",
            document_id=document.document_id,
            page_num=1,
            evidence_type="AOI_GEOMETRY",
            description="Visual map overview render",
            crop_image_path=aoi_crop_path
        ))
        item_counter += 1

    
    # 3. Spatial intersection and visual crop evidence for each detection
    for cand in reconciliation.detected_candidates:
        crop_name = f"crop_{document.document_id}_{cand.candidate_id}.png"
        crop_path = os.path.join(ev_dir, crop_name)
        crop_generated = False
        
        if cand.bbox and len(cand.bbox) == 4 and os.path.exists(pdf_path):
            result = generate_evidence_crop(pdf_path, cand.page_num, cand.bbox, crop_path)
            crop_generated = result is not None and os.path.exists(crop_path)
        
        # Spatial intersection item
        items.append(EvidenceItem(
            evidence_id=f"E-{document.document_id}-{item_counter:04d}",
            document_id=document.document_id,
            page_num=cand.page_num,
            evidence_type="SPATIAL_INTERSECTION",
            description=f"Detected '{cand.business_warning_text}' intersecting AOI (distance={cand.aoi_distance_pt:.1f}pt, conf={cand.confidence:.2f})",
            data={"warning_code": cand.warning_code, "severity": cand.severity.value,
                  "confidence": cand.confidence, "bbox": cand.bbox},
            crop_image_path=crop_path if crop_generated else None
        ))
        item_counter += 1
        
        # Separate MAP_CROP item when crop was successfully generated
        if crop_generated:
            items.append(EvidenceItem(
                evidence_id=f"E-{document.document_id}-{item_counter:04d}",
                document_id=document.document_id,
                page_num=cand.page_num,
                evidence_type="MAP_CROP",
                description=f"Visual crop of map region around detected {cand.warning_code}",
                data={"candidate_id": cand.candidate_id, "warning_code": cand.warning_code},
                crop_image_path=crop_path
            ))
            item_counter += 1
        
    pkg = EvidencePackage(
        package_id=pkg_id,
        document_id=document.document_id,
        items=items,
        is_complete=False
    )
    
    verify_evidence_completeness(pkg, reconciliation)
    reconciliation.evidence_ids = [it.evidence_id for it in items]
    
    logger.info(f"Built evidence package {pkg_id} with {len(items)} items (is_complete={pkg.is_complete})")
    return pkg
