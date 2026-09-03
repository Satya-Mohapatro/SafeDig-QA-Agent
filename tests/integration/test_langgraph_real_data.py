import pytest
import os
from src.orchestration import map_qa_workflow, MapQAState

SAMPLE_FOLDER = "d:/Safedig_AG/Data/244414_201678"

def test_langgraph_real_folder_execution():
    assert os.path.exists(SAMPLE_FOLDER)
    initial_state: MapQAState = {
        "root_dir": SAMPLE_FOLDER,
        "job_id": "TEST-LANGGRAPH-244414"
    }
    final_state = map_qa_workflow.invoke(initial_state)
    
    assert final_state["status"] == "COMPLETED"
    assert len(final_state["document_results"]) == 69
    assert "reports" in final_state
    assert os.path.exists(final_state["reports"]["job_report_path"])
    assert final_state["overall_decision"] in ["AUTO_CLEAR", "HUMAN_REVIEW", "BLOCKED"]
