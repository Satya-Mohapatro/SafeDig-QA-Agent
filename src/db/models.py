"""SQLAlchemy ORM models for SafeDig database persistence.

Tables:
    - jobs: QA processing jobs
    - documents: Utility map documents within a job
    - evidence_items: Evidence artifacts (crops, vectors, OCR text)
    - reconciliations: 4-way reconciliation results
    - policy_results: 17-gate policy engine evaluations
    - audit_logs: Immutable, append-only audit trail
    - human_dispositions: Human reviewer decisions
"""
import json
from datetime import datetime
from typing import Optional, List

from sqlalchemy import (
    String, Integer, Float, Boolean, Text, DateTime, ForeignKey,
    Index, event
)
from sqlalchemy.orm import (
    DeclarativeBase, Mapped, mapped_column, relationship
)


class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass


class JobRecord(Base):
    __tablename__ = "jobs"

    job_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    root_dir: Mapped[str] = mapped_column(String(512), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="QUEUED")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    duration_sec: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    total_documents: Mapped[int] = mapped_column(Integer, default=0)
    auto_clear_count: Mapped[int] = mapped_column(Integer, default=0)
    human_review_count: Mapped[int] = mapped_column(Integer, default=0)
    blocked_count: Mapped[int] = mapped_column(Integer, default=0)

    # Relationships
    documents: Mapped[List["DocumentRecord"]] = relationship(
        back_populates="job", cascade="all, delete-orphan", lazy="selectin"
    )
    audit_logs: Mapped[List["AuditLogRecord"]] = relationship(
        back_populates="job", cascade="all, delete-orphan", lazy="selectin"
    )

    __table_args__ = (
        Index("ix_jobs_status", "status"),
        Index("ix_jobs_created_at", "created_at"),
    )


class DocumentRecord(Base):
    __tablename__ = "documents"

    document_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    job_id: Mapped[str] = mapped_column(String(128), ForeignKey("jobs.job_id"), nullable=False)
    filename: Mapped[str] = mapped_column(String(512), nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    provider: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    utility_type: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    modality: Mapped[str] = mapped_column(String(32), default="VECTOR")
    page_count: Mapped[int] = mapped_column(Integer, default=1)
    decision: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    decision_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reconciliation_outcome: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    # Relationships
    job: Mapped["JobRecord"] = relationship(back_populates="documents")
    evidence_items: Mapped[List["EvidenceItemRecord"]] = relationship(
        back_populates="document", cascade="all, delete-orphan", lazy="selectin"
    )
    reconciliations: Mapped[List["ReconciliationRecord"]] = relationship(
        back_populates="document", cascade="all, delete-orphan", lazy="selectin"
    )
    policy_results: Mapped[List["PolicyResultRecord"]] = relationship(
        back_populates="document", cascade="all, delete-orphan", lazy="selectin"
    )
    human_dispositions: Mapped[List["HumanDispositionRecord"]] = relationship(
        back_populates="document", cascade="all, delete-orphan", lazy="selectin"
    )

    __table_args__ = (
        Index("ix_documents_job_id", "job_id"),
        Index("ix_documents_decision", "decision"),
    )


class EvidenceItemRecord(Base):
    __tablename__ = "evidence_items"

    evidence_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    document_id: Mapped[str] = mapped_column(String(128), ForeignKey("documents.document_id"), nullable=False)
    page_num: Mapped[int] = mapped_column(Integer, nullable=False)
    evidence_type: Mapped[str] = mapped_column(String(64), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    data_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    crop_image_path: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    document: Mapped["DocumentRecord"] = relationship(back_populates="evidence_items")

    __table_args__ = (
        Index("ix_evidence_document_id", "document_id"),
    )


class ReconciliationRecord(Base):
    __tablename__ = "reconciliations"

    reconciliation_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    document_id: Mapped[str] = mapped_column(String(128), ForeignKey("documents.document_id"), nullable=False)
    outcome: Mapped[str] = mapped_column(String(64), nullable=False)
    severity: Mapped[str] = mapped_column(String(32), default="UNKNOWN")
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    claimed_warning_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    detected_candidates_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    evidence_ids_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    document: Mapped["DocumentRecord"] = relationship(back_populates="reconciliations")

    __table_args__ = (
        Index("ix_reconciliations_document_id", "document_id"),
        Index("ix_reconciliations_outcome", "outcome"),
    )


class PolicyResultRecord(Base):
    __tablename__ = "policy_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    document_id: Mapped[str] = mapped_column(String(128), ForeignKey("documents.document_id"), nullable=False)
    decision: Mapped[str] = mapped_column(String(32), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    gates_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reconciliation_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    evidence_package_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    safe_mode_applied: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    document: Mapped["DocumentRecord"] = relationship(back_populates="policy_results")

    __table_args__ = (
        Index("ix_policy_results_document_id", "document_id"),
    )


class AuditLogRecord(Base):
    """Immutable, append-only audit trail.
    
    No UPDATE or DELETE operations are permitted on this table.
    Event listeners enforce this constraint at the ORM level.
    """
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_id: Mapped[str] = mapped_column(String(128), ForeignKey("jobs.job_id"), nullable=False)
    document_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    action: Mapped[str] = mapped_column(String(128), nullable=False)
    actor: Mapped[str] = mapped_column(String(32), nullable=False, default="SYSTEM")
    detail_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    job: Mapped["JobRecord"] = relationship(back_populates="audit_logs")

    __table_args__ = (
        Index("ix_audit_logs_job_id", "job_id"),
        Index("ix_audit_logs_document_id", "document_id"),
        Index("ix_audit_logs_timestamp", "timestamp"),
    )


class HumanDispositionRecord(Base):
    __tablename__ = "human_dispositions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    document_id: Mapped[str] = mapped_column(String(128), ForeignKey("documents.document_id"), nullable=False)
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    reviewer_id: Mapped[str] = mapped_column(String(128), nullable=False, default="ANONYMOUS")
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    document: Mapped["DocumentRecord"] = relationship(back_populates="human_dispositions")

    __table_args__ = (
        Index("ix_human_dispositions_document_id", "document_id"),
    )


# ── Immutability enforcement for audit_logs ──────────────────────────────────

def _block_audit_update(mapper, connection, target):
    raise RuntimeError(
        "SECURITY VIOLATION: Audit log records are immutable. "
        "UPDATE operations are forbidden on the audit_logs table."
    )

def _block_audit_delete(mapper, connection, target):
    raise RuntimeError(
        "SECURITY VIOLATION: Audit log records are immutable. "
        "DELETE operations are forbidden on the audit_logs table."
    )

event.listen(AuditLogRecord, "before_update", _block_audit_update)
event.listen(AuditLogRecord, "before_delete", _block_audit_delete)
