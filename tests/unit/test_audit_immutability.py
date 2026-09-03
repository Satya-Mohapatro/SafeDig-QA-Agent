import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.db.models import Base, AuditLogRecord

@pytest.fixture
def sync_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    Base.metadata.drop_all(engine)

def test_audit_log_insert_succeeds(sync_db):
    log = AuditLogRecord(
        job_id="JOB-AUDIT-01",
        document_id="DOC-01",
        action="DOCUMENT_DECISION",
        actor="SYSTEM",
        detail_json='{"decision": "AUTO_CLEAR"}',
    )
    sync_db.add(log)
    sync_db.commit()

    retrieved = sync_db.query(AuditLogRecord).filter_by(job_id="JOB-AUDIT-01").first()
    assert retrieved is not None
    assert retrieved.action == "DOCUMENT_DECISION"

def test_audit_log_update_raises_error(sync_db):
    log = AuditLogRecord(
        job_id="JOB-AUDIT-02",
        action="JOB_STARTED",
        actor="SYSTEM",
    )
    sync_db.add(log)
    sync_db.commit()

    # Attempt to modify the audit log entry
    log.action = "TAMPERED_ACTION"
    with pytest.raises(RuntimeError, match="SECURITY VIOLATION"):
        sync_db.commit()

def test_audit_log_delete_raises_error(sync_db):
    log = AuditLogRecord(
        job_id="JOB-AUDIT-03",
        action="HUMAN_DISPOSITION",
        actor="HUMAN",
    )
    sync_db.add(log)
    sync_db.commit()

    # Attempt to delete the audit log entry
    sync_db.delete(log)
    with pytest.raises(RuntimeError, match="SECURITY VIOLATION"):
        sync_db.commit()
