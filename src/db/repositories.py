"""Async repository classes for database CRUD operations.

Each repository method takes an AsyncSession for transaction control.
All methods are async and use SQLAlchemy 2.0 select() style.
"""
import json
from typing import List, Optional
from datetime import datetime

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import (
    JobRecord, DocumentRecord, EvidenceItemRecord,
    ReconciliationRecord, PolicyResultRecord,
    AuditLogRecord, HumanDispositionRecord,
)
from src.config.logging import logger


class JobRepository:
    """CRUD operations for the jobs table."""

    async def create_job(
        self, session: AsyncSession, job_id: str, root_dir: str,
        status: str = "QUEUED"
    ) -> JobRecord:
        record = JobRecord(
            job_id=job_id,
            root_dir=root_dir,
            status=status,
        )
        session.add(record)
        await session.flush()
        logger.info(f"[DB] Created job record: {job_id}")
        return record

    async def get_job(self, session: AsyncSession, job_id: str) -> Optional[JobRecord]:
        result = await session.execute(
            select(JobRecord).where(JobRecord.job_id == job_id)
        )
        return result.scalar_one_or_none()

    async def update_job_status(
        self, session: AsyncSession, job_id: str, status: str,
        completed_at: Optional[datetime] = None,
        duration_sec: Optional[float] = None,
        error_message: Optional[str] = None,
        total_documents: int = 0,
        auto_clear_count: int = 0,
        human_review_count: int = 0,
        blocked_count: int = 0,
    ) -> Optional[JobRecord]:
        job = await self.get_job(session, job_id)
        if not job:
            return None
        job.status = status
        if completed_at:
            job.completed_at = completed_at
        if duration_sec is not None:
            job.duration_sec = duration_sec
        if error_message:
            job.error_message = error_message
        job.total_documents = total_documents
        job.auto_clear_count = auto_clear_count
        job.human_review_count = human_review_count
        job.blocked_count = blocked_count
        await session.flush()
        return job

    async def list_jobs(
        self, session: AsyncSession,
        status_filter: Optional[str] = None,
        limit: int = 100, offset: int = 0
    ) -> List[JobRecord]:
        stmt = select(JobRecord).order_by(JobRecord.created_at.desc())
        if status_filter:
            stmt = stmt.where(JobRecord.status == status_filter)
        stmt = stmt.limit(limit).offset(offset)
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def count_jobs(self, session: AsyncSession, status_filter: Optional[str] = None) -> int:
        stmt = select(func.count()).select_from(JobRecord)
        if status_filter:
            stmt = stmt.where(JobRecord.status == status_filter)
        result = await session.execute(stmt)
        return result.scalar_one()


class DocumentRepository:
    """CRUD operations for the documents table."""

    async def create_document(
        self, session: AsyncSession,
        document_id: str, job_id: str, filename: str, sha256: str,
        provider: Optional[str] = None, utility_type: Optional[str] = None,
        modality: str = "VECTOR", page_count: int = 1,
        decision: Optional[str] = None, decision_reason: Optional[str] = None,
        reconciliation_outcome: Optional[str] = None,
    ) -> DocumentRecord:
        existing = await self.get_document(session, document_id)
        if existing:
            existing.job_id = job_id
            existing.filename = filename
            existing.sha256 = sha256
            existing.provider = provider
            existing.utility_type = utility_type
            existing.modality = modality
            existing.page_count = page_count
            existing.decision = decision
            existing.decision_reason = decision_reason
            existing.reconciliation_outcome = reconciliation_outcome
            await session.flush()
            return existing

        record = DocumentRecord(
            document_id=document_id,
            job_id=job_id,
            filename=filename,
            sha256=sha256,
            provider=provider,
            utility_type=utility_type,
            modality=modality,
            page_count=page_count,
            decision=decision,
            decision_reason=decision_reason,
            reconciliation_outcome=reconciliation_outcome,
        )
        session.add(record)
        await session.flush()
        return record

    async def get_document(self, session: AsyncSession, document_id: str) -> Optional[DocumentRecord]:
        result = await session.execute(
            select(DocumentRecord).where(DocumentRecord.document_id == document_id)
        )
        return result.scalar_one_or_none()

    async def update_decision(
        self, session: AsyncSession, document_id: str,
        decision: str, reason: str
    ) -> Optional[DocumentRecord]:
        doc = await self.get_document(session, document_id)
        if not doc:
            return None
        doc.decision = decision
        doc.decision_reason = reason
        await session.flush()
        return doc

    async def list_by_job(self, session: AsyncSession, job_id: str) -> List[DocumentRecord]:
        result = await session.execute(
            select(DocumentRecord)
            .where(DocumentRecord.job_id == job_id)
            .order_by(DocumentRecord.filename)
        )
        return list(result.scalars().all())

    async def list_pending_review(self, session: AsyncSession, limit: int = 100) -> List[DocumentRecord]:
        result = await session.execute(
            select(DocumentRecord)
            .where(DocumentRecord.decision == "HUMAN_REVIEW")
            .order_by(DocumentRecord.document_id)
            .limit(limit)
        )
        return list(result.scalars().all())


class EvidenceRepository:
    """CRUD operations for the evidence_items table."""

    async def create_evidence(
        self, session: AsyncSession,
        evidence_id: str, document_id: str, page_num: int,
        evidence_type: str, description: str,
        data: Optional[dict] = None,
        crop_image_path: Optional[str] = None,
    ) -> EvidenceItemRecord:
        result = await session.execute(
            select(EvidenceItemRecord).where(EvidenceItemRecord.evidence_id == evidence_id)
        )
        existing = result.scalar_one_or_none()
        if existing:
            existing.document_id = document_id
            existing.page_num = page_num
            existing.evidence_type = evidence_type
            existing.description = description
            existing.data_json = json.dumps(data) if data else None
            existing.crop_image_path = crop_image_path
            await session.flush()
            return existing

        record = EvidenceItemRecord(
            evidence_id=evidence_id,
            document_id=document_id,
            page_num=page_num,
            evidence_type=evidence_type,
            description=description,
            data_json=json.dumps(data) if data else None,
            crop_image_path=crop_image_path,
        )
        session.add(record)
        await session.flush()
        return record


    async def list_by_document(self, session: AsyncSession, document_id: str) -> List[EvidenceItemRecord]:
        result = await session.execute(
            select(EvidenceItemRecord)
            .where(EvidenceItemRecord.document_id == document_id)
            .order_by(EvidenceItemRecord.evidence_id)
        )
        return list(result.scalars().all())


class ReconciliationRepository:
    """CRUD operations for the reconciliations table."""

    async def save_result(
        self, session: AsyncSession,
        reconciliation_id: str, document_id: str,
        outcome: str, severity: str, explanation: str,
        claimed_warning: Optional[dict] = None,
        detected_candidates: Optional[list] = None,
        evidence_ids: Optional[list] = None,
    ) -> ReconciliationRecord:
        record = ReconciliationRecord(
            reconciliation_id=reconciliation_id,
            document_id=document_id,
            outcome=outcome,
            severity=severity,
            explanation=explanation,
            claimed_warning_json=json.dumps(claimed_warning) if claimed_warning else None,
            detected_candidates_json=json.dumps(detected_candidates) if detected_candidates else None,
            evidence_ids_json=json.dumps(evidence_ids) if evidence_ids else None,
        )
        session.add(record)
        await session.flush()
        return record

    async def list_by_document(self, session: AsyncSession, document_id: str) -> List[ReconciliationRecord]:
        result = await session.execute(
            select(ReconciliationRecord)
            .where(ReconciliationRecord.document_id == document_id)
        )
        return list(result.scalars().all())


class PolicyRepository:
    """CRUD operations for the policy_results table."""

    async def save_result(
        self, session: AsyncSession,
        document_id: str, decision: str, reason: str,
        gates: Optional[dict] = None,
        reconciliation_id: Optional[str] = None,
        evidence_package_id: Optional[str] = None,
        safe_mode_applied: bool = False,
    ) -> PolicyResultRecord:
        record = PolicyResultRecord(
            document_id=document_id,
            decision=decision,
            reason=reason,
            gates_json=json.dumps(gates) if gates else None,
            reconciliation_id=reconciliation_id,
            evidence_package_id=evidence_package_id,
            safe_mode_applied=safe_mode_applied,
        )
        session.add(record)
        await session.flush()
        return record

    async def get_by_document(self, session: AsyncSession, document_id: str) -> Optional[PolicyResultRecord]:
        result = await session.execute(
            select(PolicyResultRecord)
            .where(PolicyResultRecord.document_id == document_id)
            .order_by(PolicyResultRecord.created_at.desc())
        )
        return result.scalars().first()


class AuditRepository:
    """Append-only operations for the immutable audit_logs table.
    
    Only INSERT is allowed. UPDATE and DELETE are blocked by ORM event listeners.
    """

    async def append_log(
        self, session: AsyncSession,
        job_id: str, action: str,
        actor: str = "SYSTEM",
        document_id: Optional[str] = None,
        detail: Optional[dict] = None,
    ) -> AuditLogRecord:
        record = AuditLogRecord(
            job_id=job_id,
            document_id=document_id,
            action=action,
            actor=actor,
            detail_json=json.dumps(detail) if detail else None,
        )
        session.add(record)
        await session.flush()
        return record

    async def list_by_job(self, session: AsyncSession, job_id: str) -> List[AuditLogRecord]:
        result = await session.execute(
            select(AuditLogRecord)
            .where(AuditLogRecord.job_id == job_id)
            .order_by(AuditLogRecord.timestamp.asc())
        )
        return list(result.scalars().all())

    async def list_by_document(self, session: AsyncSession, document_id: str) -> List[AuditLogRecord]:
        result = await session.execute(
            select(AuditLogRecord)
            .where(AuditLogRecord.document_id == document_id)
            .order_by(AuditLogRecord.timestamp.asc())
        )
        return list(result.scalars().all())


class DispositionRepository:
    """CRUD operations for the human_dispositions table."""

    async def save_disposition(
        self, session: AsyncSession,
        document_id: str, action: str,
        reviewer_id: str = "ANONYMOUS",
        comment: Optional[str] = None,
    ) -> HumanDispositionRecord:
        record = HumanDispositionRecord(
            document_id=document_id,
            action=action,
            reviewer_id=reviewer_id,
            comment=comment,
        )
        session.add(record)
        await session.flush()
        return record

    async def list_by_document(self, session: AsyncSession, document_id: str) -> List[HumanDispositionRecord]:
        result = await session.execute(
            select(HumanDispositionRecord)
            .where(HumanDispositionRecord.document_id == document_id)
            .order_by(HumanDispositionRecord.timestamp.desc())
        )
        return list(result.scalars().all())


# Singleton instances
job_repo = JobRepository()
document_repo = DocumentRepository()
evidence_repo = EvidenceRepository()
reconciliation_repo = ReconciliationRepository()
policy_repo = PolicyRepository()
audit_repo = AuditRepository()
disposition_repo = DispositionRepository()
