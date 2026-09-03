import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from src.db.models import Base
from src.db.repositories import (
    job_repo,
    document_repo,
    evidence_repo,
    reconciliation_repo,
    policy_repo,
    audit_repo,
    disposition_repo,
)

@pytest.fixture
async def async_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session_maker() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

@pytest.mark.anyio
async def test_job_repository_crud(async_session):
    job = await job_repo.create_job(async_session, "JOB-REPO-01", "/path/to/job", status="RUNNING")
    await async_session.commit()

    retrieved = await job_repo.get_job(async_session, "JOB-REPO-01")
    assert retrieved is not None
    assert retrieved.status == "RUNNING"

    updated = await job_repo.update_job_status(
        async_session, "JOB-REPO-01", status="COMPLETED", total_documents=2, auto_clear_count=2
    )
    await async_session.commit()
    assert updated.status == "COMPLETED"
    assert updated.auto_clear_count == 2

    jobs = await job_repo.list_jobs(async_session)
    assert len(jobs) == 1

@pytest.mark.anyio
async def test_document_and_evidence_repos(async_session):
    await job_repo.create_job(async_session, "JOB-02", "/path", status="RUNNING")
    doc = await document_repo.create_document(
        async_session, document_id="DOC-99", job_id="JOB-02", filename="test.pdf", sha256="hash99", decision="AUTO_CLEAR"
    )
    ev = await evidence_repo.create_evidence(
        async_session, evidence_id="EV-99", document_id="DOC-99", page_num=1, evidence_type="AOI_CROPPED_IMAGE", description="Sample crop"
    )
    await async_session.commit()

    retrieved_doc = await document_repo.get_document(async_session, "DOC-99")
    assert retrieved_doc is not None
    assert retrieved_doc.decision == "AUTO_CLEAR"

    evs = await evidence_repo.list_by_document(async_session, "DOC-99")
    assert len(evs) == 1
    assert evs[0].evidence_type == "AOI_CROPPED_IMAGE"

@pytest.mark.anyio
async def test_disposition_repo(async_session):
    await job_repo.create_job(async_session, "JOB-03", "/path", status="RUNNING")
    await document_repo.create_document(
        async_session, document_id="DOC-100", job_id="JOB-03", filename="test.pdf", sha256="hash100", decision="HUMAN_REVIEW"
    )
    disp = await disposition_repo.save_disposition(
        async_session, document_id="DOC-100", action="CONFIRM_WARNING", reviewer_id="USER-QA", comment="Confirmed gas line"
    )
    await async_session.commit()

    disp_list = await disposition_repo.list_by_document(async_session, "DOC-100")
    assert len(disp_list) == 1
    assert disp_list[0].action == "CONFIRM_WARNING"
    assert disp_list[0].reviewer_id == "USER-QA"
