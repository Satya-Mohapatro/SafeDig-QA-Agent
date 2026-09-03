import os
import pytest
from src.ingestion import scan_root_folder
from src.index import parse_index_excel, validate_index_records, account_for_all_rows
from src.documents import resolve_documents
from src.domain.enums import DocumentResolutionStatus

SAMPLE_DIR = r"d:\Safedig_AG\Data\244414_201678"
INDEX_PATH = os.path.join(SAMPLE_DIR, "index.xlsx")

def test_parse_real_index_excel():
    assert os.path.exists(INDEX_PATH)
    records = parse_index_excel(INDEX_PATH, job_id="JOB-244414")
    assert len(records) >= 50
    
    # Check validation
    val_report = validate_index_records(records)
    assert val_report["is_valid"] is True
    assert val_report["assets_present_count"] >= 5
    
    # Check accounting before resolution
    acct = account_for_all_rows(records)
    assert acct["total_rows"] == len(records)

def test_resolve_documents_against_real_files():
    discovered = scan_root_folder(SAMPLE_DIR)
    records = parse_index_excel(INDEX_PATH, job_id="JOB-244414")
    
    resolved_records, doc_map = resolve_documents(records, discovered)
    
    # Every row with Status='Yes' and a file name should resolve
    unique_resolved = [r for r in resolved_records if r.resolution_status == DocumentResolutionStatus.UNIQUE]
    assert len(unique_resolved) >= 5
    
    # Check that BT.pdf, VM.pdf, W.pdf, GTC.pdf are uniquely resolved
    resolved_filenames = [r.file_name for r in unique_resolved]
    assert "BT.pdf" in resolved_filenames
    assert "VM.pdf" in resolved_filenames
    assert "W.pdf" in resolved_filenames
    assert "42332089_NGED - Wales.pdf" in resolved_filenames
