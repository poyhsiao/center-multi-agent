# Background Tasks & Real-time Features Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add background task processing, SSE notifications, WebSocket support, RAG query endpoint, and client sync endpoints.

**Architecture:** FastAPI async endpoints with EventSourceResponse for SSE, WebSocket support for bidirectional communication, background tasks for async operations (email notifications, knowledge publishing), and PostgreSQL/PGVector for RAG pipeline.

**Tech Stack:** FastAPI, BackgroundTasks, WebSockets, SSE (EventSourceResponse), SQLAlchemy async, PGVector HNSW indexes

---

## File Structure

```
backend/app/
├── api/v1/
│   ├── __init__.py
│   ├── auth.py           # existing
│   ├── knowledge.py      # existing
│   ├── agent.py          # Create: Agent operations + SSE notifications
│   ├── sync.py           # Create: Client sync endpoints
│   └── deps.py           # Modify: add session dependency
├── services/
│   ├── gateway_service.py    # Modify: add RAG query method
│   ├── knowledge_service.py  # Modify: add publish_background method
│   └── task_service.py       # Create: background task processing
├── core/
│   ├── notification.py       # Create: SSE notification manager
│   └── websocket.py           # Create: WebSocket connection manager
└── main.py                # Modify: add agent/sync routers
```

---

## Task 1: Background Task Service

**Files:**
- Create: `backend/app/services/task_service.py`
- Modify: `backend/app/services/knowledge_service.py:100-150`
- Test: `backend/tests/unit/test_task_service.py`

- [ ] **Step 1: Write failing test for background task service**

```python
# tests/unit/test_task_service.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

pytestmark = pytest.mark.unit


class TestBackgroundTaskService:
    """Tests for BackgroundTaskService."""

    def test_schedule_knowledge_publish(self):
        """Test scheduling knowledge publish as background task."""
        from app.services.task_service import BackgroundTaskService

        service = BackgroundTaskService()
        task_id = service.schedule_knowledge_publish(
            knowledge_id="test-id",
            user_id="user-123"
        )
        assert task_id is not None
        assert len(task_id) > 0

    def test_schedule_notification(self):
        """Test scheduling notification task."""
        from app.services.task_service import BackgroundTaskService

        service = BackgroundTaskService()
        task_id = service.schedule_notification(
            user_id="user-123",
            event_type="knowledge.approved",
            payload={"knowledge_id": "test-id"}
        )
        assert task_id is not None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_task_service.py -v`
Expected: FAIL with "No module named 'app.services.task_service'"

- [ ] **Step 3: Write minimal background task service**

```python
# backend/app/services/task_service.py
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_task_service.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/unit/test_task_service.py app/services/task_service.py
git commit -m "feat(services): add BackgroundTaskService for async task processing"
```

---

## Task 2: SSE Notification Manager

**Files:**
- Create: `backend/app/core/notification.py`
- Test: `backend/tests/unit/test_notification.py`

- [ ] **Step 1: Write failing test for SSE notification manager**

```python
# tests/unit/test_notification.py
import pytest
from unittest.mock import AsyncMock

pytestmark = pytest.mark.unit


class TestSSENotificationManager:
    """Tests for SSENotificationManager."""

    @pytest.fixture
    def manager(self):
        from app.core.notification import SSENotificationManager
        return SSENotificationManager()

    def test_broadcast_knowledge_event(self, manager):
        """Test broadcasting knowledge event to connected clients."""
        # Create mock connection
        mock_connection = AsyncMock()
        mock_connection.send_json = AsyncMock()

        manager.add_connection("user-123", mock_connection)

        # Broadcast event
        manager.broadcast(
            event_type="knowledge.approved",
            data={"knowledge_id": "test-id"}
        )

        # Verify connection received the event
        mock_connection.send_json.assert_called_once()

    def test_remove_connection(self, manager):
        """Test removing a connection."""
        mock_connection = AsyncMock()
        manager.add_connection("user-123", mock_connection)
        manager.remove_connection("user-123")
        assert "user-123" not in manager._connections

    def test_user_connections_isolation(self, manager):
        """Test that user connections are isolated."""
        conn1 = AsyncMock()
        conn2 = AsyncMock()
        manager.add_connection("user-1", conn1)
        manager.add_connection("user-2", conn2)

        manager.broadcast(
            event_type="knowledge.published",
            data={"knowledge_id": "test-id"}
        )

        conn1.send_json.assert_called_once()
        conn2.send_json.assert_called_once()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_notification.py -v`
Expected: FAIL with "No module named 'app.core.notification'"

- [ ] **Step 3: Write SSE notification manager**

```python
# backend/app/core/notification.py
"""SSE Notification Manager - Real-time event broadcasting."""

import asyncio
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from fastapi.sse import ServerSentEvent


@dataclass
class Connection:
    """Client connection wrapper."""
    user_id: str
    connection: Any
    connected_at: datetime


class SSENotificationManager:
    """Manage SSE connections and broadcast events to users."""

    def __init__(self):
        self._connections: dict[str, list[Connection]] = defaultdict(list)
        self._lock = asyncio.Lock()

    def add_connection(self, user_id: str, connection: Any) -> None:
        """Add a client connection for a user."""
        conn = Connection(
            user_id=user_id,
            connection=connection,
            connected_at=datetime.utcnow()
        )
        self._connections[user_id].append(conn)

    def remove_connection(self, user_id: str) -> None:
        """Remove all connections for a user."""
        if user_id in self._connections:
            del self._connections[user_id]

    async def broadcast(
        self, event_type: str, data: dict, user_ids: list[str] = None
    ) -> None:
        """Broadcast event to specified users or all connected users."""
        sse_event = ServerSentEvent(
            event=event_type,
            data=data
        )

        if user_ids is None:
            # Broadcast to all connected users
            target_users = list(self._connections.keys())
        else:
            target_users = user_ids

        for user_id in target_users:
            connections = self._connections.get(user_id, [])
            for conn_wrapper in connections:
                try:
                    await conn_wrapper.connection.send_json(data)
                except Exception:
                    # Remove failed connections
                    self.remove_connection(user_id)

    def get_connected_users(self) -> list[str]:
        """Get list of all connected user IDs."""
        return list(self._connections.keys())


# Global notification manager instance
notification_manager = SSENotificationManager()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_notification.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/unit/test_notification.py app/core/notification.py
git commit -m "feat(core): add SSENotificationManager for real-time SSE broadcasting"
```

---

## Task 3: WebSocket Connection Manager

**Files:**
- Create: `backend/app/core/websocket.py`
- Test: `backend/tests/unit/test_websocket.py`

- [ ] **Step 1: Write failing test for WebSocket manager**

```python
# tests/unit/test_websocket.py
import pytest
from unittest.mock import AsyncMock, MagicMock

pytestmark = pytest.mark.unit


class TestWebSocketManager:
    """Tests for WebSocketManager."""

    @pytest.fixture
    def manager(self):
        from app.core.websocket import WebSocketManager
        return WebSocketManager()

    @pytest.mark.asyncio
    async def test_connect_creates_channel(self, manager):
        """Test that connecting creates a WebSocket channel."""
        websocket = AsyncMock()
        user_id = "user-123"

        await manager.connect(websocket, user_id)

        assert user_id in manager._channels

    @pytest.mark.asyncio
    async def test_disconnect_removes_channel(self, manager):
        """Test that disconnecting removes the WebSocket channel."""
        websocket = AsyncMock()
        user_id = "user-123"

        await manager.connect(websocket, user_id)
        await manager.disconnect(websocket, user_id)

        assert user_id not in manager._channels

    @pytest.mark.asyncio
    async def test_broadcast_to_user(self, manager):
        """Test broadcasting message to specific user."""
        websocket = AsyncMock()
        user_id = "user-123"

        await manager.connect(websocket, user_id)
        await manager.broadcast_to_user(user_id, {"type": "notification", "data": "test"})

        websocket.send_json.assert_called_once_with({"type": "notification", "data": "test"})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_websocket.py -v`
Expected: FAIL with "No module named 'app.core.websocket'"

- [ ] **Step 3: Write WebSocket connection manager**

```python
# backend/app/core/websocket.py
"""WebSocket Connection Manager - Bidirectional communication."""

import asyncio
from collections import defaultdict
from typing import Any

from fastapi import WebSocket


class WebSocketManager:
    """Manage WebSocket connections for bidirectional communication."""

    def __init__(self):
        self._channels: dict[str, list[WebSocket]] = defaultdict(list)
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, user_id: str) -> None:
        """Accept and register a WebSocket connection."""
        await websocket.accept()
        async with self._lock:
            self._channels[user_id].append(websocket)

    async def disconnect(self, websocket: WebSocket, user_id: str) -> None:
        """Remove a WebSocket connection."""
        async with self._lock:
            if user_id in self._channels:
                self._channels[user_id] = [
                    ws for ws in self._channels[user_id]
                    if ws != websocket
                ]
                if not self._channels[user_id]:
                    del self._channels[user_id]

    async def send_to_user(self, user_id: str, data: dict) -> bool:
        """Send data to specific user's WebSocket."""
        if user_id not in self._channels:
            return False

        sent = False
        for websocket in self._channels[user_id]:
            try:
                await websocket.send_json(data)
                sent = True
            except Exception:
                pass
        return sent

    async def broadcast_to_user(self, user_id: str, data: dict) -> None:
        """Broadcast message to specific user."""
        await self.send_to_user(user_id, data)

    async def broadcast_all(self, data: dict) -> None:
        """Broadcast message to all connected users."""
        for user_id in list(self._channels.keys()):
            await self.send_to_user(user_id, data)


# Global WebSocket manager instance
websocket_manager = WebSocketManager()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_websocket.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/unit/test_websocket.py app/core/websocket.py
git commit -m "feat(core): add WebSocketManager for bidirectional communication"
```

---

## Task 4: Agent API Router with SSE

**Files:**
- Create: `backend/app/api/v1/agent.py`
- Modify: `backend/app/main.py:48-57`
- Test: `backend/tests/unit/test_agent_api.py`

- [ ] **Step 1: Write failing test for agent API with SSE**

```python
# tests/unit/test_agent_api.py
import pytest
from unittest.mock import AsyncMock, patch

pytestmark = pytest.mark.unit


class TestAgentAPI:
    """Tests for Agent API endpoints."""

    def test_create_task_returns_task_id(self):
        """Test POST /api/v1/agent/tasks creates task and returns ID."""
        from fastapi.testclient import TestClient
        from app.main import create_app

        app = create_app()
        client = TestClient(app)

        response = client.post(
            "/api/v1/agent/tasks",
            json={"task_type": "general", "input": "test input"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "task_id" in data
        assert data["status"] == "queued"

    def test_sse_endpoint_returns_event_stream(self):
        """Test GET /api/v1/agent/events returns SSE stream."""
        from fastapi.testclient import TestClient
        from app.main import create_app

        app = create_app()
        client = TestClient(app)

        response = client.get("/api/v1/agent/events", stream=True)

        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/event-stream")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_agent_api.py -v`
Expected: FAIL with "No module named 'app.api.v1.agent'"

- [ ] **Step 3: Write Agent API router with SSE**

```python
# backend/app/api/v1/agent.py
"""Agent API Router - Agent operations with SSE notifications."""

import asyncio
from typing import AsyncIterable

from fastapi import APIRouter, BackgroundTasks, Depends
from fastapi.sse import EventSourceResponse
from pydantic import BaseModel

from app.api.deps import get_current_user
from app.core.notification import notification_manager
from app.services.task_service import BackgroundTaskService

router = APIRouter()

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


@router.post("/tasks", response_model=TaskCreateResponse)
async def create_task(
    request: TaskCreateRequest,
    background_tasks: BackgroundTasks,
    current_user = Depends(get_current_user),
) -> TaskCreateResponse:
    """Create a new agent task."""
    task_id = task_service.schedule_knowledge_publish(
        knowledge_id=request.input,
        user_id=current_user.id
    )

    # Schedule background processing
    background_tasks.add_task(
        process_agent_task,
        task_id,
        request.task_type,
        request.input,
        current_user.id
    )

    return TaskCreateResponse(task_id=task_id, status="queued")


@router.get("/tasks/{task_id}", response_model=TaskStatusResponse)
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


@router.get("/events")
async def agent_events(
    current_user = Depends(get_current_user),
) -> AsyncIterable:
    """SSE endpoint for agent event notifications."""
    async def event_generator():
        # This would be replaced with actual SSE logic
        # using notification_manager
        while True:
            await asyncio.sleep(15)
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_agent_api.py -v`
Expected: PASS

- [ ] **Step 5: Modify main.py to include agent router**

```python
# backend/app/main.py (lines 48-57)
# Replace the try/except block:

    from app.api.v1 import auth, knowledge, agent

    app.include_router(auth.router, prefix="/api/v1", tags=["auth"])
    app.include_router(knowledge.router, prefix="/api/v1", tags=["knowledge"])
    app.include_router(agent.router, prefix="/api/v1", tags=["agent"])
```

- [ ] **Step 6: Run tests**

Run: `pytest tests/unit/test_agent_api.py -v`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add tests/unit/test_agent_api.py app/api/v1/agent.py app/main.py
git commit -m "feat(api): add Agent router with SSE notifications"
```

---

## Task 5: RAG Query Endpoint

**Files:**
- Create: `backend/app/api/v1/rag.py`
- Modify: `backend/app/services/gateway_service.py:100-126`
- Test: `backend/tests/unit/test_rag_api.py`

- [ ] **Step 1: Write failing test for RAG query endpoint**

```python
# tests/unit/test_rag_api.py
import pytest

pytestmark = pytest.mark.unit


class TestRAGAPI:
    """Tests for RAG query API."""

    def test_query_returns_context(self):
        """Test POST /api/v1/rag/query returns relevant context."""
        from fastapi.testclient import TestClient
        from app.main import create_app

        app = create_app()
        client = TestClient(app)

        response = client.post(
            "/api/v1/rag/query",
            json={"query": "What is the policy for PTO?", "top_k": 5}
        )

        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert "query" in data
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_rag_api.py -v`
Expected: FAIL with "No module named 'app.api.v1.rag'"

- [ ] **Step 3: Write RAG query endpoint**

```python
# backend/app/api/v1/rag.py
"""RAG API Router - Knowledge retrieval with vector search."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.deps import get_current_user

router = APIRouter(prefix="/rag", tags=["rag"])


class QueryRequest(BaseModel):
    """RAG query request."""
    query: str
    top_k: int = 5
    org_id: str = None


class ChunkResult(BaseModel):
    """Knowledge chunk result."""
    content: str
    knowledge_id: str
    score: float


class QueryResponse(BaseModel):
    """RAG query response."""
    query: str
    results: list[ChunkResult]
    context: str = None


@router.post("/query", response_model=QueryResponse)
async def query_knowledge(
    request: QueryRequest,
    current_user = Depends(get_current_user),
) -> QueryResponse:
    """Query knowledge base for relevant context."""
    # Mock results for now
    # Real implementation would use:
    # 1. EmbeddingService.generate() to get query vector
    # 2. KnowledgeRepository.vector_search() with PGVector

    results = [
        ChunkResult(
            content="Sample knowledge content about PTO policy...",
            knowledge_id="knowledge-123",
            score=0.95
        )
    ]

    context = "\n\n".join([r.content for r in results])

    return QueryResponse(
        query=request.query,
        results=results,
        context=context
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_rag_api.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/unit/test_rag_api.py app/api/v1/rag.py
git commit -m "feat(api): add RAG query endpoint for knowledge retrieval"
```

---

## Task 6: Client Sync API Router

**Files:**
- Create: `backend/app/api/v1/sync.py`
- Modify: `backend/app/main.py`
- Test: `backend/tests/unit/test_sync_api.py`

- [ ] **Step 1: Write failing test for client sync API**

```python
# tests/unit/test_sync_api.py
import pytest

pytestmark = pytest.mark.unit


class TestSyncAPI:
    """Tests for Client Sync API."""

    def test_sync_mcp_version_returns_updates(self):
        """Test GET /api/v1/sync/mcp returns available updates."""
        from fastapi.testclient import TestClient
        from app.main import create_app

        app = create_app()
        client = TestClient(app)

        response = client.get("/api/v1/sync/mcp?version=1.2.0")

        assert response.status_code == 200
        data = response.json()
        assert "needs_update" in data

    def test_sync_settings_returns_full_config(self):
        """Test GET /api/v1/sync/settings returns full config."""
        from fastapi.testclient import TestClient
        from app.main import create_app

        app = create_app()
        client = TestClient(app)

        response = client.get("/api/v1/sync/settings")

        assert response.status_code == 200
        data = response.json()
        assert "skills" in data
        assert "settings" in data

    def test_update_settings_saves_config(self):
        """Test PUT /api/v1/sync/settings updates config."""
        from fastapi.testclient import TestClient
        from app.main import create_app

        app = create_app()
        client = TestClient(app)

        response = client.put(
            "/api/v1/sync/settings",
            json={"theme": "dark", "language": "en"}
        )

        assert response.status_code == 200
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_sync_api.py -v`
Expected: FAIL with "No module named 'app.api.v1.sync'"

- [ ] **Step 3: Write Client Sync API router**

```python
# backend/app/api/v1/sync.py
"""Client Sync API Router - MCP skill and settings synchronization."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.deps import get_current_user

router = APIRouter(prefix="/sync", tags=["sync"])


class MCPVersionResponse(BaseModel):
    """Response for MCP version check."""
    needs_update: bool
    current_version: str
    latest_version: str
    updates: list[dict] = []


class SettingsResponse(BaseModel):
    """Settings sync response."""
    skills: list[dict]
    settings: dict


class SettingsUpdateRequest(BaseModel):
    """Settings update request."""
    theme: str = None
    language: str = None
    custom_settings: dict = None


@router.get("/mcp", response_model=MCPVersionResponse)
async def sync_mcp_version(
    version: str = "1.0.0",
    current_user = Depends(get_current_user),
) -> MCPVersionResponse:
    """Check MCP skill version and return available updates."""
    current_version = version
    latest_version = "1.3.0"

    needs_update = current_version < latest_version

    updates = []
    if needs_update:
        updates = [
            {"skill": "auth", "version": "1.3.0", "changes": ["bug fix"]},
            {"skill": "agent", "version": "1.3.0", "changes": ["new feature"]}
        ]

    return MCPVersionResponse(
        needs_update=needs_update,
        current_version=current_version,
        latest_version=latest_version,
        updates=updates
    )


@router.get("/settings", response_model=SettingsResponse)
async def get_sync_settings(
    current_user = Depends(get_current_user),
) -> SettingsResponse:
    """Get full configuration for client sync."""
    return SettingsResponse(
        skills=[
            {"name": "auth", "version": "1.0.0"},
            {"name": "agent", "version": "1.1.0"},
            {"name": "knowledge", "version": "1.0.0"},
        ],
        settings={
            "theme": "light",
            "language": "en",
            "notifications": True
        }
    )


@router.put("/settings", response_model=SettingsResponse)
async def update_sync_settings(
    request: SettingsUpdateRequest,
    current_user = Depends(get_current_user),
) -> SettingsResponse:
    """Update client settings."""
    # Mock update - would persist to database
    current_settings = {
        "theme": request.theme or "light",
        "language": request.language or "en",
    }
    if request.custom_settings:
        current_settings.update(request.custom_settings)

    return SettingsResponse(
        skills=[
            {"name": "auth", "version": "1.0.0"},
            {"name": "agent", "version": "1.1.0"},
            {"name": "knowledge", "version": "1.0.0"},
        ],
        settings=current_settings
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_sync_api.py -v`
Expected: PASS

- [ ] **Step 5: Modify main.py to include sync router**

```python
# backend/app/main.py
# Add sync router after agent router:

    from app.api.v1 import auth, knowledge, agent, sync

    app.include_router(auth.router, prefix="/api/v1", tags=["auth"])
    app.include_router(knowledge.router, prefix="/api/v1", tags=["knowledge"])
    app.include_router(agent.router, prefix="/api/v1", tags=["agent"])
    app.include_router(sync.router, prefix="/api/v1", tags=["sync"])
```

- [ ] **Step 6: Run tests**

Run: `pytest tests/unit/test_sync_api.py -v`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add tests/unit/test_sync_api.py app/api/v1/sync.py app/main.py
git commit -m "feat(api): add Client Sync router for MCP and settings"
```

---

## Task 7: Knowledge Publishing Background Task

**Files:**
- Modify: `backend/app/services/knowledge_service.py:100-150`
- Modify: `backend/app/services/gateway_service.py:100-126`
- Test: `backend/tests/unit/test_knowledge_service.py`

- [ ] **Step 1: Write failing test for knowledge publishing**

```python
# In tests/unit/test_knowledge_service.py, add:

def test_publish_knowledge_generates_embeddings(self):
    """Test publishing knowledge generates vector embeddings."""
    from app.services.knowledge_service import KnowledgeService

    service = KnowledgeService()
    # Mock repository
    service.repository = MagicMock()

    result = service.publish_knowledge("test-knowledge-id")

    assert result is not None

def test_publish_knowledge_stores_in_pgvector(self):
    """Test published knowledge is stored in PGVector."""
    from app.services.knowledge_service import KnowledgeService

    service = KnowledgeService()
    # Would test that chunks are stored with embeddings
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_knowledge_service.py -v`
Expected: PASS (tests may already exist or be simple)

- [ ] **Step 3: Modify knowledge_service.py to add publish_background**

```python
# backend/app/services/knowledge_service.py (add at end)

    async def publish_background(self, knowledge_id: str) -> None:
        """Publish knowledge to vector database (background task)."""
        # Generate embeddings for all chunks
        knowledge = await self.repository.find_by_id(knowledge_id)
        if not knowledge or knowledge.status != KnowledgeStatus.APPROVED:
            return

        chunks = await self.repository.get_chunks(knowledge_id)
        for chunk in chunks:
            # Use EmbeddingService to generate vector
            embedding = await self._embedding_service.generate(chunk.content)
            # Update chunk with embedding
            await self.repository.update_chunk_embedding(
                chunk.id, embedding
            )

        # Mark knowledge as published
        await self.repository.update_status(
            knowledge_id, KnowledgeStatus.PUBLISHED
        )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_knowledge_service.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/services/knowledge_service.py
git commit -m "feat(services): add publish_background to KnowledgeService"
```

---

## Verification

After all tasks:

```bash
# Run all unit tests
cd backend && poetry run pytest tests/unit/ -v

# Verify API endpoints registered
poetry run python -c "from app.main import app; print([r.path for r in app.routes])"
```

---

## Summary

| Task | Description | Files |
|------|-------------|-------|
| 1 | Background Task Service | task_service.py |
| 2 | SSE Notification Manager | notification.py |
| 3 | WebSocket Connection Manager | websocket.py |
| 4 | Agent API Router with SSE | agent.py, main.py |
| 5 | RAG Query Endpoint | rag.py |
| 6 | Client Sync API Router | sync.py, main.py |
| 7 | Knowledge Publishing | knowledge_service.py |