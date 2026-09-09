import os
import pytest
from src.pdf import inspect_pdf, extract_page_vector_paths, extract_page_words_and_text
from src.domain.enums import PDFModality
from tests.conftest import PROJECT_ROOT, DATA_DIR, SAMPLE_FOLDER_244414, SAMPLE_NGED_PDF

SAMPLE_PDF = str(SAMPLE_NGED_PDF)

def test_inspect_real_pdf():
    assert os.path.exists(SAMPLE_PDF)
    doc = inspect_pdf(SAMPLE_PDF, "DOC-001", "JOB-101", "FIL-001", "fakehash")
    assert doc.page_count >= 1
    assert doc.is_corrupted is False
    assert doc.modality in [PDFModality.VECTOR, PDFModality.HYBRID]
    
    # Check page 1 details
    p1 = doc.pages[0]
    assert p1.width_pt > 0
    assert p1.height_pt > 0
    assert p1.vector_paths_count > 0

def test_extract_vectors_and_words():
    drawings = extract_page_vector_paths(SAMPLE_PDF, 1)
    assert len(drawings) > 0
    
    words = extract_page_words_and_text(SAMPLE_PDF, 1)
    assert len(words) > 0
