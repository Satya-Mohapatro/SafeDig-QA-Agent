import os
import json
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from src.config.settings import settings
from src.config.logging import logger

router = APIRouter(prefix="/evidence", tags=["Evidence Files & Crops"])

@router.get("/{job_id}/{document_id}/crop/{crop_filename}")
def get_evidence_crop(job_id: str, document_id: str, crop_filename: str):
    # Check specific job evidence dir first
    candidates = [
        os.path.join(settings.output_dir, job_id, "evidence", crop_filename),
        os.path.join(settings.output_dir, "evidence", crop_filename),
        os.path.join(settings.output_dir, job_id, crop_filename),
    ]
    for p in candidates:
        if os.path.exists(p):
            return FileResponse(p, media_type="image/png")
            
    # Search recursively in job output folder if needed
    job_out_dir = os.path.join(settings.output_dir, job_id)
    if os.path.exists(job_out_dir):
        for root, _, files in os.walk(job_out_dir):
            if crop_filename in files:
                return FileResponse(os.path.join(root, crop_filename), media_type="image/png")
                
    raise HTTPException(status_code=404, detail=f"Evidence crop '{crop_filename}' not found for {job_id}/{document_id}.")


@router.get("/{job_id}/{document_id}/map-image")
def get_map_image(job_id: str, document_id: str):
    """Render on-the-fly and return a 200 DPI PNG of the map with the red AOI boundary."""
    job_out_dir = os.path.join(settings.output_dir, job_id)
    report_file = os.path.join(job_out_dir, "job_report.json")
    if not os.path.exists(report_file):
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found.")
        
    with open(report_file, "r", encoding="utf-8") as f:
        rep_data = json.load(f)
    root_dir = rep_data.get("root_dir", "")
    
    results_file = os.path.join(job_out_dir, "document_results.json")
    if not os.path.exists(results_file):
        raise HTTPException(status_code=404, detail="Document results not found.")
    with open(results_file, "r", encoding="utf-8") as f:
        docs = json.load(f)
        
    matched = next((d for d in docs if d.get("document_id") == document_id or d.get("index_record_id") == document_id), None)
    if not matched:
        raise HTTPException(status_code=404, detail=f"Document {document_id} not found.")
        
    fn = matched.get("filename")
    pdf_path = os.path.join(root_dir, fn) if fn else None
    if not pdf_path or not os.path.exists(pdf_path):
        # Search in root_dir
        for root, _, files in os.walk(root_dir):
            if fn and fn in files:
                pdf_path = os.path.join(root, fn)
                break
                
    if not pdf_path or not os.path.exists(pdf_path):
        raise HTTPException(status_code=404, detail=f"Source PDF for {document_id} not found on disk.")
        
    out_img = os.path.join(job_out_dir, "evidence", f"map_render_{document_id}.png")
    if os.path.exists(out_img):
        return FileResponse(out_img, media_type="image/png")
        
    from src.aoi import get_document_aoi
    from src.evidence.crops import generate_aoi_map_render
    aoi = get_document_aoi(pdf_path, document_id, page_num=1)
    bbox = aoi.bbox if aoi else None
    res = generate_aoi_map_render(pdf_path, aoi.page_num if aoi else 1, bbox, out_img, dpi=200)
    if res and os.path.exists(out_img):
        return FileResponse(out_img, media_type="image/png")
        
    raise HTTPException(status_code=500, detail="Failed to render map image.")

