import os
import uuid
from typing import Dict, Any, List
from src.domain.enums import Decision, DocumentResolutionStatus, Severity, HumanDispositionAction, ReconciliationOutcome
from src.domain.warning import ClaimedWarning
from src.domain.audit import DecisionRecord, VersionSnapshot
from src.domain.reconciliation import ReconciliationResult
from src.domain.evidence import EvidencePackage
from src.domain.policy import PolicyResult
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
from src.agent import advisory_service
from src.qa import human_disposition_service
from src.reporting import generate_job_reports
from src.config.settings import settings
from src.config.logging import logger
from src.orchestration.state import MapQAState

def ingest_and_index_node(state: MapQAState) -> MapQAState:
    root_dir = state["root_dir"]
    job_id = state.get("job_id", f"JOB-{os.path.basename(os.path.abspath(root_dir))}")
    run_id = state.get("workflow_run_id", f"RUN-{uuid.uuid4().hex[:8]}")
    out_dir = state.get("output_dir", os.path.join(settings.output_dir, job_id))
    os.makedirs(out_dir, exist_ok=True)
    
    logger.info(f"[LangGraph: ingest_and_index_node] Starting run {run_id} for {job_id}")
    
    discovered = scan_root_folder(root_dir)
    manifest = build_manifest(job_id, root_dir, discovered)
    
    index_files = [f for f in discovered if f.filename.lower() in ["index.xlsx", "index.xls"]]
    if not index_files:
        index_files = [f for f in discovered if f.extension in [".xlsx", ".xls"]]
        
    if not index_files:
        logger.error(f"No index Excel found in {root_dir}")
        return {
            **state,
            "status": "FAILED",
            "overall_decision": Decision.BLOCKED.value,
            "error_state": {"error": "Missing mandatory index Excel file."}
        }
        
    index_file = index_files[0]
    index_path = index_file.metadata.get("full_path", os.path.join(root_dir, index_file.filename))
    
    records = parse_index_excel(index_path, job_id)
    val_report = validate_index_records(records)
    resolved_records, doc_map = resolve_documents(records, discovered)
    account_report = account_for_all_rows(resolved_records)
    
    return {
        **state,
        "job_id": job_id,
        "workflow_run_id": run_id,
        "output_dir": out_dir,
        "manifest": manifest if isinstance(manifest, dict) else manifest.model_dump(),
        "discovered_files": [f.model_dump() for f in discovered],
        "index_records": [r.model_dump() for r in resolved_records],
        "resolved_documents": {k: v.model_dump() for k, v in doc_map.items()},
        "validation_report": val_report if isinstance(val_report, dict) else val_report.model_dump(),
        "accounting_report": account_report if isinstance(account_report, dict) else account_report.model_dump(),
        "status": "INDEXED"
    }

def process_qa_and_policy_node(state: MapQAState) -> MapQAState:
    root_dir = state["root_dir"]
    job_id = state["job_id"]
    out_dir = state["output_dir"]
    
    from src.domain.index_record import IndexRecord
    from src.domain.document import DiscoveredFile
    
    records = [IndexRecord(**r) for r in state["index_records"]]
    doc_map = {k: DiscoveredFile(**v) for k, v in state["resolved_documents"].items()}
    index_file_hash = state["manifest"]["files"][0]["sha256"] if state["manifest"].get("files") else "UNKNOWN"
    
    version_snap = VersionSnapshot(
        engine_version=settings.engine_version,
        policy_version=settings.policy_version,
        warning_catalogue_version=settings.warning_catalogue_version,
        legend_version=settings.legend_version,
        cv_version="1.0.0"
    )
    
    document_results: List[Dict[str, Any]] = []
    decision_records: List[Dict[str, Any]] = []
    evidence_packages: Dict[str, Any] = {}
    reconciliations: Dict[str, Any] = {}
    policy_results: Dict[str, Any] = {}
    human_queue: List[Dict[str, Any]] = []
    
    has_blocked = False
    has_human_review = False
    
    for rec in records:
        # Case A: Status='No'
        if not rec.is_asset_present:
            reconcil_res = reconcile_warnings(rec.index_record_id, None, [])
            pol_res = policy_engine.evaluate(
                index_record=rec,
                document=None,
                legend_profile=None,
                aoi=None,
                reconciliation=reconcil_res,
                evidence_pkg=None
            )
            drec = DecisionRecord(
                job_id=job_id,
                document_id=rec.index_record_id,
                index_record_id=rec.index_record_id,
                source_file_hash=index_file_hash,
                provider=rec.utility_name,
                utility_type=rec.utility_type,
                decision=Decision.AUTO_CLEAR,
                reason=pol_res.reason,
                versions=version_snap,
                evidence_ids=[]
            )
            decision_records.append(drec.model_dump())
            document_results.append({
                "index_record_id": rec.index_record_id,
                "utility_name": rec.utility_name,
                "utility_type": rec.utility_type,
                "status": "No",
                "decision": Decision.AUTO_CLEAR.value,
                "reason": pol_res.reason
            })
            continue
            
        matched_file = doc_map.get(rec.index_record_id)
        if not matched_file:
            # Case B: Missing Map File -> BLOCKED
            has_blocked = True
            missing_name = rec.file_name or rec.utility_name
            reason = f"Expected map for '{missing_name}' was not found in job folder."
            drec = DecisionRecord(
                job_id=job_id,
                document_id=rec.index_record_id,
                index_record_id=rec.index_record_id,
                source_file_hash=index_file_hash,
                provider=rec.utility_name,
                utility_type=rec.utility_type,
                decision=Decision.BLOCKED,
                reason=reason,
                versions=version_snap,
                evidence_ids=[]
            )
            decision_records.append(drec.model_dump())
            document_results.append({
                "index_record_id": rec.index_record_id,
                "utility_name": rec.utility_name,
                "utility_type": rec.utility_type,
                "file_name": rec.file_name,
                "decision": Decision.BLOCKED.value,
                "reason": reason
            })
            continue
            
        # Case C: Execute QA Pipeline
        pdf_path = matched_file.metadata.get("full_path", os.path.join(root_dir, matched_file.filename))
        doc_id = f"DOC-{matched_file.file_id}"
        
        doc_obj = inspect_pdf(pdf_path, doc_id, job_id, matched_file.file_id, matched_file.sha256)
        wdefs = master_warning_catalogue.get_definitions_for_provider(rec.utility_name)
        legend = resolve_legend(rec.utility_name)
        aoi = get_document_aoi(pdf_path, doc_id, page_num=1)
        
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
            
        detected_cands = detect_independent_warnings(pdf_path, doc_obj, aoi, wdefs, legend)
        reconcil_res = reconcile_warnings(doc_id, claimed_w, detected_cands)
        ev_pkg = build_evidence_package(pdf_path, doc_obj, aoi, reconcil_res, output_dir=os.path.join(out_dir, "evidence"))
        pol_res = policy_engine.evaluate(rec, doc_obj, legend, aoi, reconcil_res, ev_pkg)
        
        evidence_packages[doc_id] = ev_pkg.model_dump()
        reconciliations[doc_id] = reconcil_res.model_dump()
        policy_results[doc_id] = pol_res.model_dump()
        
        drec = DecisionRecord(
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
        )
        decision_records.append(drec.model_dump())
        
        doc_entry = {
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
        }
        document_results.append(doc_entry)
        
        if pol_res.decision == Decision.HUMAN_REVIEW:
            has_human_review = True
            human_queue.append(doc_entry)
        elif pol_res.decision == Decision.BLOCKED:
            has_blocked = True
            
    # Compute job-level overall decision
    if has_blocked:
        overall_dec = Decision.BLOCKED.value
    elif has_human_review:
        overall_dec = Decision.HUMAN_REVIEW.value
    else:
        overall_dec = Decision.AUTO_CLEAR.value
        
    return {
        **state,
        "document_results": document_results,
        "decision_records": decision_records,
        "evidence_packages": evidence_packages,
        "reconciliations": reconciliations,
        "policy_results": policy_results,
        "human_review_queue": human_queue,
        "overall_decision": overall_dec,
        "status": "EVALUATED"
    }

def llm_advisory_node(state: MapQAState) -> MapQAState:
    logger.info(f"[LangGraph: llm_advisory_node] Generating advisory summaries for {len(state.get('human_review_queue', []))} queue items")
    advisories: Dict[str, Any] = {}
    
    for item in state.get("human_review_queue", []):
        doc_id = item["document_id"]
        ev_data = state.get("evidence_packages", {}).get(doc_id)
        ev_pkg = EvidencePackage(**ev_data) if ev_data else None
        
        rec_data = state.get("reconciliations", {}).get(doc_id)
        if rec_data:
            reconcil_res = ReconciliationResult(**rec_data)
        else:
            reconcil_res = ReconciliationResult(
                reconciliation_id=f"REC-{doc_id}",
                document_id=doc_id,
                outcome=ReconciliationOutcome(item["reconciliation_outcome"]),
                explanation=item["reason"]
            )
            
        pol_data = state.get("policy_results", {}).get(doc_id)
        if pol_data:
            pol_res = PolicyResult(**pol_data)
        else:
            pol_res = PolicyResult(
                document_id=doc_id,
                decision=Decision(item["decision"]),
                reason=item["reason"]
            )
            
        adv = advisory_service.generate_advisory(
            document=None,
            reconciliation=reconcil_res,
            evidence_pkg=ev_pkg,
            policy_result=pol_res
        )
        advisories[doc_id] = adv.model_dump()
        
    return {
        **state,
        "advisories": advisories,
        "status": "ADVISORY_GENERATED"
    }

def finalize_report_node(state: MapQAState) -> MapQAState:
    job_id = state["job_id"]
    root_dir = state["root_dir"]
    out_dir = state["output_dir"]
    doc_results = state.get("document_results", [])
    
    logger.info(f"[LangGraph: finalize_report_node] Writing reports to {out_dir}")
    reports = generate_job_reports(job_id, root_dir, doc_results, out_dir)
    
    return {
        **state,
        "reports": reports,
        "status": "REPORTS_GENERATED"
    }

def persist_to_db_node(state: MapQAState) -> MapQAState:
    job_id = state.get("job_id", "")
    root_dir = state.get("root_dir", "")
    doc_results = state.get("document_results", [])
    
    logger.info(f"[LangGraph: persist_to_db_node] Persisting job {job_id} to database")
    try:
        import asyncio
        import concurrent.futures
        from src.db.engine import AsyncSessionLocal
        from src.db.persistence import persistence_service
        
        async def _persist():
            async with AsyncSessionLocal() as session:
                await persistence_service.persist_job_result(
                    session=session,
                    job_id=job_id,
                    root_dir=root_dir,
                    document_results=doc_results
                )
        
        try:
            loop = asyncio.get_running_loop()
            with concurrent.futures.ThreadPoolExecutor() as pool:
                pool.submit(lambda: asyncio.run(_persist())).result(timeout=10)
        except RuntimeError:
            asyncio.run(_persist())
    except Exception as e:
        logger.warning(f"[LangGraph: persist_to_db_node] Failed to persist: {e}")

    # Record telemetry metrics
    try:
        from src.utils.telemetry import metrics_registry
        metrics_registry.record_job("COMPLETED")
        metrics_registry.set_queue_pending(len(state.get("human_review_queue", [])))
        for doc_res in doc_results:
            dec = doc_res.get("decision", "AUTO_CLEAR")
            metrics_registry.record_document(dec)
            outc = doc_res.get("reconciliation_outcome")
            if outc:
                metrics_registry.record_reconciliation(outc)
    except Exception as me:
        logger.debug(f"Telemetry recording skipped: {me}")
        
    return {
        **state,
        "status": "COMPLETED"
    }


