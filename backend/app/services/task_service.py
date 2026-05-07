"""Background Task Service - Async task processing."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import uuid


class TaskStatus(str, Enum):
    """Task execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Task:
    """Background task representation."""
    id: str
    task_type: str
    payload: dict
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = None
    started_at: datetime = None
    completed_at: datetime = None
    error: str = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()


class BackgroundTaskService:
    """Manage background tasks for async processing."""

    def schedule_knowledge_publish(
        self, knowledge_id: str, user_id: str
    ) -> str:
        """Schedule knowledge publish task."""
        task_id = str(uuid.uuid4())
        task = Task(
            id=task_id,
            task_type="knowledge.publish",
            payload={"knowledge_id": knowledge_id, "user_id": user_id}
        )
        return task_id

    def schedule_notification(
        self, user_id: str, event_type: str, payload: dict
    ) -> str:
        """Schedule notification task."""
        task_id = str(uuid.uuid4())
        task = Task(
            id=task_id,
            task_type="notification",
            payload={
                "user_id": user_id,
                "event_type": event_type,
                "payload": payload
            }
        )
        return task_id

    async def process_task(self, task: Task) -> None:
        """Process a background task."""
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.utcnow()
