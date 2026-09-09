import pytest
from src.policy import policy_engine
from src.domain.index_record import IndexRecord
from src.domain.document import Document
from src.domain.aoi import AOI
from src.domain.legend import LegendProfile
from src.domain.reconciliation import ReconciliationResult
from src.domain.evidence import EvidencePackage, EvidenceItem
from src.domain.enums import Decision, ReconciliationOutcome, DocumentResolutionStatus, AOIDetectionMethod

def test_policy_missed_warning_forces_human_review():
    rec = IndexRecord(
        index_record_id="IDX-1",
        job_id="JOB-1",
        row_index=1,
        file_name="map.pdf",
        utility_name="SGN",
        utility_type="Gas",
        raw_status="Yes",
        is_asset_present=True,
        resolution_status=DocumentResolutionStatus.UNIQUE
    )
    doc = Document(
        document_id="DOC-1",
        job_id="JOB-1",
        file_id="FIL-1",
        filename="map.pdf",
        sha256="hash",
        page_count=1
    )
    aoi = AOI(
        aoi_id="AOI-1",
        document_id="DOC-1",
        page_num=1,
        method=AOIDetectionMethod.NATIVE_VECTOR,
        coordinates=[(0, 0), (10, 0), (10, 10), (0, 10), (0, 0)],
        is_valid=True
    )
    reconcil = ReconciliationResult(
        reconciliation_id="REC-1",
        document_id="DOC-1",
        outcome=ReconciliationOutcome.MISSED_WARNING,
        explanation="Missed HP gas line"
    )
    ev_pkg = EvidencePackage(
        package_id="PKG-1",
        document_id="DOC-1",
        items=[
            EvidenceItem(evidence_id="E-1", document_id="DOC-1", page_num=1, evidence_type="SOURCE_FILE", description="src"),
            EvidenceItem(evidence_id="E-2", document_id="DOC-1", page_num=1, evidence_type="AOI_GEOMETRY", description="aoi"),
            EvidenceItem(evidence_id="E-3", document_id="DOC-1", page_num=1, evidence_type="SPATIAL_INTERSECTION", description="spatial"),
            EvidenceItem(evidence_id="E-4", document_id="DOC-1", page_num=1, evidence_type="MAP_CROP", description="crop")
        ],
        is_complete=True
    )
    
    res = policy_engine.evaluate(
        index_record=rec,
        document=doc,
        legend_profile=LegendProfile(legend_id="LGD-1", provider="SGN", utility_type="Gas"),
        aoi=aoi,
        reconciliation=reconcil,
        evidence_pkg=ev_pkg
    )
    assert res.decision == Decision.HUMAN_REVIEW
    assert "MANDATORY HUMAN REVIEW" in res.reason
