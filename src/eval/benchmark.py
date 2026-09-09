import os
import json
import uuid
from typing import List, Optional
from datetime import datetime
from src.eval.models import GroundTruthCase, CaseEvaluationResult, BenchmarkReport
from src.eval.dataset import ground_truth_dataset
from src.eval.metrics import metrics_calculator
from src.orchestration import map_qa_workflow, MapQAState
from src.config.settings import settings
from src.config.logging import logger

class BenchmarkRunner:
    def run_benchmark(self, cases: Optional[List[GroundTruthCase]] = None, output_dir: Optional[str] = None) -> BenchmarkReport:
        gt_cases = cases or ground_truth_dataset.get_gold_standard_cases()
        run_id = f"BENCH-{uuid.uuid4().hex[:8].upper()}"
        out_dir = output_dir or os.path.join(settings.output_dir, "benchmarks", run_id)
        os.makedirs(out_dir, exist_ok=True)
        
        logger.info(f"Starting Benchmark Run {run_id} on {len(gt_cases)} ground-truth cases...")
        case_results: List[CaseEvaluationResult] = []

        # Cache job results by root_dir to avoid running same folder multiple times
        job_cache = {}

        for case in gt_cases:
            if case.root_dir not in job_cache:
                job_id = f"BENCH-JOB-{os.path.basename(case.root_dir)}"
                state: MapQAState = {
                    "root_dir": case.root_dir,
                    "job_id": job_id,
                    "output_dir": os.path.join(out_dir, job_id)
                }
                final_state = map_qa_workflow.invoke(state)
                job_cache[case.root_dir] = final_state.get("document_results", [])

            doc_results = job_cache[case.root_dir]
            
            # Find matching document
            matched_doc = None
            for d in doc_results:
                if case.filename and d.get("filename") == case.filename:
                    matched_doc = d
                    break
                elif d.get("utility_name") == case.utility_name:
                    matched_doc = d
                    break

            actual_dec = matched_doc.get("decision", "BLOCKED") if matched_doc else "BLOCKED"
            actual_out = matched_doc.get("reconciliation_outcome", "CONFIRMED_CLEAN") if matched_doc else "CONFIRMED_CLEAN"
            doc_id = matched_doc.get("document_id", "MISSING_DOC") if matched_doc else "MISSING_DOC"
            fname = matched_doc.get("filename", case.filename or "N/A") if matched_doc else (case.filename or "N/A")

            is_dec_match = (actual_dec == case.expected_decision.value)
            is_out_match = (actual_out == case.expected_outcome.value)
            
            # Critical Safety Check: Escaped hazard happens if expected is HUMAN_REVIEW/BLOCKED but actual was AUTO_CLEAR
            is_escaped = (case.is_safety_critical and case.expected_decision in ["HUMAN_REVIEW", "BLOCKED"] and actual_dec == "AUTO_CLEAR")

            case_results.append(CaseEvaluationResult(
                case_id=case.case_id,
                job_id=case.job_id,
                document_id=doc_id,
                filename=fname,
                utility_name=case.utility_name,
                expected_decision=case.expected_decision.value,
                actual_decision=actual_dec,
                expected_outcome=case.expected_outcome.value,
                actual_outcome=actual_out,
                is_decision_match=is_dec_match,
                is_outcome_match=is_out_match,
                is_escaped_hazard=is_escaped,
                reason=matched_doc.get("reason", "Evaluated against ground truth.") if matched_doc else "Missing document."
            ))

        metrics = metrics_calculator.calculate(case_results)
        
        report = BenchmarkReport(
            run_id=run_id,
            timestamp=datetime.utcnow().isoformat(),
            engine_version=settings.engine_version,
            policy_version=settings.policy_version,
            total_cases_evaluated=len(gt_cases),
            safety_compliance_passed=(metrics.escaped_hazard_count == 0),
            metrics=metrics,
            case_results=case_results
        )

        # Save eval_report.json
        report_path = os.path.join(out_dir, "eval_report.json")
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report.model_dump(), f, indent=2)

        # Also save latest pointer
        latest_path = os.path.join(settings.output_dir, "benchmarks", "latest_eval_report.json")
        with open(latest_path, "w", encoding="utf-8") as f:
            json.dump(report.model_dump(), f, indent=2)

        logger.info(f"Benchmark Run {run_id} completed: Decision Accuracy {metrics.decision_accuracy}%, Recall {metrics.recall}%, Escaped Hazards: {metrics.escaped_hazard_count}")
        return report

benchmark_runner = BenchmarkRunner()
