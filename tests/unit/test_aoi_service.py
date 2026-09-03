import os
import pytest
from src.aoi import get_document_aoi
from src.domain.enums import GeometryType

SAMPLE_PDF = r"d:\Safedig_AG\Data\244414_201678\42332089_NGED - Wales.pdf"

def test_detect_aoi():
    assert os.path.exists(SAMPLE_PDF)
    aoi = get_document_aoi(SAMPLE_PDF, "DOC-001", page_num=1)
    assert aoi.is_valid is True
    assert aoi.geometry_type == GeometryType.POLYGON
    assert aoi.confidence > 0.5
    assert len(aoi.coordinates) >= 4
