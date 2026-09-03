import fitz
import pymupdf
from typing import List, Dict, Any

def extract_page_vector_paths(pdf_path: str, page_num: int) -> List[Dict[str, Any]]:
    """Extract all vector drawing paths from a PDF page.
    
    Returns complete drawing dict list from PyMuPDF including:
    - 'color': stroke color (0-1 float tuples, or CMYK 4-tuples)
    - 'fill': fill color
    - 'width': stroke width in points
    - 'dashes': dash pattern string (e.g. '[ 12 6 ] 0')
    - 'items': list of path commands [('l', p1, p2), ('re', rect, 1), ('c', ...)]
    - 'rect': bounding Rect of the whole drawing
    """
    doc = pymupdf.open(pdf_path)
    if page_num < 1 or page_num > len(doc):
        return []
    page = doc[page_num - 1]
    drawings = page.get_drawings()
    # Enrich: add page dimensions to each drawing for AOI-relative filtering
    page_rect = page.rect
    for d in drawings:
        d["_page_width"] = page_rect.width
        d["_page_height"] = page_rect.height
    return drawings

def extract_page_words_and_text(pdf_path: str, page_num: int) -> List[Dict[str, Any]]:
    """Extract all text words with bounding boxes from a PDF page."""
    doc = pymupdf.open(pdf_path)
    if page_num < 1 or page_num > len(doc):
        return []
    page = doc[page_num - 1]
    # words: (x0, y0, x1, y1, word, block_no, line_no, word_no)
    words_raw = page.get_text("words")
    words = []
    for w in words_raw:
        words.append({
            "bbox": [w[0], w[1], w[2], w[3]],
            "text": w[4],
            "block_no": w[5],
            "line_no": w[6],
            "word_no": w[7]
        })
    return words

def extract_text_blocks_in_aoi(pdf_path: str, page_num: int, aoi_bbox: List[float]) -> List[str]:
    """Extract all text strings found inside the AOI bounding box on the given page.
    
    Used to detect text labels like '100 mm', '150 mm', 'TRUNK', 'HP', 'HV' etc.
    overlaid on utility lines within the excavation site boundary.
    """
    doc = pymupdf.open(pdf_path)
    if page_num < 1 or page_num > len(doc):
        return []
    page = doc[page_num - 1]
    x0, y0, x1, y1 = aoi_bbox
    aoi_rect = pymupdf.Rect(x0, y0, x1, y1)
    clip_text = page.get_text("text", clip=aoi_rect)
    if clip_text:
        return [line.strip() for line in clip_text.splitlines() if line.strip()]
    return []
