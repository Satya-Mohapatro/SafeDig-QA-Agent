"""PersistenceService — Bridge between Pydantic domain models and ORM records.

Converts workflow results into database records and provides query methods
for the API layer. Falls back gracefully if the database is unavailable.
"""
import json
import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime


from sqlalchemy.ext.asyncio import AsyncSession

from src.db.repositories import (
    job_repo, document_repo, evidence_repo,
    reconciliation_repo, policy_repo,
    audit_repo, disposition_repo,
)
from src.config.logging import logger


class PersistenceService:
    """Converts pipeline results to DB records and provides query interface."""

    async def persist_job_result(
        self,
        session: AsyncSession,
        job_id: str,
        root_dir: str,
        document_results: List[Dict[str, Any]],
        duration_sec: Optional[float] = None,
        error_message: Optional[str] = None,
    ) -> None:
        """Persist a complete LangGraph workflow result to the database.

        Args:
            session: Active async DB session.
            job_id: Unique job identifier.
            root_dir: Source folder path.
            document_results: List of per-document result dicts from the workflow.
            duration_sec: Total processing time in seconds.
            error_message: Error message if the job failed.
        """
        try:
            # Tally decision counts
            auto_clear = sum(1 for d in document_results if d.get("decision") == "AUTO_CLEAR")
            human_review = sum(1 for d in document_results if d.get("decision") == "HUMAN_REVIEW")
            blocked = sum(1 for d in document_results if d.get("decision") == "BLOCKED")

            status = "FAILED" if error_message else "COMPLETED"

            # Create or update job record
            existing_job = await job_repo.get_job(session, job_id)
            if existing_job:
                await job_repo.update_job_status(
                    session, job_id, status=status,
                    completed_at=datetime.utcnow(),
                    duration_sec=duration_sec,
                    error_message=error_message,
                    total_documents=len(document_results),
                    auto_clear_count=auto_clear,
                    human_review_count=human_review,
                    blocked_count=blocked,
                )
            else:
                job = await job_repo.create_job(session, job_id, root_dir, status=status)
                job.completed_at = datetime.utcnow()
                job.duration_sec = duration_sec
                job.error_message = error_message
                job.total_documents = len(document_results)
                job.auto_clear_count = auto_clear
                job.human_review_count = human_review
                job.blocked_count = blocked

            # Audit: job started
            await audit_repo.append_log(
                session, job_id=job_id, action="JOB_COMPLETED",
                actor="SYSTEM",
                detail={"total_documents": len(document_results),
                        "auto_clear": auto_clear,
                        "human_review": human_review,
                        "blocked": blocked,
                        "duration_sec": duration_sec}
            )

            # Persist each document result
            for doc_result in document_results:
                doc_id = doc_result.get("document_id") or doc_result.get("index_record_id") or f"DOC-{uuid.uuid4().hex[:8]}"
                provider = doc_result.get("provider") or doc_result.get("utility_name")
                
                await document_repo.create_document(
                    session,
                    document_id=doc_id,
                    job_id=job_id,
                    filename=doc_result.get("filename", "N/A"),
                    sha256=doc_result.get("sha256", ""),
                    provider=provider,
                    utility_type=doc_result.get("utility_type"),
                    modality=doc_result.get("modality", "VECTOR"),
                    page_count=doc_result.get("page_count", 1),
                    decision=doc_result.get("decision"),
                    decision_reason=doc_result.get("reason"),
                    reconciliation_outcome=doc_result.get("reconciliation_outcome"),
                )


                # Persist evidence items
                evidence_items = doc_result.get("evidence_items", [])
                for ev in evidence_items:
                    await evidence_repo.create_evidence(
                        session,
                        evidence_id=ev.get("evidence_id", f"E-{doc_id}"),
                        document_id=doc_id,
                        page_num=ev.get("page_num", 1),
                        evidence_type=ev.get("evidence_type", "UNKNOWN"),
                        description=ev.get("description", ""),
                        data=ev.get("data"),
                        crop_image_path=ev.get("crop_image_path"),
                    )

                # Persist reconciliation result
                recon = doc_result.get("reconciliation")
                if recon:
                    await reconciliation_repo.save_result(
                        session,
                        reconciliation_id=recon.get("reconciliation_id", f"REC-{doc_id}"),
                        document_id=doc_id,
                        outcome=recon.get("outcome", "UNCERTAIN"),
                        severity=recon.get("severity", "UNKNOWN"),
                        explanation=recon.get("explanation", ""),
                        claimed_warning=recon.get("claimed_warning"),
                        detected_candidates=recon.get("detected_candidates"),
                        evidence_ids=recon.get("evidence_ids"),
                    )

                # Persist policy result
                policy = doc_result.get("policy_result")
                if policy:
                    await policy_repo.save_result(
                        session,
                        document_id=doc_id,
                        decision=policy.get("decision", "BLOCKED"),
                        reason=policy.get("reason", ""),
                        gates=policy.get("gates"),
                        reconciliation_id=policy.get("reconciliation_id"),
                        evidence_package_id=policy.get("evidence_package_id"),
                        safe_mode_applied=policy.get("safe_mode_applied", False),
                    )

                # Audit: document decision
                await audit_repo.append_log(
                    session, job_id=job_id, action="DOCUMENT_DECISION",
                    actor="SYSTEM", document_id=doc_id,
                    detail={"decision": doc_result.get("decision"),
                            "reason": doc_result.get("reason"),
                            "filename": doc_result.get("filename")}
                )

            await session.commit()
            logger.info(f"[DB] Persisted job {job_id} with {len(document_results)} documents to database.")

        except Exception as e:
            await session.rollback()
            logger.error(f"[DB] Failed to persist job {job_id}: {e}")
            # Do NOT re-raise — persistence failure must not break the pipeline
            # The system must operate correctly even if DB is unavailable

    async def persist_human_disposition(
        self,
        session: AsyncSession,
        job_id: str,
        document_id: str,
        action: str,
        reviewer_id: str = "ANONYMOUS",
        comment: Optional[str] = None,
    ) -> None:
        """Save a human reviewer's disposition and append audit log."""
        try:
            await disposition_repo.save_disposition(
                session, document_id=document_id,
                action=action, reviewer_id=reviewer_id, comment=comment,
            )

            await audit_repo.append_log(
                session, job_id=job_id, action="HUMAN_DISPOSITION",
                actor="HUMAN", document_id=document_id,
                detail={"disposition_action": action,
                        "reviewer_id": reviewer_id,
                        "comment": comment}
            )

            await session.commit()
            logger.info(f"[DB] Saved human disposition for {document_id}: {action}")

        except Exception as e:
            await session.rollback()
            logger.error(f"[DB] Failed to persist disposition for {document_id}: {e}")

    async def load_job_summary(
        self, session: AsyncSession, job_id: str
    ) -> Optional[Dict[str, Any]]:
        """Load a job summary with document list from the database."""
        job = await job_repo.get_job(session, job_id)
        if not job:
            return None
        
        documents = await document_repo.list_by_job(session, job_id)
        
        return {
            "job_id": job.job_id,
            "root_dir": job.root_dir,
            "status": job.status,
            "created_at": job.created_at.isoformat() if job.created_at else None,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            "duration_sec": job.duration_sec,
            "total_documents": job.total_documents,
            "auto_clear_count": job.auto_clear_count,
            "human_review_count": job.human_review_count,
            "blocked_count": job.blocked_count,
            "error_message": job.error_message,
            "documents": [
                {
                    "document_id": d.document_id,
                    "filename": d.filename,
                    "provider": d.provider,
                    "utility_type": d.utility_type,
                    "decision": d.decision,
                    "decision_reason": d.decision_reason,
                    "reconciliation_outcome": d.reconciliation_outcome,
                }
                for d in documents
            ],
        }

    async def load_audit_trail(
        self, session: AsyncSession, job_id: str
    ) -> List[Dict[str, Any]]:
        """Load the immutable audit trail for a job."""
        logs = await audit_repo.list_by_job(session, job_id)
        return [
            {
                "id": log.id,
                "job_id": log.job_id,
                "document_id": log.document_id,
                "action": log.action,
                "actor": log.actor,
                "detail": json.loads(log.detail_json) if log.detail_json else None,
                "timestamp": log.timestamp.isoformat() if log.timestamp else None,
            }
            for log in logs
        ]


# Singleton
persistence_service = PersistenceService()
