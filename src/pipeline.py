import os
from typing import List, Dict, Any, Optional
from src.domain.enums import Decision, DocumentResolutionStatus, Severity
from src.domain.warning import ClaimedWarning
from src.domain.audit import DecisionRecord, VersionSnapshot
from src.domain.evidence import EvidencePackage
from src.ingestion import scan_root_folder, build_manifest
from src.index import parse_index_excel, validate_index_records, account_for_all_rows
from src.documents import resolve_documents
from src.pdf import inspect_pdf
from src.warnings import master_warning_catalogue
from src.legends import resolve_legend
from src.aoi import get_document_aoi
from src.detection import detect_independent_warnings
from src.reconciliation import reconcile_warnings
from src.evidence import build_evidence_package
from src.policy import policy_engine
from src.reporting import generate_job_reports
from src.config.logging import logger
from src.config.settings import settings

def run_map_qa_pipeline(
    root_dir: str,
    job_id: Optional[str] = None,
    output_dir: Optional[str] = None
) -> Dict[str, Any]:
    folder_name = os.path.basename(os.path.abspath(root_dir))
    job_id = job_id or f"JOB-{folder_name}"
    out_dir = output_dir or os.path.join(settings.output_dir, job_id)
    os.makedirs(out_dir, exist_ok=True)
    
    logger.info(f"=== STARTING MAP QA PIPELINE FOR {job_id} ===")
    
    version_snap = VersionSnapshot(
        engine_version=settings.engine_version,
        policy_version=settings.policy_version,
        warning_catalogue_version=settings.warning_catalogue_version,
        legend_version=settings.legend_version,
        cv_version="1.0.0"
    )
    
    # ── Phase 1: File Discovery & Inventory ──────────────────────────────────
    discovered = scan_root_folder(root_dir)
    manifest = build_manifest(job_id, root_dir, discovered)
    
    # ── Phase 2: Locate Index File ───────────────────────────────────────────
    index_files = [f for f in discovered if f.filename.lower() in ["index.xlsx", "index.xls"]]
    if not index_files:
        index_files = [f for f in discovered if f.extension in [".xlsx", ".xls"]]
    if not index_files:
        logger.error(f"No index Excel found in {root_dir}")
        return {"job_id": job_id, "error": "Index missing", "decision": Decision.BLOCKED.value}
    
    index_file = index_files[0]
    index_path = index_file.metadata.get("full_path", os.path.join(root_dir, index_file.filename))
    
    # ── Phase 3: Read-Only Index Parse ───────────────────────────────────────
    records = parse_index_excel(index_path, job_id)
    val_report = validate_index_records(records)
    
    # ── Phase 4: Document Resolution ─────────────────────────────────────────
    resolved_records, doc_map = resolve_documents(records, discovered)
    account_report = account_for_all_rows(resolved_records)
    
    # ── Phase 5: Per-Record Deterministic Processing ──────────────────────────
    document_results: List[Dict[str, Any]] = []
    decision_records: List[DecisionRecord] = []
    
    for rec in resolved_records:
        
        # --- CASE A: Asset explicitly absent (Status='No') → AUTO_CLEAR ------
        if not rec.is_asset_present:
            result_entry = {
                "index_record_id": rec.index_record_id,
                "utility_name": rec.utility_name,
                "utility_type": rec.utility_type,
                "status": "No",
                "decision": Decision.AUTO_CLEAR.value,
                "reason": "Utility reported no assets in the enquiry area (Status='No')."
            }
            decision_records.append(DecisionRecord(
                job_id=job_id,
                document_id=rec.index_record_id,
                index_record_id=rec.index_record_id,
                source_file_hash=index_file.sha256,
                provider=rec.utility_name,
                utility_type=rec.utility_type,
                decision=Decision.AUTO_CLEAR,
                reason=result_entry["reason"],
                versions=version_snap,
                evidence_ids=[]
            ))
            document_results.append(result_entry)
            continue
        
        # --- CASE B: Map file not found on disk → BLOCKED --------------------
        matched_file = doc_map.get(rec.index_record_id)
        if not matched_file:
            missing_name = rec.file_name or rec.utility_name
            reason = f"Expected map for '{missing_name}' was not found in job folder."
            decision_records.append(DecisionRecord(
                job_id=job_id,
                document_id=rec.index_record_id,
                index_record_id=rec.index_record_id,
                source_file_hash=index_file.sha256,
                provider=rec.utility_name,
                utility_type=rec.utility_type,
                decision=Decision.BLOCKED,
                reason=reason,
                versions=version_snap,
                evidence_ids=[]
            ))
            document_results.append({
                "index_record_id": rec.index_record_id,
                "utility_name": rec.utility_name,
                "utility_type": rec.utility_type,
                "file_name": rec.file_name,
                "decision": Decision.BLOCKED.value,
                "reason": reason
            })
            continue
        
        # --- CASE C: Full QA processing path ---------------------------------
        pdf_path = matched_file.metadata.get("full_path", os.path.join(root_dir, matched_file.filename))
        doc_id = f"DOC-{matched_file.file_id}"
        
        # 6. PDF Inspection
        doc_obj = inspect_pdf(pdf_path, doc_id, job_id, matched_file.file_id, matched_file.sha256)
        
        # 7. Warning Definitions & Legend Resolution
        wdefs = master_warning_catalogue.get_definitions_for_provider(rec.utility_name)
        legend = resolve_legend(rec.utility_name)
        
        # 8. AOI Resolution
        aoi = get_document_aoi(pdf_path, doc_id, page_num=1)
        
        # 9. Upstream Claimed Warning Parsing
        claimed_w = None
        if rec.raw_warning and rec.raw_warning.strip():
            matched_wdef = master_warning_catalogue.find_by_text(rec.raw_warning)
            upstream_conf = 1.0
            if rec.raw_comments:
                try:
                    upstream_conf = float(rec.raw_comments) / 100.0
                except (ValueError, TypeError):
                    upstream_conf = 1.0
            claimed_w = ClaimedWarning(
                claimed_warning_id=f"CLM-{doc_id}",
                document_id=doc_id,
                index_record_id=rec.index_record_id,
                warning_code=matched_wdef.warning_code if matched_wdef else "CLAIMED_WARNING",
                raw_warning_text=rec.raw_warning,
                severity=matched_wdef.severity if matched_wdef else Severity.MEDIUM,
                upstream_confidence=upstream_conf
            )
        
        # 10. Independent Warning Detection
        detected_cands = detect_independent_warnings(pdf_path, doc_obj, aoi, wdefs, legend)
        
        # 11. Upstream Reconciliation
        reconcil_res = reconcile_warnings(doc_id, claimed_w, detected_cands)
        
        # 12. Evidence Packaging
        ev_pkg = build_evidence_package(
            pdf_path, doc_obj, aoi, reconcil_res,
            output_dir=os.path.join(out_dir, "evidence")
        )
        
        # 13. Policy Engine Decision
        pol_res = policy_engine.evaluate(
            index_record=rec,
            document=doc_obj,
            legend_profile=legend,
            aoi=aoi,
            reconciliation=reconcil_res,
            evidence_pkg=ev_pkg
        )
        
        decision_records.append(DecisionRecord(
            job_id=job_id,
            document_id=doc_id,
            index_record_id=rec.index_record_id,
            source_file_hash=matched_file.sha256,
            provider=rec.utility_name,
            utility_type=rec.utility_type,
            decision=pol_res.decision,
            reason=pol_res.reason,
            versions=version_snap,
            evidence_ids=[it.evidence_id for it in ev_pkg.items]
        ))
        
        document_results.append({
            "index_record_id": rec.index_record_id,
            "document_id": doc_id,
            "filename": matched_file.filename,
            "utility_name": rec.utility_name,
            "utility_type": rec.utility_type,
            "upstream_claim": rec.raw_warning,
            "independent_findings_count": len(detected_cands),
            "reconciliation_outcome": reconcil_res.outcome.value,
            "decision": pol_res.decision.value,
            "reason": pol_res.reason,
            "evidence_package_id": ev_pkg.package_id,
            "evidence_count": len(ev_pkg.items)
        })
    
    # ── Phase 14: Standard Report Generation ─────────────────────────────────
    reports = generate_job_reports(job_id, root_dir, document_results, out_dir)
    
    logger.info(f"=== PIPELINE COMPLETED FOR {job_id}: {len(document_results)} documents processed ===")
    return {
        "job_id": job_id,
        "manifest": manifest,
        "validation_report": val_report,
        "accounting_report": account_report,
        "results": document_results,
        "reports": reports
    }
