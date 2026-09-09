from typing import List, Optional
from src.domain.warning import ClaimedWarning
from src.domain.detection import DetectedCandidate
from src.domain.reconciliation import ReconciliationResult
from src.domain.enums import ReconciliationOutcome, Severity
from src.config.logging import logger

def reconcile_warnings(
    document_id: str,
    claimed_warning: Optional[ClaimedWarning],
    detected_candidates: List[DetectedCandidate]
) -> ReconciliationResult:
    rec_id = f"REC-{document_id}"

    # Strictly filter for HIGH severity warnings per user requirement:
    # "I want warning only for High", "no medium status warning"
    high_candidates = [c for c in detected_candidates if c.severity == Severity.HIGH]
    has_detected = len(high_candidates) > 0

    has_claimed = False
    if claimed_warning is not None and bool(claimed_warning.raw_warning_text.strip()):
        raw_t = claimed_warning.raw_warning_text.lower().strip()
        is_clean_claim = any(neg in raw_t for neg in ["no gtc", "no plant", "not found", "no warning", "nil", "none", "clean"])
        if not is_clean_claim and claimed_warning.severity == Severity.HIGH:
            has_claimed = True

    # 1. Both claimed and detected
    if has_claimed and has_detected:
        return ReconciliationResult(
            reconciliation_id=rec_id,
            document_id=document_id,
            claimed_warning=claimed_warning,
            detected_candidates=high_candidates,
            outcome=ReconciliationOutcome.MATCH,
            severity=Severity.HIGH,
            explanation=f"Upstream claimed warning matches independent finding: {high_candidates[0].business_warning_text}",
            evidence_ids=[]
        )

    # 2. No upstream warning claimed, but independent scan found HIGH warning -> MISSED WARNING (Escalate!)
    elif not has_claimed and has_detected:
        logger.warning(f"MISSED WARNING on {document_id}: Upstream reported clean, but QA detected {len(high_candidates)} hazards.")
        return ReconciliationResult(
            reconciliation_id=rec_id,
            document_id=document_id,
            claimed_warning=claimed_warning,
            detected_candidates=high_candidates,
            outcome=ReconciliationOutcome.MISSED_WARNING,
            severity=Severity.HIGH,
            explanation=f"MISSED WARNING: Upstream reported clean, but independent analysis detected {high_candidates[0].business_warning_text}",
            evidence_ids=[]
        )

    # 3. Upstream claimed HIGH warning, but independent QA found no supporting evidence -> FALSE POSITIVE
    elif has_claimed and not has_detected:
        return ReconciliationResult(
            reconciliation_id=rec_id,
            document_id=document_id,
            claimed_warning=claimed_warning,
            detected_candidates=[],
            outcome=ReconciliationOutcome.POSSIBLE_FALSE_POSITIVE,
            severity=claimed_warning.severity if claimed_warning else Severity.HIGH,
            explanation=f"Upstream claimed warning '{claimed_warning.raw_warning_text}', but independent analysis found no intersecting assets.",
            evidence_ids=[]
        )

    # 4. Neither claimed nor detected -> CONFIRMED CLEAN (Automatic Pass)
    else:
        return ReconciliationResult(
            reconciliation_id=rec_id,
            document_id=document_id,
            claimed_warning=None,
            detected_candidates=[],
            outcome=ReconciliationOutcome.CONFIRMED_CLEAN,
            severity=Severity.LOW,
            explanation="Both upstream and independent validation confirmed no warning conditions present.",
            evidence_ids=[]
        )

