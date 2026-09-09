import os
import json
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
from src.config.settings import settings
from src.config.logging import logger

router = APIRouter(prefix="/evidence", tags=["Evidence Files"])

@router.get("/{job_id}/{document_id}/crop/{crop_filename}")
def get_evidence_crop(job_id: str, document_id: str, crop_filename: str):
    candidates = [
        os.path.join(settings.output_dir, job_id, "evidence", crop_filename),
        os.path.join(settings.output_dir, "evidence", crop_filename),
        os.path.join(settings.output_dir, job_id, crop_filename),
    ]
    for p in candidates:
        if os.path.exists(p):
            return FileResponse(p, media_type="image/png")
            
    job_out_dir = os.path.join(settings.output_dir, job_id)
    if os.path.exists(job_out_dir):
        for root, _, files in os.walk(job_out_dir):
            if crop_filename in files:
                return FileResponse(os.path.join(root, crop_filename), media_type="image/png")
                
    raise HTTPException(status_code=404, detail=f"Evidence crop '{crop_filename}' not found.")


@router.get("/{job_id}/{document_id}/map-image")
def get_document_map_image(
    job_id: str,
    document_id: str,
    refresh: bool = Query(False, description="Force regenerate map render")
):
    """Retrieve full rendered map overview with AOI boundary highlight."""
    job_out_dir = os.path.join(settings.output_dir, job_id)
    doc_results_file = os.path.join(job_out_dir, "document_results.json")
    job_report_file = os.path.join(job_out_dir, "job_report.json")
    manifest_file = os.path.join(job_out_dir, "manifest.json")
    
    # 1. First, check if an existing rendered map overview already exists on disk
    if not refresh:
        existing_candidates = [
            os.path.join(job_out_dir, "evidence", f"aoi_overview_{document_id}.png"),
            os.path.join(job_out_dir, "evidence", f"map_render_{document_id}.png"),
            os.path.join(job_out_dir, f"aoi_overview_{document_id}.png"),
            os.path.join(job_out_dir, f"map_render_{document_id}.png"),
            os.path.join(settings.output_dir, "evidence", f"aoi_overview_{document_id}.png"),
            os.path.join(settings.output_dir, "evidence", f"map_render_{document_id}.png"),
        ]
        for p in existing_candidates:
            if os.path.exists(p):
                return FileResponse(p, media_type="image/png")
                
    # 2. Locate source PDF to render
    from src.utils.paths import resolve_folder_path
    root_dir = None
    fn = None
    
    # Try job_report.json
    if os.path.exists(job_report_file):
        try:
            with open(job_report_file, "r", encoding="utf-8") as f:
                rep = json.load(f)
                root_dir = rep.get("root_dir")
                for r in rep.get("results", []):
                    if r.get("document_id") == document_id or r.get("index_record_id") == document_id:
                        fn = r.get("filename")
                        break
        except Exception as e:
            logger.debug(f"Error reading {job_report_file}: {e}")

    # Try document_results.json
    if (not fn or not root_dir) and os.path.exists(doc_results_file):
        try:
            with open(doc_results_file, "r", encoding="utf-8") as f:
                docs = json.load(f)
                for d in docs:
                    if d.get("document_id") == document_id or d.get("index_record_id") == document_id:
                        fn = d.get("filename")
                        break
        except Exception as e:
            logger.debug(f"Error reading {doc_results_file}: {e}")

    # Try manifest.json
    if not root_dir and os.path.exists(manifest_file):
        try:
            with open(manifest_file, "r", encoding="utf-8") as f:
                man = json.load(f)
                root_dir = man.get("root_folder")
        except Exception as e:
            logger.debug(f"Error reading {manifest_file}: {e}")

    # Fallback root directory
    if not root_dir:
        raw_name = job_id.replace("JOB-", "")
        root_dir = resolve_folder_path(raw_name)
    else:
        root_dir = resolve_folder_path(root_dir)

    pdf_path = None
    search_dirs = [root_dir] if root_dir and os.path.exists(root_dir) else []
    data_dir_str = str(settings.data_dir)
    if data_dir_str not in search_dirs:
        search_dirs.append(data_dir_str)

    for sdir in search_dirs:
        if not sdir or not os.path.exists(sdir):
            continue
        if fn:
            for r, _, files in os.walk(sdir):
                if fn in files:
                    pdf_path = os.path.join(r, fn)
                    break
        else:
            for r, _, files in os.walk(sdir):
                for f in files:
                    if f.lower().endswith(".pdf") and (document_id in f or f in document_id):
                        pdf_path = os.path.join(r, f)
                        break
                if pdf_path:
                    break
        if pdf_path and os.path.exists(pdf_path):
            break

    if not pdf_path or not os.path.exists(pdf_path):
        raise HTTPException(status_code=404, detail=f"Source PDF for {document_id} not found on disk.")
        
    out_img = os.path.join(job_out_dir, "evidence", f"aoi_overview_{document_id}.png")
    os.makedirs(os.path.dirname(out_img), exist_ok=True)
    from src.aoi import get_document_aoi
    from src.evidence.crops import generate_aoi_map_render
    aoi = get_document_aoi(pdf_path, document_id, page_num=1)
    bbox = aoi.bbox if aoi else None
    res = generate_aoi_map_render(pdf_path, aoi.page_num if aoi else 1, bbox, out_img, dpi=200, aoi=aoi)
    if res and os.path.exists(out_img):
        return FileResponse(out_img, media_type="image/png")
        
    alt_img = os.path.join(job_out_dir, "evidence", f"map_render_{document_id}.png")
    if os.path.exists(alt_img):
        return FileResponse(alt_img, media_type="image/png")

    raise HTTPException(status_code=500, detail="Failed to render map image.")
