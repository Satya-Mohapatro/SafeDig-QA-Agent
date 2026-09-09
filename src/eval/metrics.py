from typing import List, Dict
from src.eval.models import CaseEvaluationResult, EvaluationMetricResult

class EvaluationMetricsCalculator:
    @staticmethod
    def calculate(case_results: List[CaseEvaluationResult]) -> EvaluationMetricResult:
        total = len(case_results)
        if total == 0:
            return EvaluationMetricResult(
                total_cases=0,
                decision_accuracy=0.0,
                outcome_accuracy=0.0,
                precision=0.0,
                recall=0.0,
                f1_score=0.0,
                escaped_hazard_count=0
            )

        dec_matches = sum(1 for c in case_results if c.is_decision_match)
        out_matches = sum(1 for c in case_results if c.is_outcome_match)
        escaped_hazards = sum(1 for c in case_results if c.is_escaped_hazard)

        # Binary Safety Metrics (Hazards needing action: HUMAN_REVIEW or BLOCKED vs AUTO_CLEAR)
        tp = sum(1 for c in case_results if c.expected_decision in ["HUMAN_REVIEW", "BLOCKED"] and c.actual_decision in ["HUMAN_REVIEW", "BLOCKED"])
        fp = sum(1 for c in case_results if c.expected_decision == "AUTO_CLEAR" and c.actual_decision in ["HUMAN_REVIEW", "BLOCKED"])
        fn = sum(1 for c in case_results if c.expected_decision in ["HUMAN_REVIEW", "BLOCKED"] and c.actual_decision == "AUTO_CLEAR")
        tn = sum(1 for c in case_results if c.expected_decision == "AUTO_CLEAR" and c.actual_decision == "AUTO_CLEAR")

        precision = (tp / (tp + fp)) if (tp + fp) > 0 else 1.0
        recall = (tp / (tp + fn)) if (tp + fn) > 0 else 1.0
        f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0

        # Confusion Matrices
        dec_matrix: Dict[str, Dict[str, int]] = {}
        for c in case_results:
            exp, act = c.expected_decision, c.actual_decision
            if exp not in dec_matrix:
                dec_matrix[exp] = {}
            dec_matrix[exp][act] = dec_matrix[exp].get(act, 0) + 1

        out_matrix: Dict[str, Dict[str, int]] = {}
        for c in case_results:
            exp, act = c.expected_outcome, c.actual_outcome
            if exp not in out_matrix:
                out_matrix[exp] = {}
            out_matrix[exp][act] = out_matrix[exp].get(act, 0) + 1

        # Per Provider Accuracy
        providers: Dict[str, List[bool]] = {}
        for c in case_results:
            providers.setdefault(c.utility_name, []).append(c.is_decision_match)
        provider_acc = {p: round(sum(vals) / len(vals) * 100, 1) for p, vals in providers.items()}

        return EvaluationMetricResult(
            total_cases=total,
            decision_accuracy=round((dec_matches / total) * 100, 1),
            outcome_accuracy=round((out_matches / total) * 100, 1),
            precision=round(precision * 100, 1),
            recall=round(recall * 100, 1),
            f1_score=round(f1 * 100, 1),
            escaped_hazard_count=escaped_hazards,
            decision_confusion_matrix=dec_matrix,
            outcome_confusion_matrix=out_matrix,
            provider_accuracy=provider_acc
        )

metrics_calculator = EvaluationMetricsCalculator()
