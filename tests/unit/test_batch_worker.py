import pytest
import time
from src.batch.queue import JobQueue
from src.batch.worker import BatchWorkerPool
from src.batch.models import JobTaskStatus

def test_batch_worker_pool_execution():
    custom_queue = JobQueue()
    worker = BatchWorkerPool(max_workers=2, queue=custom_queue)
    
    # Enqueue a real folder
    task = custom_queue.enqueue("d:/Safedig_AG/Data/244414_201678", priority=1, job_id="JOB-WORKER-TEST")
    
    worker.start()
    
    # Wait for completion (max 25s)
    for _ in range(50):
        if task.status in [JobTaskStatus.COMPLETED, JobTaskStatus.FAILED]:
            break
        time.sleep(0.5)
        
    worker.stop()
    
    assert task.status == JobTaskStatus.COMPLETED
    assert task.total_records == 69
    assert task.duration_seconds > 0
    assert task.overall_decision in ["AUTO_CLEAR", "HUMAN_REVIEW", "BLOCKED"]
    
    summary = worker.get_progress_summary()
    assert summary.completed_count == 1
    assert summary.total_records_processed == 69
