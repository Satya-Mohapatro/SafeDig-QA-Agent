import os
import pytest
from src.ingestion import scan_root_folder
from src.index import parse_index_excel, validate_index_records, account_for_all_rows
from src.documents import resolve_documents
from src.domain.enums import DocumentResolutionStatus
from tests.conftest import PROJECT_ROOT, DATA_DIR, SAMPLE_FOLDER_244414, SAMPLE_NGED_PDF

SAMPLE_DIR = str(SAMPLE_FOLDER_244414)
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


def test_parse_index_with_foreign_machine_path():
    """Verify that paths from other machines are seamlessly resolved without FileNotFoundError."""
    foreign_paths = [
        "d:/Safedig_AG/data/244414_201678/index.xlsx",
        "C:/Users/SomeUser/Desktop/SafeDig/Data/244414_201678/index.xlsx",
        "/opt/safedig/Data/244414_201678/index.xlsx",
        "Data/244414_201678/index.xlsx",
        "244414_201678",
    ]
    for fp in foreign_paths:
        records = parse_index_excel(fp, job_id="JOB-FOREIGN-TEST")
        assert len(records) >= 50, f"Failed to parse records from foreign path: {fp}"


def test_portable_paths_utility():
    """Verify resolve_folder_path, resolve_index_path, and resolve_file_path."""
    from src.utils.paths import resolve_folder_path, resolve_index_path, resolve_file_path
    
    # Folder resolution
    f1 = resolve_folder_path("d:/Safedig_AG/data/244414_201678")
    assert os.path.isdir(f1)
    assert "244414_201678" in f1
    
    f2 = resolve_folder_path("244414_201678")
    assert os.path.isdir(f2)
    assert "244414_201678" in f2
    
    # Index resolution
    idx1 = resolve_index_path("d:/Safedig_AG/data/244414_201678")
    assert os.path.isfile(idx1)
    assert idx1.lower().endswith((".xlsx", ".xls"))
    
    idx2 = resolve_index_path("d:/Safedig_AG/data/244414_201678/index.xlsx")
    assert os.path.isfile(idx2)
    
    # File resolution
    pdf = resolve_file_path("42332089_WWU.pdf", "d:/Safedig_AG/data/244414_201678")
    assert os.path.isfile(pdf)

