"""API Middleware for Request Tracing and Observability.

Attaches X-Correlation-ID to all requests, logs execution timings,
and propagates correlation context to downstream operations.
"""
import uuid
import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from src.utils.logging import get_logger
from src.utils.telemetry import metrics_registry

logger = get_logger("safedig_map_qa.middleware")

class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """Middleware that extracts or generates a unique correlation ID for every request."""
    
    async def dispatch(self, request: Request, call_next) -> Response:
        start_time = time.perf_counter()
        
        # Extract existing or generate new correlation ID
        correlation_id = (
            request.headers.get("X-Correlation-ID") or 
            request.headers.get("X-Request-ID") or 
            f"req-{uuid.uuid4().hex[:12]}"
        )
        
        # Attach to request state for access within route handlers
        request.state.correlation_id = correlation_id
        
        try:
            response = await call_next(request)
        except Exception as exc:
            duration = time.perf_counter() - start_time
            logger.error(
                f"Unhandled error processing request {request.method} {request.url.path} "
                f"[corr_id={correlation_id}] after {duration:.4f}s: {exc}"
            )
            raise
            
        duration = time.perf_counter() - start_time
        response.headers["X-Correlation-ID"] = correlation_id
        response.headers["X-Response-Time"] = f"{duration:.4f}s"
        
        # Optionally record API route timing
        metrics_registry.record_stage_duration(f"api_{request.method.lower()}", duration)
        
        return response
