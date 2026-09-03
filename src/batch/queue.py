import threading
from typing import List, Optional, Dict
from src.batch.models import JobTask, JobTaskStatus
from src.config.logging import logger

class JobQueue:
    def __init__(self):
        self._lock = threading.Lock()
        self._tasks: Dict[str, JobTask] = {}
        self._queue: List[str] = []  # Ordered job_ids

    def enqueue(self, root_dir: str, priority: int = 10, job_id: Optional[str] = None, max_retries: int = 2) -> JobTask:
        with self._lock:
            import os
            folder_name = os.path.basename(os.path.abspath(root_dir))
            jid = job_id or f"JOB-{folder_name}"
            
            # Check if existing task in queue
            if jid in self._tasks and self._tasks[jid].status in [JobTaskStatus.QUEUED, JobTaskStatus.RUNNING]:
                logger.info(f"Job {jid} is already active in queue.")
                return self._tasks[jid]
                
            task = JobTask(
                job_id=jid,
                root_dir=root_dir,
                priority=priority,
                status=JobTaskStatus.QUEUED,
                max_retries=max_retries
            )
            self._tasks[jid] = task
            self._queue.append(jid)
            
            # Sort queue by priority (ascending)
            self._queue.sort(key=lambda x: self._tasks[x].priority)
            logger.info(f"Enqueued job {jid} for {root_dir} (queue size: {len(self._queue)})")
            return task

    def get_next(self) -> Optional[JobTask]:
        with self._lock:
            while self._queue:
                jid = self._queue.pop(0)
                task = self._tasks.get(jid)
                if task and task.status == JobTaskStatus.QUEUED:
                    return task
            return None

    def get_task(self, job_id: str) -> Optional[JobTask]:
        with self._lock:
            return self._tasks.get(job_id)

    def cancel(self, job_id: str) -> bool:
        with self._lock:
            task = self._tasks.get(job_id)
            if not task:
                return False
            if task.status in [JobTaskStatus.QUEUED, JobTaskStatus.RUNNING]:
                task.status = JobTaskStatus.CANCELLED
                if job_id in self._queue:
                    self._queue.remove(job_id)
                logger.info(f"Cancelled job {job_id}")
                return True
            return False

    def list_all(self, status_filter: Optional[JobTaskStatus] = None) -> List[JobTask]:
        with self._lock:
            if status_filter:
                return [t for t in self._tasks.values() if t.status == status_filter]
            return list(self._tasks.values())

    def clear(self):
        with self._lock:
            self._tasks.clear()
            self._queue.clear()

job_queue = JobQueue()
