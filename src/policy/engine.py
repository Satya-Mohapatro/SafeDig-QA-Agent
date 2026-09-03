from typing import Dict, Optional
from src.domain.index_record import IndexRecord
from src.domain.document import Document
from src.domain.aoi import AOI
from src.domain.legend import LegendProfile
from src.domain.reconciliation import ReconciliationResult
from src.domain.evidence import EvidencePackage
from src.domain.policy import PolicyResult
from src.domain.enums import Decision, ReconciliationOutcome, DocumentResolutionStatus
from .gates import evaluate_all_17_gates
from src.config.settings import settings
from src.config.logging import logger

class PolicyEngine:
    @staticmethod
    def evaluate(
        index_record: IndexRecord,
        document: Optional[Document],
        legend_profile: Optional[LegendProfile],
        aoi: Optional[AOI],
        reconciliation: ReconciliationResult,
        evidence_pkg: Optional[EvidencePackage]
    ) -> PolicyResult:
        doc_id = document.document_id if document else index_record.index_record_id
        
        # ── Early-exit blocking conditions ───────────────────────────────────
        if not index_record.is_asset_present:
            return PolicyResult(
                document_id=doc_id,
                decision=Decision.AUTO_CLEAR,
                reason="Utility reported no assets in the enquiry area (Status='No').",
                gates={},
                safe_mode_applied=False
            )
        
        if document is None or document.is_corrupted:
            return PolicyResult(
                document_id=doc_id,
                decision=Decision.BLOCKED,
                reason="Mandatory map document missing or corrupted.",
                gates={},
                safe_mode_applied=False
            )
        
        if index_record.resolution_status == DocumentResolutionStatus.AMBIGUOUS:
            return PolicyResult(
                document_id=doc_id,
                decision=Decision.BLOCKED,
                reason="Document resolution ambiguous (multiple candidate maps found).",
                gates={},
                safe_mode_applied=False
            )
        
        # ── Ensure evidence package is never None when gates are evaluated ───
        if evidence_pkg is None:
            from src.domain.evidence import EvidencePackage
            evidence_pkg = EvidencePackage(
                package_id=f"PKG-{doc_id}-EMPTY",
                document_id=doc_id,
                items=[],
                is_complete=False,
                completeness_reasons=["Evidence package was not provided."]
            )
        
        # ── Evaluate all 17 policy gates ─────────────────────────────────────
        gates = evaluate_all_17_gates(
            index_record=index_record,
            document=document,
            legend_profile=legend_profile,
            aoi=aoi,
            reconciliation=reconciliation,
            evidence_pkg=evidence_pkg
        )
        
        all_passed = all(g.passed for g in gates.values())
        
        # ── Deterministic decision routing ───────────────────────────────────
        if reconciliation.outcome == ReconciliationOutcome.MISSED_WARNING:
            decision = Decision.HUMAN_REVIEW
            reason = f"MANDATORY HUMAN REVIEW: {reconciliation.explanation}"
        
        elif reconciliation.outcome == ReconciliationOutcome.POSSIBLE_FALSE_POSITIVE:
            decision = Decision.HUMAN_REVIEW
            reason = f"HUMAN REVIEW: {reconciliation.explanation}"
        
        elif (reconciliation.outcome == ReconciliationOutcome.MATCH
              and not gates["12_NO_UNRESOLVED_CRITICAL_WARNING"].passed):
            decision = Decision.HUMAN_REVIEW
            reason = "HUMAN REVIEW: Confirmed high-severity warning requires human authorization."
        
        elif not gates["07_LEGEND_RESOLVED"].passed or not gates["08_AOI_RESOLVED"].passed:
            decision = Decision.HUMAN_REVIEW
            reason = "HUMAN REVIEW: Required legend profile or AOI boundary could not be resolved safely."
        
        elif all_passed:
            decision = Decision.AUTO_CLEAR
            reason = "AUTO CLEAR: All 17 mandatory release gates passed and evidence is complete."
        
        else:
            failed = [g.gate_name for g in gates.values() if not g.passed]
            decision = Decision.HUMAN_REVIEW
            reason = f"HUMAN REVIEW: Mandatory release gates failed: {', '.join(failed)}"
        
        logger.info(f"Policy evaluated for {doc_id} -> {decision.value} ({reason})")
        return PolicyResult(
            document_id=doc_id,
            decision=decision,
            reason=reason,
            gates=gates,
            reconciliation_id=reconciliation.reconciliation_id,
            evidence_package_id=evidence_pkg.package_id,
            safe_mode_applied=settings.safe_mode
        )

policy_engine = PolicyEngine()
