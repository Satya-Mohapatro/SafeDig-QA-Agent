import pytest
import httpx
from src.api.app import app
from tests.conftest import PROJECT_ROOT, DATA_DIR, SAMPLE_FOLDER_244414, SAMPLE_NGED_PDF

SAMPLE_FOLDER = str(SAMPLE_FOLDER_244414)

@pytest.mark.anyio
async def test_api_e2e_full_workflow():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        # 1. Submit Job
        submit_resp = await client.post("/api/v1/jobs/submit", json={
            "root_dir": SAMPLE_FOLDER,
            "job_id": "JOB-API-E2E-244414"
        })
        assert submit_resp.status_code == 200
        submit_data = submit_resp.json()
        assert submit_data["job_id"] == "JOB-API-E2E-244414"
        assert submit_data["total_documents_processed"] == 69
        assert submit_data["status"] == "COMPLETED"
        
        # 2. Query Status
        status_resp = await client.get("/api/v1/jobs/JOB-API-E2E-244414")
        assert status_resp.status_code == 200
        status_data = status_resp.json()
        assert status_data["total_records"] == 69
        assert status_data["auto_clear_count"] >= 65
        
        # 3. Query QA Queue for Human Review items
        queue_resp = await client.get("/api/v1/qa/queue?job_id=JOB-API-E2E-244414")
        assert queue_resp.status_code == 200
        queue_data = queue_resp.json()
        assert queue_data["total_items"] >= 0
        
        # 4. If items exist in queue, fetch full review workspace payload
        if queue_data["total_items"] > 0:
            first_item = queue_data["items"][0]
            ws_resp = await client.get(f"/api/v1/qa/workspace/JOB-API-E2E-244414/{first_item['document_id']}")
            assert ws_resp.status_code == 200
            ws_data = ws_resp.json()
            assert ws_data["job_id"] == "JOB-API-E2E-244414"
            assert ws_data["document_id"] == first_item["document_id"]
            assert "gates" in ws_data
            assert "advisory" in ws_data
            
            # 5. Submit Human Disposition
            disp_resp = await client.post("/api/v1/qa/disposition", json={
                "job_id": "JOB-API-E2E-244414",
                "document_id": first_item["document_id"],
                "index_record_id": first_item["index_record_id"],
                "action": "CONFIRM_WARNING",
                "reviewer_id": "API_QA_LEAD",
                "reviewer_comment": "Confirmed high pressure gas line hazard."
            })
            assert disp_resp.status_code == 200
            disp_data = disp_resp.json()
            assert disp_data["action"] == "CONFIRM_WARNING"
