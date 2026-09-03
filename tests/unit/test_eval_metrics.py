import pytest
from src.eval.models import CaseEvaluationResult
from src.eval.metrics import metrics_calculator

def test_metrics_calculator_perfect_score():
    results = [
        CaseEvaluationResult(
            case_id="C1", job_id="J1", document_id="D1", filename="map1.pdf",
            utility_name="WWU", expected_decision="HUMAN_REVIEW", actual_decision="HUMAN_REVIEW",
            expected_outcome="MISSED_WARNING", actual_outcome="MISSED_WARNING",
            is_decision_match=True, is_outcome_match=True, is_escaped_hazard=False, reason="OK"
        ),
        CaseEvaluationResult(
            case_id="C2", job_id="J1", document_id="D2", filename="map2.pdf",
            utility_name="BT", expected_decision="AUTO_CLEAR", actual_decision="AUTO_CLEAR",
            expected_outcome="CLEAN", actual_outcome="CLEAN",
            is_decision_match=True, is_outcome_match=True, is_escaped_hazard=False, reason="OK"
        )
    ]
    
    metrics = metrics_calculator.calculate(results)
    assert metrics.total_cases == 2
    assert metrics.decision_accuracy == 100.0
    assert metrics.outcome_accuracy == 100.0
    assert metrics.recall == 100.0
    assert metrics.precision == 100.0
    assert metrics.escaped_hazard_count == 0

def test_metrics_calculator_escaped_hazard_detection():
    results = [
        CaseEvaluationResult(
            case_id="C1", job_id="J1", document_id="D1", filename="map1.pdf",
            utility_name="WWU", expected_decision="HUMAN_REVIEW", actual_decision="AUTO_CLEAR",  # ESCAPED HAZARD!
            expected_outcome="MISSED_WARNING", actual_outcome="CLEAN",
            is_decision_match=False, is_outcome_match=False, is_escaped_hazard=True, reason="Missed"
        )
    ]
    
    metrics = metrics_calculator.calculate(results)
    assert metrics.escaped_hazard_count == 1
    assert metrics.recall == 0.0
