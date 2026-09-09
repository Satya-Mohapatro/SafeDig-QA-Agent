import pytest
import os
import json
import httpx
from src.api.app import app
from src.config.settings import settings

@pytest.mark.anyio
async def test_api_submit_disposition(tmp_path):
    job_id = "JOB-MOCK-DISP"
    job_dir = os.path.join(settings.output_dir, job_id)
    os.makedirs(job_dir, exist_ok=True)
    
    mock_results = [
        {
            "index_record_id": "IDX-001",
            "document_id": "DOC-FIL-0001",
            "filename": "map.pdf",
            "utility_name": "SGN",
            "utility_type": "Gas",
            "decision": "HUMAN_REVIEW",
            "reason": "Possible false positive claim"
        }
    ]
    mock_report = {
        "job_id": job_id,
        "overall_decision": "HUMAN_REVIEW",
        "generated_at": "2026-09-01T20:00:00",
        "summary": {"total_records": 1, "auto_clear": 0, "human_review": 1, "blocked": 0}
    }
    
    with open(os.path.join(job_dir, "document_results.json"), "w") as f:
        json.dump(mock_results, f)
    with open(os.path.join(job_dir, "job_report.json"), "w") as f:
        json.dump(mock_report, f)
        
    req_payload = {
        "job_id": job_id,
        "document_id": "DOC-FIL-0001",
        "index_record_id": "IDX-001",
        "action": "REJECT_WARNING",
        "reviewer_id": "QA_ENGINEER_7",
        "reviewer_comment": "Verified map; asset lies outside buffer zone."
    }
    
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post("/api/v1/qa/disposition", json=req_payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["previous_decision"] == "HUMAN_REVIEW"
        assert data["new_decision"] == "AUTO_CLEAR"
        assert data["action"] == "REJECT_WARNING"
        assert data["reviewer_id"] == "QA_ENGINEER_7"
    
    with open(os.path.join(job_dir, "job_report.json"), "r") as f:
        updated_rep = json.load(f)
    assert updated_rep["overall_decision"] == "AUTO_CLEAR"
    assert updated_rep["summary"]["auto_clear"] == 1
    assert updated_rep["summary"]["human_review"] == 0
