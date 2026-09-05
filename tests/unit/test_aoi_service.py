import os
import pytest
from src.aoi import get_document_aoi
from src.domain.enums import GeometryType
from tests.conftest import PROJECT_ROOT, DATA_DIR, SAMPLE_FOLDER_244414, SAMPLE_NGED_PDF

SAMPLE_PDF = str(SAMPLE_NGED_PDF)

def test_detect_aoi():
    assert os.path.exists(SAMPLE_PDF)
    aoi = get_document_aoi(SAMPLE_PDF, "DOC-001", page_num=1)
    assert aoi.is_valid is True
    assert aoi.geometry_type == GeometryType.POLYGON
    assert aoi.confidence > 0.5
    assert len(aoi.coordinates) >= 4
