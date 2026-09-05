"""Integration tests for production hardening and resilience."""

import os
import pytest
import httpx
from src.api.app import create_app
from src.utils.security import sanitize_path, validate_pdf_safety, SecurityError
from tests.conftest import PROJECT_ROOT, DATA_DIR, SAMPLE_FOLDER_244414, SAMPLE_NGED_PDF

@pytest.mark.asyncio
async def test_hardening_e2e_metrics_and_health():
    app = create_app()
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        # Check health
        h_resp = await client.get("/health")
        assert h_resp.status_code == 200
        
        # Check readiness
        r_resp = await client.get("/health/ready")
        assert r_resp.status_code == 200
        
        # Check metrics endpoint
        m_resp = await client.get("/metrics")
        assert m_resp.status_code == 200
        assert "safedig_jobs_total" in m_resp.text

def test_hardening_path_traversal_blocking():
    base_dir = str(DATA_DIR)
    with pytest.raises(SecurityError):
        sanitize_path(base_dir, "../../../Windows/System32")
