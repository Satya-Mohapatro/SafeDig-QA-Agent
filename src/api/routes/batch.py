import os
from fastapi import APIRouter, HTTPException
from src.batch.models import (
    BatchSubmitRequest,
    BatchSubmitResponse,
    DirectoryScanRequest,
    BatchProgressSummary
)
from src.batch import job_queue, directory_scanner, worker_pool

router = APIRouter(prefix="/batch", tags=["Batch Processing & Worker Pool"])

@router.post("/submit-bulk", response_model=BatchSubmitResponse)
def submit_bulk_jobs(req: BatchSubmitRequest):
    jids = []
    worker_pool.start()
    
    for path in req.folder_paths:
        if os.path.exists(path):
            task = job_queue.enqueue(root_dir=path, priority=req.priority)
            jids.append(task.job_id)
            
    return BatchSubmitResponse(
        submitted_count=len(jids),
        job_ids=jids,
        message=f"Enqueued {len(jids)} jobs into batch worker pool."
    )

@router.post("/scan-directory", response_model=BatchSubmitResponse)
def scan_and_enqueue_directory(req: DirectoryScanRequest):
    if not os.path.exists(req.parent_directory):
        raise HTTPException(status_code=404, detail=f"Directory '{req.parent_directory}' does not exist.")
        
    discovered_dirs = directory_scanner.scan_for_job_folders(req.parent_directory, recursive=req.recursive)
    worker_pool.start()
    
    jids = []
    for d in discovered_dirs:
        task = job_queue.enqueue(root_dir=d, priority=req.priority)
        jids.append(task.job_id)
        
    return BatchSubmitResponse(
        submitted_count=len(jids),
        job_ids=jids,
        message=f"Discovered and enqueued {len(jids)} project jobs."
    )

@router.get("/progress", response_model=BatchProgressSummary)
def get_batch_progress():
    return worker_pool.get_progress_summary()

@router.post("/cancel/{job_id}")
def cancel_batch_job(job_id: str):
    success = job_queue.cancel(job_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not active or already completed.")
    return {"job_id": job_id, "status": "CANCELLED", "message": "Job successfully cancelled."}
