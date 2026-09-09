import pytest
import os
from src.eval.dataset import ground_truth_dataset

def test_ground_truth_dataset_integrity():
    cases = ground_truth_dataset.get_gold_standard_cases()
    assert len(cases) >= 6
    
    for c in cases:
        assert c.case_id.startswith("GT-")
        assert os.path.exists(c.root_dir)
        assert c.utility_name
        assert c.expected_decision is not None
        assert c.expected_outcome is not None
