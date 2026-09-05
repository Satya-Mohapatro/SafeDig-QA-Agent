import pytest
import os
from src.qa.workspace import workspace_builder
from src.domain.index_record import IndexRecord
from src.domain.document import DiscoveredFile
from src.domain.enums import FileClassification
from tests.conftest import PROJECT_ROOT, DATA_DIR, SAMPLE_FOLDER_244414, SAMPLE_NGED_PDF

SAMPLE_FOLDER = str(SAMPLE_FOLDER_244414)
SAMPLE_PDF = os.path.join(SAMPLE_FOLDER, "42332089_WWU.pdf")

def test_workspace_payload_builder():
    assert os.path.exists(SAMPLE_PDF)
    rec = IndexRecord(
        index_record_id="IDX-TEST-001",
        job_id="TEST-JOB",
        row_index=1,
        utility_name="Wales and West Utilities",
        utility_type="Gas",
        raw_status="Yes",
        is_asset_present=True,
        raw_warning="There is a High Pressure Gas Line in this area"
    )
    disc_file = DiscoveredFile(
        file_id="FIL-0002",
        relative_path="42332089_WWU.pdf",
        filename="42332089_WWU.pdf",
        extension=".pdf",
        mime_type="application/pdf",
        size_bytes=os.path.getsize(SAMPLE_PDF),
        sha256="testhash123",
        classification=FileClassification.MAP,
        metadata={"full_path": SAMPLE_PDF}
    )
    
    payload = workspace_builder.build_workspace_payload(
        job_id="TEST-JOB",
        root_dir=SAMPLE_FOLDER,
        record=rec,
        matched_file=disc_file
    )
    
    assert payload.document_id == "DOC-FIL-0002"
    assert payload.utility_name == "Wales and West Utilities"
    assert payload.page_count > 0
    assert payload.aoi_method in ["NATIVE_VECTOR", "FALLBACK"]
    assert payload.evidence_package_id.startswith("PKG-")
    assert len(payload.evidence_items) >= 2
    assert "01_INDEX_VALID" in payload.gates
    assert payload.advisory is not None
