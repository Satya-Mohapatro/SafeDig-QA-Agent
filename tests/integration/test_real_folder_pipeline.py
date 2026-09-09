import os
import pytest
from src.pipeline import run_map_qa_pipeline
from src.domain.enums import Decision
from tests.conftest import PROJECT_ROOT, DATA_DIR, SAMPLE_FOLDER_244414, SAMPLE_NGED_PDF

SAMPLE_FOLDER = str(SAMPLE_FOLDER_244414)

def test_full_pipeline_on_real_sample_folder():
    assert os.path.exists(SAMPLE_FOLDER)
    
    pipeline_out = run_map_qa_pipeline(SAMPLE_FOLDER, job_id="TEST-JOB-244414")
    
    assert pipeline_out["job_id"] == "TEST-JOB-244414"
    assert pipeline_out["manifest"]["total_files"] == 15
    assert pipeline_out["validation_report"]["is_valid"] is True
    assert pipeline_out["accounting_report"]["total_rows"] >= 50
    
    results = pipeline_out["results"]
    assert len(results) >= 50
    
    # Verify that all documents have deterministic decisions
    decisions = [r["decision"] for r in results]
    assert Decision.AUTO_CLEAR.value in decisions
    
    # Verify that report files were written
    reports = pipeline_out["reports"]
    assert os.path.exists(reports["job_report_path"])
    assert os.path.exists(reports["document_results_path"])
