from enum import Enum
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class JobTaskStatus(str, Enum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

class JobTask(BaseModel):
    job_id: str
    root_dir: str
    priority: int = 10  # Lower number = higher priority
    status: JobTaskStatus = JobTaskStatus.QUEUED
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 2
    error_message: Optional[str] = None
    overall_decision: Optional[str] = None
    total_records: int = 0
    duration_seconds: float = 0.0
    reports: Dict[str, str] = Field(default_factory=dict)

class BatchSubmitRequest(BaseModel):
    folder_paths: List[str]
    priority: int = 10

class BatchSubmitResponse(BaseModel):
    submitted_count: int
    job_ids: List[str]
    message: str

class DirectoryScanRequest(BaseModel):
    parent_directory: str
    recursive: bool = False
    priority: int = 10

class BatchProgressSummary(BaseModel):
    total_jobs: int
    queued_count: int
    running_count: int
    completed_count: int
    failed_count: int
    cancelled_count: int
    active_workers: int
    max_workers: int
    total_records_processed: int
    auto_clear_total: int
    human_review_total: int
    blocked_total: int
    average_duration_seconds: float
    throughput_jobs_per_minute: float
