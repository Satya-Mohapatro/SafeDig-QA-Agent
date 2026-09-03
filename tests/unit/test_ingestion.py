import os
import pytest
from src.ingestion import scan_root_folder, compute_sha256, classify_file, build_manifest
from src.domain.enums import FileClassification

SAMPLE_DIR = r"d:\Safedig_AG\Data\244414_201678"

def test_file_classification():
    assert classify_file("index.xlsx") == FileClassification.INDEX
    assert classify_file("index_org.xlsx") == FileClassification.INDEX
    assert classify_file("42332089_NGED - Wales.pdf") == FileClassification.MAP
    assert classify_file("BT.pdf") == FileClassification.MAP
    assert classify_file("NGED Safety Look Out Look Up Booklet.pdf") == FileClassification.SAFETY_REFERENCE
    assert classify_file("NGED Avoidance of Danger.pdf") == FileClassification.SAFETY_REFERENCE

def test_scan_real_sample_folder():
    assert os.path.exists(SAMPLE_DIR)
    discovered = scan_root_folder(SAMPLE_DIR)
    assert len(discovered) == 15
    
    # Check that SHA-256 hashes are 64-char hex strings
    for f in discovered:
        assert len(f.sha256) == 64
        
    # Check manifest building
    manifest = build_manifest("JOB-244414", SAMPLE_DIR, discovered)
    assert manifest["total_files"] == 15
    assert manifest["classification_summary"]["MAP"] >= 6
    assert manifest["classification_summary"]["INDEX"] == 2
