from typing import Optional
from src.domain.aoi import AOI
from .detector import detect_aoi_from_pdf

def get_document_aoi(pdf_path: str, document_id: str, page_num: int = 1) -> AOI:
    return detect_aoi_from_pdf(pdf_path, document_id, page_num)
