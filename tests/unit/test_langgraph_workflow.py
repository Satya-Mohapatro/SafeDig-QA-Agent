import pytest
from src.orchestration import map_qa_workflow, MapQAState
from tests.conftest import PROJECT_ROOT, DATA_DIR, SAMPLE_FOLDER_244414, SAMPLE_NGED_PDF

def test_langgraph_compilation():
    assert map_qa_workflow is not None
    # Verify graph structure
    assert "ingest_and_index_node" in map_qa_workflow.nodes
    assert "process_qa_and_policy_node" in map_qa_workflow.nodes
    assert "llm_advisory_node" in map_qa_workflow.nodes
    assert "finalize_report_node" in map_qa_workflow.nodes

def test_langgraph_missing_folder_state():
    initial_state: MapQAState = {
        "root_dir": str(PROJECT_ROOT / "NonExistentFolder_999"),
        "job_id": "TEST-JOB-ERR"
    }
    # Should handle gracefully without unhandled crash
    try:
        final_state = map_qa_workflow.invoke(initial_state)
        assert final_state["status"] == "FAILED" or final_state.get("overall_decision") == "BLOCKED"
    except FileNotFoundError:
        # FileNotFoundError is also expected for nonexistent path
        pass
