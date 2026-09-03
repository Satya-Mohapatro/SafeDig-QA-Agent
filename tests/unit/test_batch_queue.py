import pytest
from src.batch.queue import JobQueue
from src.batch.models import JobTaskStatus

def test_job_queue_basic_operations():
    q = JobQueue()
    t1 = q.enqueue("d:/Safedig_AG/Data/244414_201678", priority=10, job_id="JOB-1")
    t2 = q.enqueue("d:/Safedig_AG/Data/299208_172565", priority=5, job_id="JOB-2")  # Higher priority
    
    assert t1.status == JobTaskStatus.QUEUED
    assert t2.status == JobTaskStatus.QUEUED
    
    # Highest priority (lower number) should come first
    first = q.get_next()
    assert first is not None
    assert first.job_id == "JOB-2"
    
    second = q.get_next()
    assert second is not None
    assert second.job_id == "JOB-1"
    
    third = q.get_next()
    assert third is None

def test_job_queue_cancellation():
    q = JobQueue()
    q.enqueue("d:/Safedig_AG/Data/534668_175407", priority=10, job_id="JOB-CANCEL")
    cancelled = q.cancel("JOB-CANCEL")
    assert cancelled is True
    
    task = q.get_task("JOB-CANCEL")
    assert task.status == JobTaskStatus.CANCELLED
    
    # Should not return cancelled tasks
    next_task = q.get_next()
    assert next_task is None
