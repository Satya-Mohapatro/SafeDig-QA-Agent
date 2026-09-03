import pymupdf
import os
from typing import Optional
from src.config.logging import logger

def render_page_to_image(pdf_path: str, page_num: int, output_image_path: str, dpi: int = 300) -> Optional[str]:
    """Render a PDF page to a high-DPI PNG image using PyMuPDF.
    
    - Uses COLORSPACE_RGB for correct color fidelity (not BGR).
    - alpha=False keeps transparent backgrounds white.
    - Writes PNG with lossless compression.
    """
    try:
        doc = pymupdf.open(pdf_path)
        if page_num < 1 or page_num > len(doc):
            logger.warning(f"Page {page_num} out of range (doc has {len(doc)} pages): {pdf_path}")
            return None
        page = doc[page_num - 1]
        zoom = dpi / 72.0
        mat = pymupdf.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, alpha=False, colorspace=pymupdf.csRGB)
        os.makedirs(os.path.dirname(output_image_path), exist_ok=True)
        pix.save(output_image_path)
        doc.close()
        return output_image_path
    except Exception as e:
        logger.error(f"Failed to render page {page_num} of {pdf_path}: {e}")
        return None
