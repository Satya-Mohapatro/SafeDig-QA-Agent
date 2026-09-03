import time
import threading
from datetime import datetime
from typing import List, Optional
from src.batch.models import JobTask, JobTaskStatus, BatchProgressSummary
from src.batch.queue import job_queue, JobQueue
from src.orchestration import map_qa_workflow, MapQAState
from src.config.settings import settings
from src.config.logging import logger

class BatchWorkerPool:
    def __init__(self, max_workers: Optional[int] = None, queue: Optional[JobQueue] = None):
        self.max_workers = max_workers or settings.max_workers or 4
        self.queue = queue or job_queue
        self._threads: List[threading.Thread] = []
        self._running = False
        self._lock = threading.Lock()
        self._active_workers = 0

    def start(self):
        with self._lock:
            if self._running:
                return
            self._running = True
            logger.info(f"Starting BatchWorkerPool with {self.max_workers} concurrent workers...")
            for i in range(self.max_workers):
                t = threading.Thread(target=self._worker_loop, name=f"SafeDigWorker-{i+1}", daemon=True)
                t.start()
                self._threads.append(t)

    def stop(self, timeout_sec: float = 5.0):
        with self._lock:
            self._running = False
        for t in self._threads:
            t.join(timeout=timeout_sec)
        self._threads.clear()
        logger.info("BatchWorkerPool stopped.")

    def _worker_loop(self):
        while self._running:
            task = self.queue.get_next()
            if not task:
                time.sleep(0.2)
                continue

            with self._lock:
                self._active_workers += 1

            self._execute_task(task)

            with self._lock:
                self._active_workers = max(0, self._active_workers - 1)

    def _execute_task(self, task: JobTask):
        task.status = JobTaskStatus.RUNNING
        task.started_at = datetime.utcnow().isoformat()
        t0 = time.time()
        
        logger.info(f"[{threading.current_thread().name}] Processing job {task.job_id} on '{task.root_dir}'")
        
        try:
            initial_state: MapQAState = {
                "root_dir": task.root_dir,
                "job_id": task.job_id
            }
            final_state = map_qa_workflow.invoke(initial_state)
            
            task.status = JobTaskStatus.COMPLETED
            task.completed_at = datetime.utcnow().isoformat()
            task.overall_decision = final_state.get("overall_decision", "UNKNOWN")
            task.total_records = len(final_state.get("document_results", []))
            task.reports = final_state.get("reports", {})
            task.duration_seconds = round(time.time() - t0, 2)
            logger.info(f"Job {task.job_id} completed successfully in {task.duration_seconds}s (Decision: {task.overall_decision})")
            
        except Exception as e:
            logger.error(f"Error executing job {task.job_id}: {e}")
            if task.retry_count < task.max_retries:
                task.retry_count += 1
                task.status = JobTaskStatus.QUEUED
                logger.info(f"Re-queueing job {task.job_id} for retry {task.retry_count}/{task.max_retries}")
                self.queue._queue.append(task.job_id)
            else:
                task.status = JobTaskStatus.FAILED
                task.completed_at = datetime.utcnow().isoformat()
                task.error_message = str(e)
                task.duration_seconds = round(time.time() - t0, 2)

    def get_progress_summary(self) -> BatchProgressSummary:
        all_tasks = self.queue.list_all()
        queued = sum(1 for t in all_tasks if t.status == JobTaskStatus.QUEUED)
        running = sum(1 for t in all_tasks if t.status == JobTaskStatus.RUNNING)
        completed = sum(1 for t in all_tasks if t.status == JobTaskStatus.COMPLETED)
        failed = sum(1 for t in all_tasks if t.status == JobTaskStatus.FAILED)
        cancelled = sum(1 for t in all_tasks if t.status == JobTaskStatus.CANCELLED)
        
        total_records = sum(t.total_records for t in all_tasks if t.status == JobTaskStatus.COMPLETED)
        durations = [t.duration_seconds for t in all_tasks if t.status == JobTaskStatus.COMPLETED and t.duration_seconds > 0]
        avg_dur = sum(durations) / len(durations) if durations else 0.0
        
        auto_c = sum(1 for t in all_tasks if t.overall_decision == "AUTO_CLEAR")
        human_r = sum(1 for t in all_tasks if t.overall_decision == "HUMAN_REVIEW")
        blocked_c = sum(1 for t in all_tasks if t.overall_decision == "BLOCKED")
        
        jobs_per_min = (60.0 / avg_dur * self.max_workers) if avg_dur > 0 else 0.0

        return BatchProgressSummary(
            total_jobs=len(all_tasks),
            queued_count=queued,
            running_count=running,
            completed_count=completed,
            failed_count=failed,
            cancelled_count=cancelled,
            active_workers=self._active_workers,
            max_workers=self.max_workers,
            total_records_processed=total_records,
            auto_clear_total=auto_c,
            human_review_total=human_r,
            blocked_total=blocked_c,
            average_duration_seconds=round(avg_dur, 2),
            throughput_jobs_per_minute=round(jobs_per_min, 1)
        )

worker_pool = BatchWorkerPool()
