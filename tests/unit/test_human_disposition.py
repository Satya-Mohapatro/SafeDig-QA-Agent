import pytest
from src.domain.enums import Decision, HumanDispositionAction
from src.domain.audit import DecisionRecord, VersionSnapshot
from src.qa import human_disposition_service

def test_human_disposition_actions():
    version_snap = VersionSnapshot(
        engine_version="1.0.0",
        policy_version="1.0.0",
        warning_catalogue_version="1.0.0",
        legend_version="1.0.0"
    )
    drec = DecisionRecord(
        job_id="JOB-TEST",
        document_id="DOC-001",
        source_file_hash="abc123hash",
        decision=Decision.HUMAN_REVIEW,
        reason="Possible false positive claim",
        versions=version_snap
    )
    
    # 1. Reject warning (False alarm confirmed by human -> AUTO_CLEAR)
    updated = human_disposition_service.apply_disposition(
        decision_record=drec,
        action=HumanDispositionAction.REJECT_WARNING,
        reviewer_id="QA_SPECIALIST_42",
        reviewer_comment="Verified drawing; label refers to adjacent parcel."
    )
    assert updated.decision == Decision.AUTO_CLEAR
    assert updated.human_disposition == HumanDispositionAction.REJECT_WARNING
    assert "QA_SPECIALIST_42" in updated.reviewer_comment
    
    # 2. Block action
    blocked = human_disposition_service.apply_disposition(
        decision_record=drec,
        action=HumanDispositionAction.BLOCK,
        reviewer_id="QA_LEAD_01",
        reviewer_comment="Unreadable scan, requested re-order."
    )
    assert blocked.decision == Decision.BLOCKED
    assert blocked.human_disposition == HumanDispositionAction.BLOCK
