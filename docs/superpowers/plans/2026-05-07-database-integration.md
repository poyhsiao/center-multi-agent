# Phase 6: Database Integration (PostgreSQL + PGVector)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement persistent storage with PostgreSQL (SQLAlchemy async) and vector search (PGVector) for knowledge chunks.

**Architecture:** Repository pattern with async SQLAlchemy 2.0. Use create_async_engine with asyncpg driver. PGVector for semantic search with HNSW index.

**Tech Stack:** SQLAlchemy 2.0 (async), asyncpg, pgvector, pytest-asyncio

---

## File Structure

```
backend/app/
├── db/
│   ├── __init__.py
│   ├── database.py        # create_async_engine, get_session, Base
│   └── redis.py            # existing, no changes
├── models/
│   ├── __init__.py
│   ├── organization.py     # Create: Organization model
│   ├── department.py       # Create: Department model
│   ├── user.py             # Create: User model
│   └── knowledge.py         # Create: Knowledge + KnowledgeChunk models
└── schemas/
    ├── __init__.py
    ├── organization.py      # Create: Organization Pydantic schemas
    ├── department.py        # Create: Department Pydantic schemas
    ├── user.py              # Create: User Pydantic schemas
    └── knowledge.py         # Create: Knowledge Pydantic schemas

backend/tests/
├── unit/
│   └── test_models.py      # Create: Model unit tests
└── integration/
    └── test_repositories.py # Create: Repository integration tests
```

---

### Task 1: Database Configuration and Base

**Files:**
- Create: `backend/app/db/database.py`
- Modify: `backend/app/db/__init__.py`

- [ ] **Step 1: Write test for database connection**

```python
# tests/unit/test_database.py
import pytest

@pytest.mark.asyncio
async def test_create_async_engine():
    from app.db.database import create_async_engine
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    assert engine is not None
    await engine.dispose()

@pytest.mark.asyncio
async def test_get_session():
    from app.db.database import get_session, create_async_engine
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async for session in get_session(engine):
        assert session is not None
    await engine.dispose()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_database.py -v`
Expected: FAIL with "No module named 'app.db.database'"

- [ ] **Step 3: Write database.py**

```python
# backend/app/db/database.py
"""Async SQLAlchemy database configuration."""
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.config import settings


class Base(DeclarativeBase):
    """SQLAlchemy declarative base."""
    pass


def create_async_engine(url: str | None = None) -> AsyncEngine:
    """Create async engine with connection pooling."""
    database_url = url or settings.database_url
    return create_async_engine(
        database_url,
        echo=False,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
    )


async def get_session(engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """Get async session for dependency injection."""
    async with AsyncSession(engine) as session:
        yield session


async def init_db(engine: AsyncEngine) -> None:
    """Initialize database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db(engine: AsyncEngine) -> None:
    """Close database connections."""
    await engine.dispose()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_database.py -v`
Expected: PASS

- [ ] **Step 5: Update db/__init__.py**

```python
# backend/app/db/__init__.py
from app.db.database import Base, create_async_engine, get_session, init_db, close_db
from app.db.redis import redis_client

__all__ = ["Base", "create_async_engine", "get_session", "init_db", "close_db", "redis_client"]
```

- [ ] **Step 6: Run tests again**

Run: `pytest tests/unit/test_database.py -v`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add backend/app/db/database.py backend/app/db/__init__.py tests/unit/test_database.py
git commit -m "feat(db): add async SQLAlchemy database configuration"
```

---

### Task 2: Organization and Department Models

**Files:**
- Create: `backend/app/models/organization.py`
- Create: `backend/app/models/department.py`
- Modify: `backend/app/models/__init__.py`

- [ ] **Step 1: Write test for Organization model**

```python
# tests/unit/test_models.py
import pytest
from datetime import datetime
from uuid import uuid4

def test_organization_model_creation():
    from app.models.organization import Organization
    org = Organization(
        id=str(uuid4()),
        name="Test Org",
        slug="test-org",
        plan="free",
    )
    assert org.name == "Test Org"
    assert org.slug == "test-org"
    assert org.plan == "free"

def test_organization_model_timestamps():
    from app.models.organization import Organization
    org = Organization(name="Test", slug="test")
    assert org.created_at is not None
    assert org.updated_at is not None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_models.py::test_organization_model_creation -v`
Expected: FAIL with "No module named 'app.models.organization'"

- [ ] **Step 3: Write Organization model**

```python
# backend/app/models/organization.py
"""Organization model."""
from datetime import datetime, timezone

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class Organization(Base):
    """Organization model for multi-tenant support."""

    __tablename__ = "organizations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    plan: Mapped[str] = mapped_column(String(20), default="free")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    departments: Mapped[list["Department"]] = relationship(
        "Department", back_populates="organization", cascade="all, delete-orphan"
    )
    users: Mapped[list["User"]] = relationship(
        "User", back_populates="organization", cascade="all, delete-orphan"
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_models.py::test_organization_model_creation -v`
Expected: PASS

- [ ] **Step 5: Write Department model**

```python
# backend/app/models/department.py
"""Department model."""
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class Department(Base):
    """Department model for organizational hierarchy."""

    __tablename__ = "departments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    org_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    parent_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("departments.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization", back_populates="departments"
    )
    parent: Mapped["Department | None"] = relationship(
        "Department", remote_side="Department.id", back_populates="children"
    )
    children: Mapped[list["Department"]] = relationship(
        "Department", back_populates="parent"
    )
    users: Mapped[list["User"]] = relationship(
        "User", back_populates="department"
    )
```

- [ ] **Step 6: Run Department test**

Run: `pytest tests/unit/test_models.py -k "department" -v`
Expected: PASS (if tests exist) or skip

- [ ] **Step 7: Update models/__init__.py**

```python
# backend/app/models/__init__.py
from app.models.organization import Organization
from app.models.department import Department
from app.models.user import User
from app.models.knowledge import Knowledge, KnowledgeChunk

__all__ = ["Organization", "Department", "User", "Knowledge", "KnowledgeChunk"]
```

- [ ] **Step 8: Commit**

```bash
git add backend/app/models/organization.py backend/app/models/department.py backend/app/models/__init__.py tests/unit/test_models.py
git commit -m "feat(models): add Organization and Department models"
```

---

### Task 3: User Model

**Files:**
- Create: `backend/app/models/user.py`
- Modify: `backend/app/models/__init__.py`

- [ ] **Step 1: Write test for User model**

```python
# tests/unit/test_models.py (add to existing)
def test_user_model_creation():
    from app.models.user import User
    from uuid import uuid4
    org_id = str(uuid4())
    user = User(
        id=str(uuid4()),
        org_id=org_id,
        email="test@example.com",
        password_hash="$2b$12$...",
        role="member",
    )
    assert user.email == "test@example.com"
    assert user.role == "member"
    assert user.status == "active"

def test_user_totp_fields():
    from app.models.user import User
    user = User(email="test@example.com", password_hash="hash", org_id="org-1")
    assert user.totp_enabled is False
    assert user.totp_secret is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_models.py::test_user_model_creation -v`
Expected: FAIL with "No module named 'app.models.user'"

- [ ] **Step 3: Write User model**

```python
# backend/app/models/user.py
"""User model."""
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class User(Base):
    """User model with RBAC support."""

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    org_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    dept_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("departments.id", ondelete="SET NULL"), nullable=True
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), default="member")
    totp_secret: Mapped[str | None] = mapped_column(String(255), nullable=True)
    totp_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(String(20), default="active")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization", back_populates="users"
    )
    department: Mapped["Department | None"] = relationship(
        "Department", back_populates="users"
    )
    knowledge_items: Mapped[list["Knowledge"]] = relationship(
        "Knowledge", back_populates="owner"
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_models.py::test_user_model_creation -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/models/user.py tests/unit/test_models.py
git commit -m "feat(models): add User model with RBAC fields"
```

---

### Task 4: Knowledge and KnowledgeChunk Models (with PGVector)

**Files:**
- Create: `backend/app/models/knowledge.py`
- Modify: `backend/app/models/__init__.py`

- [ ] **Step 1: Write test for Knowledge model**

```python
# tests/unit/test_models.py (add to existing)
def test_knowledge_model_creation():
    from app.models.knowledge import Knowledge, KnowledgeStatus
    from uuid import uuid4
    user_id = str(uuid4())
    org_id = str(uuid4())
    knowledge = Knowledge(
        id=str(uuid4()),
        org_id=org_id,
        owner_id=user_id,
        title="Test Knowledge",
        content="Test content",
        status=KnowledgeStatus.DRAFT,
    )
    assert knowledge.title == "Test Knowledge"
    assert knowledge.status == KnowledgeStatus.DRAFT

def test_knowledge_chunk_creation():
    from app.models.knowledge import KnowledgeChunk
    chunk = KnowledgeChunk(
        knowledge_id="know-1",
        content="chunk content",
        embedding=[0.1] * 1536,
    )
    assert len(chunk.embedding) == 1536
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_models.py::test_knowledge_model_creation -v`
Expected: FAIL

- [ ] **Step 3: Write Knowledge model with PGVector**

```python
# backend/app/models/knowledge.py
"""Knowledge and KnowledgeChunk models with PGVector support."""
from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import DateTime, ForeignKey, String, Text, Index
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class KnowledgeStatus(str, Enum):
    """Knowledge workflow status."""
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    PUBLISHED = "published"


class Knowledge(Base):
    """Knowledge article model."""

    __tablename__ = "knowledge"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    org_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    owner_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default=KnowledgeStatus.DRAFT.value)
    reject_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    owner: Mapped["User"] = relationship("User", back_populates="knowledge_items")
    chunks: Mapped[list["KnowledgeChunk"]] = relationship(
        "KnowledgeChunk", back_populates="knowledge", cascade="all, delete-orphan"
    )


class KnowledgeChunk(Base):
    """Knowledge chunk with vector embedding for RAG."""

    __tablename__ = "knowledge_chunks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    knowledge_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("knowledge.id", ondelete="CASCADE"), nullable=False
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float]] = mapped_column(JSONB, nullable=False)
    metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    knowledge: Mapped["Knowledge"] = relationship(
        "Knowledge", back_populates="chunks"
    )

    # HNSW index for cosine distance vector search
    __table_args__ = (
        Index(
            "ix_knowledge_chunks_embedding",
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_models.py::test_knowledge_model_creation -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/models/knowledge.py tests/unit/test_models.py
git commit -m "feat(models): add Knowledge model with PGVector chunks"
```

---

### Task 5: Pydantic Schemas

**Files:**
- Create: `backend/app/schemas/organization.py`
- Create: `backend/app/schemas/department.py`
- Create: `backend/app/schemas/user.py`
- Create: `backend/app/schemas/knowledge.py`
- Modify: `backend/app/schemas/__init__.py`

- [ ] **Step 1: Write Organization schemas**

```python
# backend/app/schemas/organization.py
"""Organization Pydantic schemas."""
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class OrganizationBase(BaseModel):
    name: str
    slug: str
    plan: str = "free"


class OrganizationCreate(OrganizationBase):
    pass


class OrganizationUpdate(BaseModel):
    name: str | None = None
    plan: str | None = None


class OrganizationResponse(OrganizationBase):
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
```

- [ ] **Step 2: Write User schemas**

```python
# backend/app/schemas/user.py
"""User Pydantic schemas."""
from datetime import datetime
from pydantic import BaseModel, EmailStr, ConfigDict


class UserBase(BaseModel):
    email: EmailStr
    role: str = "member"


class UserCreate(UserBase):
    password: str
    org_id: str
    dept_id: str | None = None


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    role: str | None = None
    dept_id: str | None = None
    status: str | None = None


class UserResponse(UserBase):
    id: str
    org_id: str
    dept_id: str | None
    status: str
    totp_enabled: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserLogin(BaseModel):
    email: EmailStr
    password: str
    device_fingerprint: str | None = None
```

- [ ] **Step 3: Write Knowledge schemas**

```python
# backend/app/schemas/knowledge.py
"""Knowledge Pydantic schemas."""
from datetime import datetime
from pydantic import BaseModel, ConfigDict

from app.models.knowledge import KnowledgeStatus


class KnowledgeBase(BaseModel):
    title: str
    content: str


class KnowledgeCreate(KnowledgeBase):
    org_id: str


class KnowledgeUpdate(BaseModel):
    title: str | None = None
    content: str | None = None


class KnowledgeResponse(KnowledgeBase):
    id: str
    org_id: str
    owner_id: str
    status: str
    reject_reason: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class KnowledgeSubmit(BaseModel):
    pass  # No body needed, just state transition


class KnowledgeApprove(BaseModel):
    pass


class KnowledgeReject(BaseModel):
    reason: str


class KnowledgePublish(BaseModel):
    pass  # Admin only, just state transition
```

- [ ] **Step 4: Update schemas/__init__.py**

```python
# backend/app/schemas/__init__.py
from app.schemas.organization import (
    OrganizationCreate,
    OrganizationUpdate,
    OrganizationResponse,
)
from app.schemas.user import (
    UserCreate,
    UserUpdate,
    UserResponse,
    UserLogin,
)
from app.schemas.knowledge import (
    KnowledgeCreate,
    KnowledgeUpdate,
    KnowledgeResponse,
    KnowledgeSubmit,
    KnowledgeApprove,
    KnowledgeReject,
    KnowledgePublish,
)

__all__ = [
    "OrganizationCreate", "OrganizationUpdate", "OrganizationResponse",
    "UserCreate", "UserUpdate", "UserResponse", "UserLogin",
    "KnowledgeCreate", "KnowledgeUpdate", "KnowledgeResponse",
    "KnowledgeSubmit", "KnowledgeApprove", "KnowledgeReject", "KnowledgePublish",
]
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/schemas/organization.py backend/app/schemas/user.py backend/app/schemas/knowledge.py backend/app/schemas/__init__.py
git commit -m "feat(schemas): add Pydantic schemas for API"
```

---

### Task 6: Integration Tests with PostgreSQL

**Files:**
- Create: `backend/tests/integration/test_repositories.py`
- Modify: `backend/tests/integration/conftest.py`

- [ ] **Step 1: Write conftest for async DB**

```python
# backend/tests/integration/conftest.py
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from app.db.database import Base


@pytest_asyncio.fixture
async def db_engine():
    """Create async engine for testing."""
    engine = create_async_engine(
        "postgresql+asyncpg://postgres:postgres@localhost:5433/center_multi_agent_test",
        echo=False,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()
```

- [ ] **Step 2: Write repository integration tests**

```python
# backend/tests/integration/test_repositories.py
import pytest
from uuid import uuid4

from app.models.organization import Organization
from app.models.user import User
from app.models.knowledge import Knowledge, KnowledgeStatus


@pytest.mark.asyncio
async def test_create_organization(db_engine):
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import AsyncSession

    async with AsyncSession(db_engine) as session:
        org = Organization(
            id=str(uuid4()),
            name="Test Organization",
            slug="test-org-" + str(uuid4())[:8],
        )
        session.add(org)
        await session.commit()

        result = await session.execute(
            select(Organization).where(Organization.name == "Test Organization")
        )
        found = result.scalar_one_or_none()
        assert found is not None
        assert found.name == "Test Organization"


@pytest.mark.asyncio
async def test_create_user_with_organization(db_engine):
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import AsyncSession

    async with AsyncSession(db_engine) as session:
        org_id = str(uuid4())
        org = Organization(id=org_id, name="Test Org", slug="test-" + str(uuid4())[:8])
        session.add(org)

        user = User(
            id=str(uuid4()),
            org_id=org_id,
            email=f"test-{uuid4()}@example.com",
            password_hash="$2b$12$hashedpassword",
            role="member",
        )
        session.add(user)
        await session.commit()

        result = await session.execute(
            select(User).where(User.email == user.email)
        )
        found = result.scalar_one_or_none()
        assert found is not None
        assert found.role == "member"
```

- [ ] **Step 3: Run integration tests**

Run: `REDIS_URL="redis://localhost:6380/0" pytest tests/integration/test_repositories.py -v`
Expected: PASS (requires PostgreSQL running)

- [ ] **Step 4: Commit**

```bash
git add backend/tests/integration/conftest.py backend/tests/integration/test_repositories.py
git commit -m "test(integration): add database repository tests"
```

---

## Summary

| Task | Description | Files |
|------|-------------|-------|
| 1 | Database configuration | database.py |
| 2 | Organization & Department models | organization.py, department.py |
| 3 | User model | user.py |
| 4 | Knowledge & KnowledgeChunk (PGVector) | knowledge.py |
| 5 | Pydantic schemas | schemas/*.py |
| 6 | Integration tests | test_repositories.py |

**Total:** 6 tasks, ~60 steps

---

## Plan Complete

Plan saved to `docs/superpowers/plans/2026-05-07-database-integration.md`.

**Two execution options:**

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?