import pytest
import httpx
from src.api.app import app

@pytest.mark.anyio
async def test_map_level_qa_visibility():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/v1/jobs")
        assert resp.status_code == 200
        jobs_data = resp.json()
        assert jobs_data["total_jobs"] > 0
        
        target_job = next((j for j in jobs_data["jobs"] if j["records"] == 69), jobs_data["jobs"][0])
        job_id = target_job["job_id"]
        total_recs = target_job["records"]
        
        # Query individual map results
        map_resp = await client.get(f"/api/v1/jobs/{job_id}/results")
        assert map_resp.status_code == 200
        maps = map_resp.json()
        assert isinstance(maps, list)
        assert len(maps) == total_recs
        
        # Verify map attributes and independent classification
        for m in maps:
            assert "index_record_id" in m
            assert "utility_name" in m
            assert "utility_type" in m
            assert "decision" in m
            assert m["decision"] in ["AUTO_CLEAR", "HUMAN_REVIEW", "BLOCKED"]
            assert "reason" in m
            
        # Verify aggregate counts match individual record sums
        ac_count = sum(1 for m in maps if m["decision"] == "AUTO_CLEAR")
        hr_count = sum(1 for m in maps if m["decision"] == "HUMAN_REVIEW")
        bl_count = sum(1 for m in maps if m["decision"] == "BLOCKED")
        assert ac_count == target_job["auto_clear"]
        assert hr_count == target_job["human_review"]
        assert bl_count == target_job["blocked"]

@pytest.mark.anyio
async def test_map_workspace_access_for_any_record():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/v1/jobs")
        jobs_data = resp.json()
        target_job = next((j for j in jobs_data["jobs"] if j["records"] == 69), jobs_data["jobs"][0])
        job_id = target_job["job_id"]
        
        map_resp = await client.get(f"/api/v1/jobs/{job_id}/results")
        maps = map_resp.json()
        
        first_doc_id = maps[0].get("document_id") or maps[0].get("index_record_id")
        ws_resp = await client.get(f"/api/v1/qa/workspace/{job_id}/{first_doc_id}")
        assert ws_resp.status_code == 200
        ws_data = ws_resp.json()
        assert ws_data["job_id"] == job_id
        assert "decision" in ws_data
        assert "reason" in ws_data
