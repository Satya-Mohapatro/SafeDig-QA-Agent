import os
import fitz  # PyMuPDF
from typing import List, Tuple, Dict, Any
from src.domain.document import Document, DocumentPage
from src.domain.enums import PDFModality
from src.config.logging import logger

def _find_map_page_in_doc(doc: fitz.Document) -> Tuple[int, bool]:
    """Identify the primary engineering map page and whether the document has map data.
    
    Returns (page_num, is_map):
    - page_num: 1-indexed page number containing the map
    - is_map: True if the document has actual map cartography; False if letter/notice only
    """
    page_count = len(doc)
    if page_count == 0:
        return 1, False

    try:
        from src.aoi.detector import _score_vector_drawings, _find_vector_map_frame
    except ImportError:
        return 1, True

    if page_count == 1:
        p0 = doc[0]
        has_frame = bool(_find_vector_map_frame(p0))
        dwgs = len(p0.get_drawings())
        imgs = len(p0.get_images())
        txt_len = len(p0.get_text().strip())
        is_notice = (not has_frame and dwgs < 15 and imgs <= 6 and txt_len > 300)
        return 1, not is_notice

    # Multi-page documents:
    # 1. Search for explicit vector boundary (dashed circle / polygon AOI)
    best_p = 1
    best_score = -1
    found_boundary = False
    for idx, page in enumerate(doc):
        p_num = idx + 1
        scored = _score_vector_drawings(page.get_drawings(), page.rotation, page.mediabox, page.rect)
        if scored and scored[0][0] >= 120 and scored[0][0] > best_score:
            best_score = scored[0][0]
            best_p = p_num
            found_boundary = True
    if found_boundary:
        return best_p, True

    # 2. Search for explicit vector map frame
    for idx, page in enumerate(doc):
        p_num = idx + 1
        if _find_vector_map_frame(page):
            return p_num, True

    # 3. Density scoring (drawings + images - text)
    best_density = -1
    for idx, page in enumerate(doc):
        p_num = idx + 1
        dwgs = len(page.get_drawings())
        imgs = len(page.get_images())
        txt_len = len(page.get_text().strip())
        score = dwgs + imgs * 50 - (txt_len if txt_len > 800 else 0)
        if score > best_density:
            best_density = score
            best_p = p_num

    is_map = best_density > 25
    return best_p, is_map


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

        map_page_num, is_map = _find_map_page_in_doc(doc)

        # Check for extracted text / notices indicating missing plant data or portal enquiry receipts
        extracted_notice = None
        is_missing_data = not is_map
        
        # Check first page text or OCR
        text0 = doc[0].get_text().strip() if page_count > 0 else ""
        if not text0 and doc_modality == PDFModality.RASTER and page_count > 0:
            try:
                import winocr
                from PIL import Image
                pix = doc[0].get_pixmap(dpi=150)
                img = Image.frombytes('RGB', [pix.width, pix.height], pix.samples)
                res = winocr.recognize_pil_sync(img, 'en')
                text0 = res.get('text', '').strip()
            except Exception as ex:
                logger.debug(f"OCR inspection error for {pdf_path}: {ex}")
                
        # Scan pages for official notices (portal enquiry or no assets affected)
        notice_indicators = [
            "enquiry result",
            "the following sites are affected",
            "please check your email",
            "no gtc plant has been found",
            "delay of up to 30 minutes before you receive the email response",
            "submit enquiry",
            "create polygon",
            "modify polygon",
            "no assets affected",
            "not affect any nget apparatus",
            "not affect any apparatus",
            "no apparatus affected",
            "no plant has been found",
            "no recorded apparatus",
            "no apparatus in the vicinity",
            "no assets found",
            "no plant affected",
            "no apparatus has been found",
            "no electrical assets affected",
            "no gas assets affected",
            "no water assets affected",
        ]
        
        all_text_to_check = text0
        for p_i in range(1, min(3, page_count)):
            all_text_to_check += " " + doc[p_i].get_text().strip()
            
        if all_text_to_check:
            text_lower = all_text_to_check.lower()
            if any(ind in text_lower for ind in notice_indicators):
                extracted_notice = all_text_to_check[:400].replace("\n", " ").strip()
                logger.info(f"Detected notice in {pdf_path}: {extracted_notice[:100]}...")
            
            portal_indicators = [
                "enquiry result", "the following sites are affected", "please check your email",
                "delay of up to 30 minutes before you receive the email response",
                "submit enquiry", "create polygon", "modify polygon"
            ]
            if (not is_map) or any(ind in text_lower for ind in portal_indicators):
                is_missing_data = True
                logger.warning(f"Marked is_missing_map_data=True for {pdf_path} (is_map={is_map})")
            
        return Document(
            document_id=document_id,
            job_id=job_id,
            file_id=file_id,
            filename=os.path.basename(pdf_path),
            sha256=sha256,
            page_count=page_count,
            pages=pages,
            modality=doc_modality,
            is_corrupted=False,
            extracted_notice=extracted_notice,
            is_missing_map_data=is_missing_data,
            map_page_num=map_page_num
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
