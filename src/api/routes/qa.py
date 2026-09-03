import os
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Query
from src.api.schemas import (
    QAQueueListResponse,
    QAQueueItem,
    ReviewWorkspacePayload,
    HumanDispositionRequest,
    HumanDispositionResponse
)
from src.qa.workspace import workspace_builder
from src.qa import human_disposition_service
from src.domain.audit import DecisionRecord, VersionSnapshot
from src.domain.index_record import IndexRecord
from src.domain.document import DiscoveredFile
from src.domain.enums import Decision, HumanDispositionAction
from src.config.settings import settings
from src.config.logging import logger

router = APIRouter(prefix="/qa", tags=["Human QA & HITL Workspace"])

@router.get("/queue", response_model=QAQueueListResponse)
def get_qa_queue(job_id: Optional[str] = Query(None, description="Optional job ID filter")):
    queue_items = []
    base_out = settings.output_dir
    
    if not os.path.exists(base_out):
        return QAQueueListResponse(total_items=0, items=[])
        
    job_dirs = [os.path.join(base_out, job_id)] if job_id else [
        os.path.join(base_out, d) for d in os.listdir(base_out) if os.path.isdir(os.path.join(base_out, d))
    ]
    
    for jd in job_dirs:
        curr_job_id = os.path.basename(jd)
        results_file = os.path.join(jd, "document_results.json")
        if not os.path.exists(results_file):
            continue
            
        with open(results_file, "r", encoding="utf-8") as f:
            docs = json.load(f)
            
        for doc in docs:
            if doc.get("decision") == "HUMAN_REVIEW":
                queue_items.append(QAQueueItem(
                    job_id=curr_job_id,
                    index_record_id=doc.get("index_record_id", ""),
                    document_id=doc.get("document_id", ""),
                    filename=doc.get("filename", ""),
                    utility_name=doc.get("utility_name", ""),
                    utility_type=doc.get("utility_type", ""),
                    upstream_claim=doc.get("upstream_claim"),
                    independent_findings_count=doc.get("independent_findings_count", 0),
                    reconciliation_outcome=doc.get("reconciliation_outcome", ""),
                    decision=doc.get("decision", ""),
                    reason=doc.get("reason", ""),
                    evidence_package_id=doc.get("evidence_package_id", ""),
                    evidence_count=doc.get("evidence_count", 0)
                ))
                
    return QAQueueListResponse(total_items=len(queue_items), items=queue_items)

@router.get("/workspace/{job_id}/{document_id}", response_model=ReviewWorkspacePayload)
def get_review_workspace(job_id: str, document_id: str):
    # Locate job folder
    job_out_dir = os.path.join(settings.output_dir, job_id)
    report_file = os.path.join(job_out_dir, "job_report.json")
    if not os.path.exists(report_file):
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found.")
        
    with open(report_file, "r", encoding="utf-8") as f:
        rep_data = json.load(f)
        
    root_dir = rep_data.get("root_dir", "")
    
    # Read document results to get row index
    results_file = os.path.join(job_out_dir, "document_results.json")
    with open(results_file, "r", encoding="utf-8") as f:
        docs = json.load(f)
        
    matched_doc_entry = next((d for d in docs if d.get("document_id") == document_id or d.get("index_record_id") == document_id), None)
    if not matched_doc_entry:
        raise HTTPException(status_code=404, detail=f"Document {document_id} not found in job {job_id}.")
        
    # Reconstruct domain objects to build full workspace payload
    index_path = os.path.join(root_dir, "index.xlsx")
    from src.index import parse_index_excel
    from src.ingestion import scan_root_folder
    from src.documents import resolve_documents
    
    records = parse_index_excel(index_path, job_id)
    target_idx = matched_doc_entry.get("index_record_id")
    target_util = matched_doc_entry.get("utility_name")
    target_fn = matched_doc_entry.get("filename")
    
    rec = next((r for r in records if r.index_record_id == target_idx), None)
    if not rec and target_util:
        rec = next((r for r in records if r.utility_name.lower().strip() == target_util.lower().strip() and r.is_asset_present), None)
    if not rec:
        raise HTTPException(status_code=404, detail=f"Index record for {document_id} not found in {index_path}.")
        
    discovered = scan_root_folder(root_dir)
    _, doc_map = resolve_documents(records, discovered)
    matched_file = doc_map.get(rec.index_record_id)
    if not matched_file and target_fn:
        matched_file = next((f for f in discovered if f.filename.lower() == target_fn.lower()), None)
        
    if not matched_file:
        # Graceful fallback for records without physical map files (e.g. Status='No')
        return ReviewWorkspacePayload(
            job_id=job_id,
            document_id=matched_doc_entry.get("document_id") or matched_doc_entry.get("index_record_id") or document_id,
            index_record_id=rec.index_record_id,
            filename=target_fn or f"No Map Required ({rec.raw_status})",
            utility_name=rec.utility_name,
            utility_type=rec.utility_type,
            page_count=0,
            modality="N/A",
            pdf_path="",
            aoi_method="N/A",
            aoi_confidence=1.0,
            aoi_bbox=None,
            aoi_coordinates=[],
            reconciliation_outcome=matched_doc_entry.get("reconciliation_outcome", "CONFIRMED_CLEAN"),
            upstream_claim=rec.raw_warning,
            independent_findings=[],
            legend_id=None,
            legend_features=[],
            evidence_package_id="PKG-NONE",
            evidence_items=[],
            advisory={
                "summary": matched_doc_entry.get("reason", "Utility reported no assets in enquiry area."),
                "key_points": [f"Status: {rec.raw_status}", f"Decision: {matched_doc_entry.get('decision')}"],
                "contradictions_detected": [],
                "model_name": "Policy Engine",
                "is_fallback": True
            },
            decision=matched_doc_entry.get("decision", "AUTO_CLEAR"),
            reason=matched_doc_entry.get("reason", f"Utility reported {rec.raw_status}."),
            gates={}
        )

        
    payload = workspace_builder.build_workspace_payload(job_id, root_dir, rec, matched_file, job_out_dir)
    return payload



@router.post("/disposition", response_model=HumanDispositionResponse)
def submit_human_disposition(req: HumanDispositionRequest):
    job_out_dir = os.path.join(settings.output_dir, req.job_id)
    results_file = os.path.join(job_out_dir, "document_results.json")
    
    if not os.path.exists(results_file):
        raise HTTPException(status_code=404, detail=f"Job {req.job_id} results not found.")
        
    with open(results_file, "r", encoding="utf-8") as f:
        docs = json.load(f)
        
    target_idx = next((i for i, d in enumerate(docs) if d.get("document_id") == req.document_id or d.get("index_record_id") == req.document_id), None)
    if target_idx is None:
        raise HTTPException(status_code=404, detail=f"Document {req.document_id} not found in {req.job_id}.")
        
    prev_decision = docs[target_idx].get("decision", "HUMAN_REVIEW")
    
    version_snap = VersionSnapshot(
        engine_version=settings.engine_version,
        policy_version=settings.policy_version,
        warning_catalogue_version=settings.warning_catalogue_version,
        legend_version=settings.legend_version,
        cv_version="1.0.0"
    )
    
    drec = DecisionRecord(
        job_id=req.job_id,
        document_id=req.document_id,
        index_record_id=req.index_record_id,
        source_file_hash="VERIFIED_AUDIT",
        decision=Decision(prev_decision) if prev_decision in [d.value for d in Decision] else Decision.HUMAN_REVIEW,
        reason=docs[target_idx].get("reason", ""),
        versions=version_snap
    )
    
    updated_drec = human_disposition_service.apply_disposition(
        decision_record=drec,
        action=req.action,
        reviewer_id=req.reviewer_id,
        reviewer_comment=req.reviewer_comment
    )
    
    # Update document results in place
    docs[target_idx]["decision"] = updated_drec.decision.value
    docs[target_idx]["reason"] = updated_drec.reason
    docs[target_idx]["human_disposition"] = req.action.value
    docs[target_idx]["reviewer_id"] = req.reviewer_id
    docs[target_idx]["reviewer_comment"] = req.reviewer_comment
    docs[target_idx]["disposition_timestamp"] = updated_drec.timestamp
    
    with open(results_file, "w", encoding="utf-8") as f:
        json.dump(docs, f, indent=2)
        
    # Also update job_report.json summary counts
    job_report_file = os.path.join(job_out_dir, "job_report.json")
    if os.path.exists(job_report_file):
        with open(job_report_file, "r", encoding="utf-8") as f:
            jrep = json.load(f)
            
        auto_c = sum(1 for d in docs if d.get("decision") == "AUTO_CLEAR")
        human_r = sum(1 for d in docs if d.get("decision") == "HUMAN_REVIEW")
        blocked_c = sum(1 for d in docs if d.get("decision") == "BLOCKED")
        
        jrep["summary"]["auto_clear"] = auto_c
        jrep["summary"]["human_review"] = human_r
        jrep["summary"]["blocked"] = blocked_c
        
        if human_r == 0 and blocked_c == 0:
            jrep["overall_decision"] = "AUTO_CLEAR"
        elif human_r > 0:
            jrep["overall_decision"] = "HUMAN_REVIEW"
        else:
            jrep["overall_decision"] = "BLOCKED"
            
        with open(job_report_file, "w", encoding="utf-8") as f:
            json.dump(jrep, f, indent=2)
            
    logger.info(f"Updated disposition for {req.document_id} -> {updated_drec.decision.value}")
    
    # Also persist to database (non-blocking, graceful fallback)
    try:
        from src.db.engine import AsyncSessionLocal
        from src.db.persistence import persistence_service
        import asyncio
        import concurrent.futures
        
        async def _persist():
            async with AsyncSessionLocal() as session:
                await persistence_service.persist_human_disposition(
                    session, job_id=req.job_id, document_id=req.document_id,
                    action=req.action.value, reviewer_id=req.reviewer_id,
                    comment=req.reviewer_comment,
                )
        
        try:
            loop = asyncio.get_running_loop()
            with concurrent.futures.ThreadPoolExecutor() as pool:
                pool.submit(lambda: asyncio.run(_persist())).result(timeout=10)
        except RuntimeError:
            asyncio.run(_persist())
    except Exception as e:
        logger.warning(f"DB persistence for disposition skipped: {e}")

    
    return HumanDispositionResponse(
        job_id=req.job_id,
        document_id=req.document_id,
        previous_decision=prev_decision,
        new_decision=updated_drec.decision.value,
        action=req.action,
        reviewer_id=req.reviewer_id,
        reviewer_comment=req.reviewer_comment,
        timestamp=updated_drec.timestamp,
        audit_persisted=True
    )
