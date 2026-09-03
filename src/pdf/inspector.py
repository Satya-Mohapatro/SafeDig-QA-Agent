import os
import fitz  # PyMuPDF
from typing import List, Tuple, Dict, Any
from src.domain.document import Document, DocumentPage
from src.domain.enums import PDFModality
from src.config.logging import logger

def inspect_pdf(pdf_path: str, document_id: str, job_id: str, file_id: str, sha256: str) -> Document:
    if not os.path.exists(pdf_path):
        return Document(
            document_id=document_id,
            job_id=job_id,
            file_id=file_id,
            filename=os.path.basename(pdf_path),
            sha256=sha256,
            page_count=0,
            is_corrupted=True,
            modality=PDFModality.UNREADABLE
        )
        
    try:
        doc = fitz.open(pdf_path)
        page_count = len(doc)
        pages: List[DocumentPage] = []
        
        total_vectors = 0
        total_images = 0
        
        for p_idx in range(page_count):
            page = doc[p_idx]
            rect = page.rect
            text = page.get_text()
            images = page.get_images()
            drawings = page.get_drawings()
            
            vec_count = len(drawings)
            img_count = len(images)
            total_vectors += vec_count
            total_images += img_count
            
            # Classify page modality
            if vec_count > 10 and img_count == 0:
                modality = PDFModality.VECTOR
            elif vec_count > 10 and img_count > 0:
                modality = PDFModality.HYBRID
            elif img_count > 0:
                modality = PDFModality.RASTER
            else:
                modality = PDFModality.VECTOR
                
            pages.append(DocumentPage(
                page_num=p_idx + 1,
                width_pt=rect.width,
                height_pt=rect.height,
                has_text=len(text.strip()) > 0,
                text_snippet=text[:300].replace("\n", " "),
                vector_paths_count=vec_count,
                images_count=img_count,
                modality=modality
            ))
            
        doc_modality = PDFModality.VECTOR
        if total_vectors > 50 and total_images > 0:
            doc_modality = PDFModality.HYBRID
        elif total_vectors <= 10 and total_images > 0:
            doc_modality = PDFModality.RASTER
            
        return Document(
            document_id=document_id,
            job_id=job_id,
            file_id=file_id,
            filename=os.path.basename(pdf_path),
            sha256=sha256,
            page_count=page_count,
            pages=pages,
            modality=doc_modality,
            is_corrupted=False
        )
    except Exception as e:
        logger.error(f"Error inspecting PDF {pdf_path}: {e}")
        return Document(
            document_id=document_id,
            job_id=job_id,
            file_id=file_id,
            filename=os.path.basename(pdf_path),
            sha256=sha256,
            page_count=0,
            is_corrupted=True,
            modality=PDFModality.UNREADABLE
        )
