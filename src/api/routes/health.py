"""Health and Readiness Probes for SafeDig AI Map QA."""

import os
import time
from typing import Dict, Any
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from src.config.settings import settings
from src.warnings import master_warning_catalogue
from src.db.engine import AsyncSessionLocal

from sqlalchemy import text

router = APIRouter(tags=["Health"])

START_TIME = time.time()

@router.get("/health")
def liveness_probe():
    """Liveness probe to check if the API server process is alive."""
    uptime_sec = round(time.time() - START_TIME, 2)
    return {
        "status": "HEALTHY",
        "service": "safedig-map-qa-agent",
        "version": settings.engine_version,
        "uptime_seconds": uptime_sec
    }

@router.get("/health/ready")
async def readiness_probe():
    """Readiness probe to check if all backend subsystems are functional."""
    checks: Dict[str, Any] = {
        "database": "UNKNOWN",
        "output_directory": "UNKNOWN",
        "warning_catalogue": "UNKNOWN"
    }
    all_healthy = True

    # 1. Check Warning Catalogue
    cat_count = len(master_warning_catalogue.definitions)
    if cat_count > 0:
        checks["warning_catalogue"] = f"READY ({cat_count} definitions)"
    else:
        checks["warning_catalogue"] = "EMPTY"
        all_healthy = False

    # 2. Check Output Directory Writability
    out_dir = settings.output_dir
    try:
        os.makedirs(out_dir, exist_ok=True)
        test_file = os.path.join(out_dir, ".health_check_tmp")
        with open(test_file, "w") as f:
            f.write("ok")
        if os.path.exists(test_file):
            os.remove(test_file)
        checks["output_directory"] = f"WRITABLE ({out_dir})"
    except Exception as e:
        checks["output_directory"] = f"FAILED: {str(e)}"
        all_healthy = False

    # 3. Check Database Connectivity
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        checks["database"] = "CONNECTED"
    except Exception as e:
        checks["database"] = f"DEGRADED/UNAVAILABLE ({str(e)})"
        # Persistence is designed to degrade gracefully to file output
        # so we don't necessarily fail readiness if DB is dev SQLite fallback

    status_code = status.HTTP_200_OK if all_healthy else status.HTTP_503_SERVICE_UNAVAILABLE
    return JSONResponse(
        status_code=status_code,
        content={
            "status": "READY" if all_healthy else "NOT_READY",
            "service": "safedig-map-qa-agent",
            "version": settings.engine_version,
            "checks": checks
        }
    )

