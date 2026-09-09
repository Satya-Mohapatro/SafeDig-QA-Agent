import pytest
from src.reconciliation import reconcile_warnings
from src.domain.warning import ClaimedWarning
from src.domain.detection import DetectedCandidate
from src.domain.enums import ReconciliationOutcome, Severity, DetectionMethod, GeometryType

def test_reconciliation_match():
    claimed = ClaimedWarning(
        claimed_warning_id="CLM-1",
        document_id="DOC-1",
        raw_warning_text="There is a High Pressure Gas Line in this area | ",
        severity=Severity.HIGH
    )
    detected = [
        DetectedCandidate(
            candidate_id="CAND-1",
            document_id="DOC-1",
            page_num=1,
            warning_code="SGN_HP_GAS",
            business_warning_text="High Pressure Gas Line",
            severity=Severity.HIGH,
            detection_method=DetectionMethod.VECTOR_ANALYSIS,
            geometry_type=GeometryType.LINE,
            intersects_aoi=True
        )
    ]
    res = reconcile_warnings("DOC-1", claimed, detected)
    assert res.outcome == ReconciliationOutcome.MATCH
    assert res.severity == Severity.HIGH

def test_reconciliation_missed_warning():
    # Upstream claimed nothing, but independent QA found high pressure gas
    detected = [
        DetectedCandidate(
            candidate_id="CAND-1",
            document_id="DOC-1",
            page_num=1,
            warning_code="SGN_HP_GAS",
            business_warning_text="High Pressure Gas Line",
            severity=Severity.HIGH,
            detection_method=DetectionMethod.VECTOR_ANALYSIS,
            geometry_type=GeometryType.LINE,
            intersects_aoi=True
        )
    ]
    res = reconcile_warnings("DOC-1", None, detected)
    assert res.outcome == ReconciliationOutcome.MISSED_WARNING
    assert res.severity == Severity.HIGH

def test_reconciliation_clean():
    res = reconcile_warnings("DOC-1", None, [])
    assert res.outcome == ReconciliationOutcome.CONFIRMED_CLEAN
