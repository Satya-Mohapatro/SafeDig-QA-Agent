"""Unit tests for observability, Prometheus metrics, and middleware."""

import pytest
import httpx
from src.utils.telemetry import MetricsRegistry
from src.api.app import create_app

def test_metrics_registry_recording():
    reg = MetricsRegistry()
    reg.record_job("COMPLETED")
    reg.record_job("COMPLETED")
    reg.record_document("AUTO_CLEAR")
    reg.record_document("HUMAN_REVIEW")
    reg.record_reconciliation("MATCH")
    reg.record_stage_duration("pdf_extract", 0.125)
    reg.set_queue_pending(5)
    reg.set_active_workers(2)

    snapshot = reg.get_metrics_snapshot()
    assert snapshot["jobs"]["COMPLETED"] == 2
    assert snapshot["documents"]["AUTO_CLEAR"] == 1
    assert snapshot["documents"]["HUMAN_REVIEW"] == 1
    assert snapshot["reconciliations"]["MATCH"] == 1
    assert snapshot["escaped_hazards"] == 0
    assert snapshot["queue_pending_items"] == 5
    assert snapshot["active_workers"] == 2
    assert "pdf_extract" in snapshot["stage_durations"]
    assert snapshot["stage_durations"]["pdf_extract"]["count"] == 1

def test_prometheus_exposition_format():
    reg = MetricsRegistry()
    reg.record_job("COMPLETED")
    reg.record_document("AUTO_CLEAR")
    reg.record_stage_duration("ocr", 0.05)

    prom_text = reg.generate_prometheus_metrics()
    assert "# HELP safedig_jobs_total" in prom_text
    assert 'safedig_jobs_total{status="COMPLETED"} 1' in prom_text
    assert 'safedig_documents_total{decision="AUTO_CLEAR"} 1' in prom_text
    assert "safedig_escaped_hazards_total 0" in prom_text
    assert 'safedig_stage_duration_seconds_total{stage="ocr"}' in prom_text

@pytest.mark.asyncio
async def test_correlation_id_middleware_and_metrics_endpoint():
    app = create_app()
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        # Test custom correlation ID propagation
        headers = {"X-Correlation-ID": "test-corr-12345"}
        resp = await client.get("/api/v1/health", headers=headers)
        assert resp.status_code == 200
        assert resp.headers.get("X-Correlation-ID") == "test-corr-12345"
        assert "X-Response-Time" in resp.headers

        # Test Prometheus metrics endpoint
        prom_resp = await client.get("/metrics")
        assert prom_resp.status_code == 200
        assert "safedig_escaped_hazards_total" in prom_resp.text

        # Test JSON metrics snapshot endpoint
        json_resp = await client.get("/api/v1/metrics")
        assert json_resp.status_code == 200
        data = json_resp.json()
        assert "escaped_hazards" in data
        assert data["escaped_hazards"] == 0
