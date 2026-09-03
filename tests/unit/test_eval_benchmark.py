import pytest
from src.eval.dataset import ground_truth_dataset
from src.eval.benchmark import benchmark_runner

def test_benchmark_runner_execution():
    # Run on subset of gold standard cases
    all_cases = ground_truth_dataset.get_gold_standard_cases()
    subset = all_cases[:4]  # 4 cases from 244414_201678
    
    report = benchmark_runner.run_benchmark(cases=subset)
    assert report.total_cases_evaluated == 4
    assert report.safety_compliance_passed is True
    assert report.metrics.escaped_hazard_count == 0
    assert report.metrics.decision_accuracy >= 75.0
    assert len(report.case_results) == 4
