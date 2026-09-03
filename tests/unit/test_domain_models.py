import pytest
from src.domain import (
    FileClassification,
    DocumentResolutionStatus,
    PDFModality,
    Severity,
    GeometryType,
    AOIDetectionMethod,
    DetectionMethod,
    ReconciliationOutcome,
    Decision,
    IndexRecord,
    DiscoveredFile,
    Document,
    DocumentPage,
    WarningDefinition,
    ClaimedWarning,
    LegendProfile,
    LegendFeature,
    ColorSignature,
    StrokeStyle,
    AOI,
    DetectedCandidate,
    EvidenceItem,
    EvidencePackage,
    ReconciliationResult,
    PolicyResult,
    GateCheck,
    VersionSnapshot,
    DecisionRecord,
)
from src.config import settings

def test_settings_loaded():
    assert settings.app_name == "AI Map QA & Validation Agent"
    assert settings.safe_mode is True
    assert settings.engine_version == "1.0.0"

def test_index_record_creation():
    rec = IndexRecord(
        index_record_id="IDX-001",
        job_id="JOB-101",
        row_index=1,
        file_name="42332089_NGED - Wales.pdf",
        utility_name="National Grid Electricity Distribution",
        utility_type="Electricity",
        raw_status="Yes",
        is_asset_present=True,
        raw_warning="There is a 11kV High Voltage Electricity Line in this Area |",
        raw_comments="100.0",
        resolution_status=DocumentResolutionStatus.UNIQUE,
    )
    assert rec.is_asset_present is True
    assert rec.resolution_status == DocumentResolutionStatus.UNIQUE

def test_discovered_file():
    df = DiscoveredFile(
        file_id="FIL-001",
        relative_path="42332089_NGED - Wales.pdf",
        filename="42332089_NGED - Wales.pdf",
        extension=".pdf",
        mime_type="application/pdf",
        size_bytes=260286,
        sha256="abc123hash",
        classification=FileClassification.MAP,
    )
    assert df.classification == FileClassification.MAP
    assert df.extension == ".pdf"

def test_warning_definition():
    wdef = WarningDefinition(
        warning_code="SGN_HP_GAS",
        provider="SGN",
        utility_type="Gas",
        business_warning_text="There is a High Pressure Gas Line in this area | ",
        severity=Severity.HIGH,
        geometry_type=GeometryType.LINE,
        aoi_required=True,
    )
    assert wdef.severity == Severity.HIGH
    assert wdef.geometry_type == GeometryType.LINE

def test_evidence_package():
    item1 = EvidenceItem(
        evidence_id="E-000001",
        document_id="DOC-001",
        page_num=1,
        evidence_type="MAP_CROP",
        description="High pressure gas line crop intersecting AOI",
    )
    pkg = EvidencePackage(
        package_id="PKG-001",
        document_id="DOC-001",
        items=[item1],
        is_complete=True,
    )
    assert len(pkg.items) == 1
    assert pkg.items[0].evidence_id == "E-000001"

def test_policy_result():
    gates = {
        "index_valid": GateCheck(gate_name="index_valid", passed=True, reason="Index valid"),
        "map_readable": GateCheck(gate_name="map_readable", passed=True, reason="PDF intact"),
    }
    res = PolicyResult(
        document_id="DOC-001",
        decision=Decision.AUTO_CLEAR,
        reason="All gates passed",
        gates=gates,
        safe_mode_applied=False,
    )
    assert res.decision == Decision.AUTO_CLEAR
    assert res.gates["index_valid"].passed is True
