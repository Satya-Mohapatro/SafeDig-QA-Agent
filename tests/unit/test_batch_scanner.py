import pytest
import os
from src.batch.scanner import directory_scanner
from tests.conftest import PROJECT_ROOT, DATA_DIR, SAMPLE_FOLDER_244414, SAMPLE_NGED_PDF

def test_directory_scanner_discovers_all_data_folders():
    parent_dir = str(DATA_DIR)
    assert os.path.exists(parent_dir)
    
    folders = directory_scanner.scan_for_job_folders(parent_dir, recursive=False)
    assert len(folders) == 13
    
    # All folders must contain index.xlsx
    for f in folders:
        assert os.path.isdir(f)
        assert os.path.exists(os.path.join(f, "index.xlsx"))
