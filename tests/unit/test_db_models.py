import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.db.models import (
    Base,
    JobRecord,
    DocumentRecord,
    EvidenceItemRecord,
    ReconciliationRecord,
    PolicyResultRecord,
    AuditLogRecord,
    HumanDispositionRecord,
)

@pytest.fixture
def sync_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    Base.metadata.drop_all(engine)

def test_job_model_creation(sync_db):
    job = JobRecord(
        job_id="TEST-JOB-001",
        root_dir="/data/sample",
        status="COMPLETED",
        total_documents=5,
        auto_clear_count=3,
        human_review_count=1,
        blocked_count=1,
    )
    sync_db.add(job)
    sync_db.commit()

    retrieved = sync_db.query(JobRecord).filter_by(job_id="TEST-JOB-001").first()
    assert retrieved is not None
    assert retrieved.job_id == "TEST-JOB-001"
    assert retrieved.status == "COMPLETED"
    assert retrieved.auto_clear_count == 3
    assert retrieved.human_review_count == 1
    assert retrieved.blocked_count == 1

def test_document_and_relationships(sync_db):
    job = JobRecord(job_id="TEST-JOB-REL", root_dir="/data/sample", status="RUNNING")
    sync_db.add(job)
    sync_db.commit()

    doc = DocumentRecord(
        document_id="DOC-001",
        job_id="TEST-JOB-REL",
        filename="map1.pdf",
        sha256="abc123hash",
        provider="Virgin Media",
        utility_type="TELECOMS",
        decision="HUMAN_REVIEW",
        decision_reason="Possible false positive warning",
    )
    sync_db.add(doc)
    sync_db.commit()

    # Evidence
    ev = EvidenceItemRecord(
        evidence_id="EV-001",
        document_id="DOC-001",
        page_num=1,
        evidence_type="AOI_CROPPED_IMAGE",
        description="Hazard near red boundary",
        data_json='{"confidence": 0.95}',
    )
    # Reconciliation
    recon = ReconciliationRecord(
        reconciliation_id="REC-001",
        document_id="DOC-001",
        outcome="MATCH",
        severity="HIGH",
        explanation="Warning detected and matched",
    )
    # Policy
    pol = PolicyResultRecord(
        document_id="DOC-001",
        decision="HUMAN_REVIEW",
        reason="Requires visual confirmation",
    )
    sync_db.add_all([ev, recon, pol])
    sync_db.commit()

    doc_queried = sync_db.query(DocumentRecord).filter_by(document_id="DOC-001").first()
    assert doc_queried is not None
    assert len(doc_queried.evidence_items) == 1
    assert doc_queried.reconciliations[0].outcome == "MATCH"
    assert doc_queried.policy_results[0].decision == "HUMAN_REVIEW"
