from typing import List, Dict, Any
from src.pdf.extractor import extract_page_words_and_text
from src.config.logging import logger

class OCRService:
    @staticmethod
    def extract_text_and_labels(pdf_path: str, page_num: int) -> List[Dict[str, Any]]:
        # Native PDF text words extraction with coordinates
        try:
            return extract_page_words_and_text(pdf_path, page_num)
        except Exception as e:
            logger.error(f"OCR extraction failed for {pdf_path} page {page_num}: {e}")
            return []

ocr_service = OCRService()
