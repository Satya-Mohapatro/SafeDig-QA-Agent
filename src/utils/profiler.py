"""Pipeline Performance Profiler and Benchmarking Utilities.

Provides context managers and decorators for profiling execution times
and recording timing metrics across all map processing stages.
"""
import time
import functools
from typing import Optional, Callable, Any
from contextlib import contextmanager

from src.utils.logging import get_logger
from src.utils.telemetry import metrics_registry

logger = get_logger("safedig_map_qa.profiler")

@contextmanager
def profile_stage(stage_name: str, extra_info: Optional[str] = None):
    """Context manager to measure and record execution time of a pipeline stage."""
    start_time = time.perf_counter()
    try:
        yield
    finally:
        duration = time.perf_counter() - start_time
        metrics_registry.record_stage_duration(stage_name, duration)
        msg = f"[Profiler] Stage '{stage_name}' executed in {duration:.4f}s"
        if extra_info:
            msg += f" ({extra_info})"
        logger.debug(msg)


def timed_stage(stage_name: str):
    """Decorator to profile a function and record timing under stage_name."""
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start = time.perf_counter()
            try:
                return func(*args, **kwargs)
            finally:
                dur = time.perf_counter() - start
                metrics_registry.record_stage_duration(stage_name, dur)
                logger.debug(f"[Profiler] {func.__name__} ({stage_name}) completed in {dur:.4f}s")
        return wrapper
    return decorator
