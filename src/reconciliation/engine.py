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
    has_claimed = claimed_warning is not None and bool(claimed_warning.raw_warning_text.strip())
    has_detected = len(detected_candidates) > 0
    
    # 1. Both claimed and detected
    if has_claimed and has_detected:
        highest_sev = max([c.severity for c in detected_candidates], key=lambda s: 3 if s == Severity.HIGH else (2 if s == Severity.MEDIUM else 1))
        return ReconciliationResult(
            reconciliation_id=rec_id,
            document_id=document_id,
            claimed_warning=claimed_warning,
            detected_candidates=detected_candidates,
            outcome=ReconciliationOutcome.MATCH,
            severity=highest_sev,
            explanation=f"Upstream claimed warning matches independent finding: {detected_candidates[0].business_warning_text}",
            evidence_ids=[]
        )
        
    # 2. No upstream warning claimed, but independent scan found warning -> MISSED WARNING (Escalate!)
    elif not has_claimed and has_detected:
        highest_sev = max([c.severity for c in detected_candidates], key=lambda s: 3 if s == Severity.HIGH else (2 if s == Severity.MEDIUM else 1))
        logger.warning(f"MISSED WARNING on {document_id}: Upstream reported clean, but QA detected {len(detected_candidates)} hazards.")
        return ReconciliationResult(
            reconciliation_id=rec_id,
            document_id=document_id,
            claimed_warning=claimed_warning,
            detected_candidates=detected_candidates,
            outcome=ReconciliationOutcome.MISSED_WARNING,
            severity=highest_sev,
            explanation=f"MISSED WARNING: Upstream reported clean, but independent analysis detected {detected_candidates[0].business_warning_text}",
            evidence_ids=[]
        )
        
    # 3. Upstream claimed warning, but independent QA found no supporting evidence -> FALSE POSITIVE
    elif has_claimed and not has_detected:
        return ReconciliationResult(
            reconciliation_id=rec_id,
            document_id=document_id,
            claimed_warning=claimed_warning,
            detected_candidates=[],
            outcome=ReconciliationOutcome.POSSIBLE_FALSE_POSITIVE,
            severity=claimed_warning.severity if claimed_warning else Severity.MEDIUM,
            explanation=f"Upstream claimed warning '{claimed_warning.raw_warning_text}', but independent analysis found no intersecting assets.",
            evidence_ids=[]
        )
        
    # 4. Neither claimed nor detected -> CONFIRMED CLEAN
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
