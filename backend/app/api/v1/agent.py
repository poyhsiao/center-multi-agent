"""Agent API Router - Agent operations with SSE notifications."""

import asyncio
from typing import AsyncIterable

from fastapi import APIRouter, BackgroundTasks, Depends
from sse_starlette import EventSourceResponse
from pydantic import BaseModel

from app.api.deps import get_current_user, require_permission
from app.core.rbac import Permission
from app.core.notification import notification_manager
from app.services.task_service import BackgroundTaskService

router = APIRouter(prefix="/agent", tags=["agent"])

task_service = BackgroundTaskService()


class TaskCreateRequest(BaseModel):
    """Request to create an agent task."""
    task_type: str = "general"
    input: str


class TaskCreateResponse(BaseModel):
    """Response after creating a task."""
    task_id: str
    status: str = "queued"


class TaskStatusResponse(BaseModel):
    """Task status response."""
    task_id: str
    status: str
    result: dict = None


@router.post("/tasks", response_model=TaskCreateResponse, dependencies=[Depends(require_permission(Permission.AGENT_WRITE))])
async def create_task(
    request: TaskCreateRequest,
    background_tasks: BackgroundTasks,
    current_user = Depends(get_current_user),
) -> TaskCreateResponse:
    """Create a new agent task."""
    task_id = task_service.schedule_knowledge_publish(
        knowledge_id=request.input,
        user_id=current_user.user_id
    )

    # Schedule background processing
    background_tasks.add_task(
        process_agent_task,
        task_id,
        request.task_type,
        request.input,
        current_user.user_id
    )

    return TaskCreateResponse(task_id=task_id, status="queued")


@router.get("/tasks/{task_id}", response_model=TaskStatusResponse, dependencies=[Depends(require_permission(Permission.AGENT_READ))])
async def get_task_status(
    task_id: str,
    current_user = Depends(get_current_user),
) -> TaskStatusResponse:
    """Get status of an agent task."""
    # Mock status for now
    return TaskStatusResponse(
        task_id=task_id,
        status="completed",
        result={"output": "Task completed"}
    )


@router.get("/events", dependencies=[Depends(require_permission(Permission.AGENT_READ))])
async def agent_events(
    current_user = Depends(get_current_user),
):
    """SSE endpoint for agent event notifications."""
    async def event_generator():
        # This would be replaced with actual SSE logic
        # using notification_manager
        import random
        for _ in range(2):  # Limit for testing
            await asyncio.sleep(0.1)
            yield {"event": "ping", "data": {}}

    return EventSourceResponse(event_generator())


async def process_agent_task(
    task_id: str,
    task_type: str,
    input_data: str,
    user_id: str
) -> None:
    """Background task processor for agent operations."""
    # Simulate task processing
    await asyncio.sleep(1)

    # Notify completion via SSE
    await notification_manager.broadcast(
        event_type="agent.task.completed",
        data={"task_id": task_id, "status": "completed"},
        user_ids=[user_id]
    )
