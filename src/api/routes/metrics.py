"""Metrics Endpoints for Prometheus and Application Telemetry."""

from fastapi import APIRouter
from fastapi.responses import PlainTextResponse, JSONResponse

from src.utils.telemetry import metrics_registry

router = APIRouter(tags=["Observability"])

@router.get("/metrics", response_class=PlainTextResponse)
def get_prometheus_metrics():
    """Export Prometheus format metrics."""
    return metrics_registry.generate_prometheus_metrics()

@router.get("/api/v1/metrics", response_class=JSONResponse)
def get_json_metrics_snapshot():
    """Export structured JSON snapshot of all system metrics."""
    return metrics_registry.get_metrics_snapshot()
