"""Telemetry and Metrics Collection for SafeDig AI Map QA.

Provides thread-safe in-memory metric aggregation and Prometheus format generation.
"""
import time
import threading
from typing import Dict, Any, List
from collections import defaultdict

class MetricsRegistry:
    """Thread-safe in-memory metric registry with Prometheus export."""
    
    def __init__(self):
        self._lock = threading.Lock()
        
        # Counters
        self._jobs_total = defaultdict(int)  # status -> count
        self._documents_total = defaultdict(int)  # decision -> count
        self._reconciliation_outcomes = defaultdict(int)  # outcome -> count
        self._escaped_hazards_total = 0  # Invariant: Must remain 0
        
        # Timers / Histograms (stage -> {"count": int, "total_sec": float})
        self._stage_durations = defaultdict(lambda: {"count": 0, "total_sec": 0.0})
        
        # Gauges
        self._queue_pending_items = 0
        self._active_workers = 0

    def record_job(self, status: str = "COMPLETED"):
        with self._lock:
            self._jobs_total[status] += 1

    def record_document(self, decision: str):
        with self._lock:
            self._documents_total[decision] += 1

    def record_reconciliation(self, outcome: str):
        with self._lock:
            self._reconciliation_outcomes[outcome] += 1

    def record_escaped_hazard(self):
        """Record an escaped hazard violation. INVARIANT WARNING: This should NEVER be called."""
        with self._lock:
            self._escaped_hazards_total += 1

    def record_stage_duration(self, stage: str, duration_sec: float):
        with self._lock:
            self._stage_durations[stage]["count"] += 1
            self._stage_durations[stage]["total_sec"] += duration_sec

    def set_queue_pending(self, count: int):
        with self._lock:
            self._queue_pending_items = max(0, count)

    def set_active_workers(self, count: int):
        with self._lock:
            self._active_workers = max(0, count)

    def get_metrics_snapshot(self) -> Dict[str, Any]:
        """Return a structured dictionary snapshot of all metrics."""
        with self._lock:
            stages_summary = {}
            for st, val in self._stage_durations.items():
                avg = (val["total_sec"] / val["count"]) if val["count"] > 0 else 0.0
                stages_summary[st] = {
                    "count": val["count"],
                    "total_seconds": round(val["total_sec"], 4),
                    "avg_seconds": round(avg, 4)
                }
                
            return {
                "jobs": dict(self._jobs_total),
                "documents": dict(self._documents_total),
                "reconciliations": dict(self._reconciliation_outcomes),
                "escaped_hazards": self._escaped_hazards_total,
                "stage_durations": stages_summary,
                "queue_pending_items": self._queue_pending_items,
                "active_workers": self._active_workers
            }

    def generate_prometheus_metrics(self) -> str:
        """Render metrics in standard Prometheus exposition format."""
        lines = []
        
        with self._lock:
            # Jobs total
            lines.append("# HELP safedig_jobs_total Total number of batch or enquiry jobs processed.")
            lines.append("# TYPE safedig_jobs_total counter")
            for status, count in self._jobs_total.items():
                lines.append(f'safedig_jobs_total{{status="{status}"}} {count}')
            if not self._jobs_total:
                lines.append('safedig_jobs_total{status="COMPLETED"} 0')

            # Documents total
            lines.append("\n# HELP safedig_documents_total Total documents evaluated by decision.")
            lines.append("# TYPE safedig_documents_total counter")
            for dec, count in self._documents_total.items():
                lines.append(f'safedig_documents_total{{decision="{dec}"}} {count}')
            if not self._documents_total:
                lines.append('safedig_documents_total{decision="AUTO_CLEAR"} 0')

            # Escaped hazards total (Invariant counter)
            lines.append("\n# HELP safedig_escaped_hazards_total Total escaped hazard violations (MUST BE 0).")
            lines.append("# TYPE safedig_escaped_hazards_total counter")
            lines.append(f"safedig_escaped_hazards_total {self._escaped_hazards_total}")

            # Queue pending items gauge
            lines.append("\n# HELP safedig_queue_pending_items Current items awaiting human review.")
            lines.append("# TYPE safedig_queue_pending_items gauge")
            lines.append(f"safedig_queue_pending_items {self._queue_pending_items}")

            # Active workers gauge
            lines.append("\n# HELP safedig_active_workers Current active worker processes.")
            lines.append("# TYPE safedig_active_workers gauge")
            lines.append(f"safedig_active_workers {self._active_workers}")

            # Stage duration histogram/summary
            lines.append("\n# HELP safedig_stage_duration_seconds_total Total duration in seconds spent per pipeline stage.")
            lines.append("# TYPE safedig_stage_duration_seconds_total counter")
            for stage, val in self._stage_durations.items():
                lines.append(f'safedig_stage_duration_seconds_total{{stage="{stage}"}} {round(val["total_sec"], 4)}')
                lines.append(f'safedig_stage_duration_seconds_count{{stage="{stage}"}} {val["count"]}')

        lines.append("")
        return "\n".join(lines)


# Global Singleton Metrics Registry
metrics_registry = MetricsRegistry()
