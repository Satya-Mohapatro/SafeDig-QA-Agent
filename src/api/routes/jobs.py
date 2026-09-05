import os
import json
from fastapi import APIRouter, HTTPException
from src.api.schemas import JobSubmitRequest, JobSubmitResponse, JobStatusResponse
from src.orchestration import map_qa_workflow, MapQAState
from src.config.settings import settings
from src.config.logging import logger

router = APIRouter(prefix="/jobs", tags=["Jobs"])

@router.get("")
def list_all_jobs():
    """List all executed jobs, compute real-time KPI metrics, and discover available data presets."""
    base_out = settings.output_dir
    jobs_list = []
    
    total_processed = 0
    total_auto_clear = 0
    total_human_review = 0
    total_blocked = 0
    
    if os.path.exists(base_out):
        for item in sorted(os.listdir(base_out), reverse=True):
            item_path = os.path.join(base_out, item)
            if not os.path.isdir(item_path):
                continue
            rep_file = os.path.join(item_path, "job_report.json")
            if os.path.exists(rep_file):
                try:
                    with open(rep_file, "r", encoding="utf-8") as f:
                        rep_data = json.load(f)
                    summary = rep_data.get("summary", {})
                    n_recs = summary.get("total_documents", summary.get("total_records", len(rep_data.get("results", []))))
                    ac = summary.get("auto_clear", summary.get("auto_clear_count", 0))
                    hr = summary.get("human_review", summary.get("human_review_count", 0))
                    bl = summary.get("blocked", summary.get("blocked_count", 0))
                    
                    total_processed += n_recs
                    total_auto_clear += ac
                    total_human_review += hr
                    total_blocked += bl
                    
                    dec = rep_data.get("overall_decision")
                    if not dec or dec == "UNKNOWN":
                        if bl > 0:
                            dec = "BLOCKED"
                        elif hr > 0:
                            dec = "HUMAN_REVIEW"
                        else:
                            dec = "AUTO_CLEAR"
                    
                    jobs_list.append({
                        "job_id": item,
                        "records": n_recs,
                        "auto_clear": ac,
                        "human_review": hr,
                        "blocked": bl,
                        "decision": dec,
                        "generated_at": rep_data.get("generated_at"),
                        "root_dir": rep_data.get("root_dir", "").replace("\\", "/")
                    })
                except Exception as e:
                    logger.warning(f"Error reading job report in {item_path}: {e}")


    # Discover presets in Data/
    presets = []
    data_dir = str(settings.data_dir)
    if os.path.exists(data_dir):
        for d in sorted(os.listdir(data_dir)):
            full_dp = os.path.join(data_dir, d)
            if os.path.isdir(full_dp) and os.path.exists(os.path.join(full_dp, "index.xlsx")):
                presets.append({
                    "label": f"Folder {d} (69 recs)",
                    "path": full_dp.replace("\\", "/")
                })
                
    ac_rate = round((total_auto_clear / total_processed * 100), 1) if total_processed > 0 else 0.0
    hr_rate = round((total_human_review / total_processed * 100), 1) if total_processed > 0 else 0.0
    bl_rate = round((total_blocked / total_processed * 100), 1) if total_processed > 0 else 0.0

    return {
        "total_jobs": len(jobs_list),
        "total_processed": total_processed,
        "auto_clear_count": total_auto_clear,
        "auto_clear_rate": ac_rate,
        "human_review_count": total_human_review,
        "human_review_rate": hr_rate,
        "blocked_count": total_blocked,
        "blocked_rate": bl_rate,
        "jobs": jobs_list,
        "available_presets": presets
    }


@router.post("/submit", response_model=JobSubmitResponse)
def submit_job(req: JobSubmitRequest):
    resolved_root = req.root_dir
    if not os.path.exists(resolved_root):
        cand1 = os.path.join(str(settings.data_dir), req.root_dir)
        cand2 = os.path.join(str(settings.project_root), req.root_dir)
        if os.path.exists(cand1):
            resolved_root = cand1
        elif os.path.exists(cand2):
            resolved_root = cand2
        else:
            raise HTTPException(status_code=404, detail=f"Target root folder not found: {req.root_dir}")
        
    folder_name = os.path.basename(os.path.abspath(resolved_root))
    job_id = req.job_id or f"JOB-{folder_name}"
    out_dir = req.output_dir or os.path.join(str(settings.output_dir), job_id)
    
    initial_state: MapQAState = {
        "root_dir": resolved_root,
        "job_id": job_id,
        "output_dir": out_dir
    }
    
    final_state = map_qa_workflow.invoke(initial_state)
    
    doc_results = final_state.get("document_results", [])
    overall_dec = final_state.get("overall_decision", "BLOCKED")
    reports = final_state.get("reports", {})
    
    return JobSubmitResponse(
        job_id=job_id,
        status=final_state.get("status", "COMPLETED"),
        message="Job executed successfully through LangGraph workflow.",
        overall_decision=overall_dec,
        total_documents_processed=len(doc_results),
        reports=reports
    )


@router.get("/{job_id}", response_model=JobStatusResponse)
def get_job_status(job_id: str):
    job_out_dir = os.path.join(settings.output_dir, job_id)
    report_file = os.path.join(job_out_dir, "job_report.json")
    
    if not os.path.exists(report_file):
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found or report not yet generated.")
        
    with open(report_file, "r", encoding="utf-8") as f:
        rep_data = json.load(f)
        
    summary = rep_data.get("summary", {})
    total_recs = summary.get("total_documents", summary.get("total_records", len(rep_data.get("results", []))))
    auto_c = summary.get("auto_clear_count", summary.get("auto_clear", 0))
    human_r = summary.get("human_review_count", summary.get("human_review", 0))
    block_c = summary.get("blocked_count", summary.get("blocked", 0))
    
    return JobStatusResponse(
        job_id=job_id,
        status="COMPLETED",
        overall_decision=rep_data.get("overall_decision", "UNKNOWN"),
        total_records=total_recs,
        auto_clear_count=auto_c,
        human_review_count=human_r,
        blocked_count=block_c,
        created_at=rep_data.get("generated_at"),
        completed_at=rep_data.get("generated_at"),
        reports={
            "job_report": report_file,
            "document_results": os.path.join(job_out_dir, "document_results.json")
        }
    )

@router.get("/{job_id}/report")
def get_job_report(job_id: str):
    job_out_dir = os.path.join(settings.output_dir, job_id)
    report_file = os.path.join(job_out_dir, "job_report.json")
    if not os.path.exists(report_file):
        raise HTTPException(status_code=404, detail=f"Job report for {job_id} not found.")
    with open(report_file, "r", encoding="utf-8") as f:
        return json.load(f)

@router.get("/{job_id}/results")
def get_document_results(job_id: str):
    job_out_dir = os.path.join(settings.output_dir, job_id)
    results_file = os.path.join(job_out_dir, "document_results.json")
    if not os.path.exists(results_file):
        raise HTTPException(status_code=404, detail=f"Document results for {job_id} not found.")
    with open(results_file, "r", encoding="utf-8") as f:
        return json.load(f)


# ── DB-Backed Endpoints ─────────────────────────────────────────────────────

@router.get("/{job_id}/audit-trail")
async def get_audit_trail(job_id: str):
    """Return the immutable audit trail for a job from the database."""
    from src.db.engine import AsyncSessionLocal
    from src.db.persistence import persistence_service
    
    async with AsyncSessionLocal() as session:
        trail = await persistence_service.load_audit_trail(session, job_id)
    
    if not trail:
        raise HTTPException(status_code=404, detail=f"No audit trail found for job {job_id}.")
    return {"job_id": job_id, "total_entries": len(trail), "audit_trail": trail}


@router.get("/{job_id}/db-summary")
async def get_job_db_summary(job_id: str):
    """Return job summary with documents from the database."""
    from src.db.engine import AsyncSessionLocal
    from src.db.persistence import persistence_service
    
    async with AsyncSessionLocal() as session:
        summary = await persistence_service.load_job_summary(session, job_id)
    
    if not summary:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found in database.")
    return summary

