import pytest
from src.domain.enums import ReconciliationOutcome, Decision, Severity
from src.domain.reconciliation import ReconciliationResult
from src.domain.detection import DetectedCandidate
from src.domain.evidence import EvidencePackage, EvidenceItem
from src.domain.policy import PolicyResult
from src.agent import LLMAdvisoryService, advisory_service

def test_deterministic_advisory_missed_warning():
    reconcil = ReconciliationResult(
        reconciliation_id="REC-TEST-001",
        document_id="DOC-001",
        outcome=ReconciliationOutcome.MISSED_WARNING,
        detected_candidates=[
            DetectedCandidate(
                candidate_id="CAND-01",
                document_id="DOC-001",
                page_num=1,
                warning_code="SGN_HP_GAS",
                business_warning_text="High Pressure Gas Line",
                severity=Severity.HIGH,
                detection_method="VECTOR_ANALYSIS"
            )
        ],
        explanation="Upstream reported clean, but independent scan found SGN_HP_GAS."
    )
    ev_pkg = EvidencePackage(
        package_id="PKG-001",
        document_id="DOC-001",
        items=[
            EvidenceItem(
                evidence_id="E-001",
                document_id="DOC-001",
                page_num=1,
                evidence_type="SPATIAL_INTERSECTION",
                description="High Pressure Gas Line intersecting AOI"
            )
        ],
        is_complete=True
    )
    pol_res = PolicyResult(
        document_id="DOC-001",
        decision=Decision.HUMAN_REVIEW,
        reason="Missed critical warning"
    )
    
    adv = advisory_service.generate_advisory(None, reconcil, ev_pkg, pol_res)
    assert adv.document_id == "DOC-001"
    assert "CRITICAL HAZARD" in adv.summary
    assert len(adv.contradictions_detected) > 0
    assert "E-001" in adv.recommended_evidence_ids
    assert adv.is_fallback is True

def test_llm_cannot_override_policy_invariant():
    # Invariant: Advisory is strictly informational metadata and contains no release execution method
    reconcil = ReconciliationResult(
        reconciliation_id="REC-TEST-002",
        document_id="DOC-002",
        outcome=ReconciliationOutcome.CONFIRMED_CLEAN,
        explanation="Clean"
    )
    pol_res = PolicyResult(
        document_id="DOC-002",
        decision=Decision.AUTO_CLEAR,
        reason="Clean"
    )
    adv = advisory_service.generate_advisory(None, reconcil, None, pol_res)
    assert not hasattr(adv, "authorize_release")
    assert not hasattr(adv, "override_decision")
