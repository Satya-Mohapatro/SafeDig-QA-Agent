import os
from typing import Dict, Any, Optional, List
from src.domain.index_record import IndexRecord
from src.domain.document import Document, DiscoveredFile
from src.domain.aoi import AOI
from src.domain.legend import LegendProfile
from src.domain.reconciliation import ReconciliationResult
from src.domain.evidence import EvidencePackage
from src.domain.policy import PolicyResult
from src.api.schemas import ReviewWorkspacePayload
from src.pdf import inspect_pdf
from src.aoi import get_document_aoi
from src.legends import resolve_legend
from src.warnings import master_warning_catalogue
from src.detection import detect_independent_warnings
from src.reconciliation import reconcile_warnings
from src.evidence import build_evidence_package
from src.policy import policy_engine
from src.agent import advisory_service

class WorkspacePayloadBuilder:
    @staticmethod
    def build_workspace_payload(
        job_id: str,
        root_dir: str,
        record: IndexRecord,
        matched_file: DiscoveredFile,
        output_dir: Optional[str] = None
    ) -> ReviewWorkspacePayload:
        pdf_path = matched_file.metadata.get("full_path", os.path.join(root_dir, matched_file.filename))
        doc_id = f"DOC-{matched_file.file_id}"
        from src.config.settings import settings
        out_dir = output_dir or os.path.join(settings.output_dir, job_id)

        
        # 1. PDF Inspection
        doc_obj = inspect_pdf(pdf_path, doc_id, job_id, matched_file.file_id, matched_file.sha256)
        
        # 2. Legend & AOI
        legend = resolve_legend(record.utility_name)
        aoi = get_document_aoi(pdf_path, doc_id, page_num=1)
        wdefs = master_warning_catalogue.get_definitions_for_provider(record.utility_name)
        
        # 3. Detections & Reconciliation
        from src.domain.warning import ClaimedWarning
        from src.domain.enums import Severity
        claimed_w = None
        if record.raw_warning and record.raw_warning.strip():
            matched_wdef = master_warning_catalogue.find_by_text(record.raw_warning)
            claimed_w = ClaimedWarning(
                claimed_warning_id=f"CLM-{doc_id}",
                document_id=doc_id,
                index_record_id=record.index_record_id,
                warning_code=matched_wdef.warning_code if matched_wdef else "CLAIMED_WARNING",
                raw_warning_text=record.raw_warning,
                severity=matched_wdef.severity if matched_wdef else Severity.MEDIUM
            )
            
        detected_cands = detect_independent_warnings(pdf_path, doc_obj, aoi, wdefs, legend)
        reconcil_res = reconcile_warnings(doc_id, claimed_w, detected_cands)
        
        # 4. Evidence Package
        ev_pkg = build_evidence_package(pdf_path, doc_obj, aoi, reconcil_res, output_dir=os.path.join(out_dir, "evidence"))
        
        # 5. Policy Gates
        pol_res = policy_engine.evaluate(record, doc_obj, legend, aoi, reconcil_res, ev_pkg)
        
        # 6. Advisory Briefing
        adv = advisory_service.generate_advisory(doc_obj, reconcil_res, ev_pkg, pol_res)
        
        # Assemble complete payload
        legend_feats = []
        if legend:
            for feat in legend.features:
                legend_feats.append({
                    "feature_id": feat.feature_id,
                    "warning_code": feat.warning_code,
                    "description": feat.description,
                    "rgb": feat.color.rgb,
                    "min_width": feat.stroke.min_width_pt,
                    "max_width": feat.stroke.max_width_pt
                })
                
        evidence_items_data = []
        for it in ev_pkg.items:
            evidence_items_data.append({
                "evidence_id": it.evidence_id,
                "evidence_type": it.evidence_type,
                "description": it.description,
                "data": it.data,
                "crop_image_path": it.crop_image_path,
                "crop_url": f"/api/v1/evidence/{job_id}/{doc_id}/crop/{os.path.basename(it.crop_image_path)}" if it.crop_image_path else None
            })
            
        indep_findings_data = []
        for c in detected_cands:
            indep_findings_data.append({
                "candidate_id": c.candidate_id,
                "warning_code": c.warning_code,
                "business_warning_text": c.business_warning_text,
                "severity": c.severity.value,
                "confidence": c.confidence,
                "intersects_aoi": c.intersects_aoi,
                "distance_pt": c.aoi_distance_pt,
                "bbox": c.bbox
            })
            
        gates_dict = {k: v.model_dump() for k, v in pol_res.gates.items()}
        
        return ReviewWorkspacePayload(
            job_id=job_id,
            document_id=doc_id,
            index_record_id=record.index_record_id,
            filename=matched_file.filename,
            utility_name=record.utility_name,
            utility_type=record.utility_type,
            page_count=doc_obj.page_count,
            modality=doc_obj.modality.value,
            pdf_path=pdf_path,
            aoi_method=aoi.method.value,
            aoi_confidence=aoi.confidence,
            aoi_bbox=aoi.bbox,
            aoi_coordinates=aoi.coordinates,
            reconciliation_outcome=reconcil_res.outcome.value,
            upstream_claim=record.raw_warning,
            independent_findings=indep_findings_data,
            legend_id=legend.legend_id if legend else None,
            legend_features=legend_feats,
            evidence_package_id=ev_pkg.package_id,
            evidence_items=evidence_items_data,
            advisory=adv.model_dump(),
            decision=pol_res.decision.value,
            reason=pol_res.reason,
            gates=gates_dict
        )

workspace_builder = WorkspacePayloadBuilder()
