import os
import pytest
from src.evidence import build_evidence_package, verify_evidence_completeness
from src.domain.document import Document
from src.domain.aoi import AOI
from src.domain.reconciliation import ReconciliationResult
from src.domain.enums import ReconciliationOutcome, Severity, AOIDetectionMethod

SAMPLE_PDF = r"d:\Safedig_AG\Data\244414_201678\42332089_NGED - Wales.pdf"

def test_build_evidence():
    doc = Document(
        document_id="DOC-TEST",
        job_id="JOB-101",
        file_id="FIL-001",
        filename="42332089_NGED - Wales.pdf",
        sha256="fakehash123",
        page_count=1
    )
    aoi = AOI(
        aoi_id="AOI-1",
        document_id="DOC-TEST",
        page_num=1,
        method=AOIDetectionMethod.NATIVE_VECTOR,
        coordinates=[(100, 100), (200, 100), (200, 200), (100, 200), (100, 100)],
        bbox=[100, 100, 200, 200],
        is_valid=True
    )
    rec = ReconciliationResult(
        reconciliation_id="REC-1",
        document_id="DOC-TEST",
        outcome=ReconciliationOutcome.CONFIRMED_CLEAN,
        explanation="Clean map"
    )
    
    pkg = build_evidence_package(SAMPLE_PDF, doc, aoi, rec)
    assert pkg.is_complete is True
    assert len(pkg.items) >= 2
