import pytest
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from src.db.models import Base
from src.db.persistence import PersistenceService
from src.db.repositories import job_repo, document_repo, audit_repo

@pytest.fixture
async def async_db():
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
async def test_full_pipeline_persistence_and_queries(async_db):
    service = PersistenceService()
    job_id = "JOB-INTEGRATION-01"
    root_dir = "d:/Safedig_AG/Data/Sample1"

    doc_results = [
        {
            "document_id": "DOC-INT-1",
            "filename": "map1.pdf",
            "sha256": "hash123",
            "provider": "Cadent Gas",
            "utility_type": "GAS",
            "decision": "AUTO_CLEAR",
            "reason": "Clean vector map within AOI",
            "reconciliation_outcome": "CONFIRMED_CLEAN",
            "evidence_items": [
                {
                    "evidence_id": "EV-INT-1",
                    "page_num": 1,
                    "evidence_type": "AOI_CROPPED_IMAGE",
                    "description": "AOI clean area crop",
                }
            ],
            "reconciliation": {
                "reconciliation_id": "REC-INT-1",
                "outcome": "CONFIRMED_CLEAN",
                "explanation": "No assets intersecting AOI",
            },
            "policy_result": {
                "decision": "AUTO_CLEAR",
                "reason": "Clean map passed all 17 gates",
            },
        },
        {
            "document_id": "DOC-INT-2",
            "filename": "map2.pdf",
            "sha256": "hash456",
            "provider": "UK Power Networks",
            "utility_type": "ELECTRICITY",
            "decision": "HUMAN_REVIEW",
            "reason": "Warning detected near boundary",
            "reconciliation_outcome": "MATCH",
            "evidence_items": [],
        }
    ]

    # 1. Persist Job Result
    await service.persist_job_result(
        session=async_db,
        job_id=job_id,
        root_dir=root_dir,
        document_results=doc_results,
        duration_sec=1.45,
    )

    # 2. Query summary
    summary = await service.load_job_summary(async_db, job_id)
    assert summary is not None
    assert summary["job_id"] == job_id
    assert summary["total_documents"] == 2
    assert summary["auto_clear_count"] == 1
    assert summary["human_review_count"] == 1
    assert len(summary["documents"]) == 2

    # 3. Query audit trail
    trail = await service.load_audit_trail(async_db, job_id)
    assert len(trail) >= 3  # 1 for JOB_COMPLETED, 2 for DOCUMENT_DECISION
    actions = [t["action"] for t in trail]
    assert "JOB_COMPLETED" in actions
    assert "DOCUMENT_DECISION" in actions

    # 4. Apply Human Disposition
    await service.persist_human_disposition(
        session=async_db,
        job_id=job_id,
        document_id="DOC-INT-2",
        action="CONFIRM_WARNING",
        reviewer_id="QA-ENGINEER-1",
        comment="Verified cable presence near work zone",
    )

    # Verify audit trail appended
    updated_trail = await service.load_audit_trail(async_db, job_id)
    assert len(updated_trail) == len(trail) + 1
    assert updated_trail[-1]["action"] == "HUMAN_DISPOSITION"
    assert updated_trail[-1]["actor"] == "HUMAN"
