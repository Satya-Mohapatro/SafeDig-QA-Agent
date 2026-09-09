from datetime import datetime
from typing import Optional, Dict, Any, List
from src.domain.enums import Decision, HumanDispositionAction
from src.domain.audit import DecisionRecord
from src.domain.policy import PolicyResult
from src.config.logging import logger

class HumanDispositionService:
    @staticmethod
    def apply_disposition(
        decision_record: DecisionRecord,
        action: HumanDispositionAction,
        reviewer_id: str,
        reviewer_comment: str
    ) -> DecisionRecord:
        logger.info(f"Applying human disposition {action.value} by {reviewer_id} for doc {decision_record.document_id}")
        
        decision_record.human_disposition = action
        decision_record.reviewer_comment = f"[{reviewer_id}] {reviewer_comment}"
        decision_record.timestamp = datetime.utcnow().isoformat()
        
        if action == HumanDispositionAction.CONFIRM_WARNING:
            # Human confirms warning condition exists
            decision_record.decision = Decision.HUMAN_REVIEW # Retains validated warning record
            decision_record.reason = f"Human Reviewer ({reviewer_id}) confirmed warning: {reviewer_comment}"
            
        elif action == HumanDispositionAction.REJECT_WARNING:
            # Human confirms upstream claim was a false alarm -> Release permitted
            decision_record.decision = Decision.AUTO_CLEAR
            decision_record.reason = f"Human Reviewer ({reviewer_id}) rejected false alarm: {reviewer_comment}"
            
        elif action == HumanDispositionAction.BLOCK:
            decision_record.decision = Decision.BLOCKED
            decision_record.reason = f"Human Reviewer ({reviewer_id}) blocked release: {reviewer_comment}"
            
        elif action == HumanDispositionAction.REQUEST_SECOND_REVIEW:
            decision_record.decision = Decision.HUMAN_REVIEW
            decision_record.reason = f"Escalated for senior review by {reviewer_id}: {reviewer_comment}"
            
        return decision_record

human_disposition_service = HumanDispositionService()
