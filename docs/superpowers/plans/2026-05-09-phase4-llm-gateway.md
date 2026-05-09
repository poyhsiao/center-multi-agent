# Phase 4: LLM Gateway + Knowledge Service Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement Model Router with failover, RAG Pipeline with PGVector, Knowledge state machine (draft→pending_review→approved→published), and SSE notification events.

**Architecture:** LLM Gateway provides model routing with failover chains. Knowledge Service manages document lifecycle. SSE notifications emit events on state changes.

**Tech Stack:** FastAPI, OpenAI SDK, Anthropic SDK, PGVector, SSE, Redis

---

## File Structure

```
backend/app/services/llm_gateway.py           # Model router (CREATE)
backend/app/services/knowledge_service.py     # State machine (EXISTS - expand)
backend/app/services/embedding_service.py    # Embedding generation (CREATE)
backend/app/core/notification.py              # SSE notifications (EXISTS)
backend/app/db/vector.py                      # PGVector operations (CREATE)
backend/app/api/v1/rag.py                     # RAG endpoint (EXISTS - expand)
backend/app/api/v1/knowledge.py                # Knowledge endpoints (EXISTS)
backend/tests/unit/test_llm_gateway.py         # CREATE
backend/tests/unit/test_knowledge_service.py   # EXISTS - expand
backend/tests/integration/test_rag_pipeline.py # CREATE
backend/tests/bdd/features/C-knowledge-contribution.feature  # EXISTS
```

---

## Current Implementation Status

| Component | Status | Notes |
|-----------|--------|-------|
| `KnowledgeStatus` enum | ✅ EXISTS | draft/pending_review/approved/published/rejected |
| `Knowledge` dataclass | ✅ EXISTS | Has state machine methods |
| `KnowledgeChunk` dataclass | ✅ EXISTS | With embedding field |
| RAG `/query` endpoint | ✅ EXISTS | Has Permission.KNOWLEDGE_READ |
| `llm_gateway.py` | ❌ MISSING | Need to create |
| Model Router | ❌ MISSING | Need to create |
| Model Failover chains | ❌ MISSING | Need to create |
| PGVector schema | ❌ MISSING | Need to create |
| Embedding generation | ❌ MISSING | Need to create |
| SSE notification events | ⚠️ PARTIAL | notification.py exists |
| Unit tests for llm | ❌ MISSING | Need to create |

---

## Task 1: LLM Gateway Model Router

**Files:**
- Create: `backend/app/services/llm_gateway.py`
- Test: `backend/tests/unit/test_llm_gateway.py`

- [ ] **Step 1: Write ModelRouter class**

```python
# backend/app/services/llm_gateway.py
"""LLM Gateway - Model Router with Failover."""
from enum import Enum
from dataclasses import dataclass
from typing import Optional
import structlog

logger = structlog.get_logger()


class TaskType(str, Enum):
    """Task classification for model selection."""
    COMPLEX_REASONING = "complex_reasoning"
    GENERAL = "general"
    CREATIVE = "creative"
    BATCH = "batch"


@dataclass
class ModelConfig:
    """Model configuration."""
    name: str
    provider: str
    cost_tier: str  # high, medium, low
    context_window: int
    supports_reasoning: bool = False


class LLMGateway:
    """Model router with failover support."""

    MODELS = {
        "gpt-4o": ModelConfig(
            name="gpt-4o",
            provider="openai",
            cost_tier="high",
            context_window=128000,
            supports_reasoning=True,
        ),
        "gpt-4o-mini": ModelConfig(
            name="gpt-4o-mini",
            provider="openai",
            cost_tier="medium",
            context_window=128000,
            supports_reasoning=False,
        ),
        "claude-3-5-sonnet": ModelConfig(
            name="claude-3-5-sonnet",
            provider="anthropic",
            cost_tier="high",
            context_window=200000,
            supports_reasoning=True,
        ),
        "claude-3-haiku": ModelConfig(
            name="claude-3-haiku",
            provider="anthropic",
            cost_tier="low",
            context_window=200000,
            supports_reasoning=False,
        ),
        "gemini-2-0-flash": ModelConfig(
            name="gemini-2-0-flash",
            provider="google",
            cost_tier="low",
            context_window=1000000,
            supports_reasoning=False,
        ),
    }

    FAILOVER_CHAINS = {
        TaskType.COMPLEX_REASONING: ["gpt-4o", "claude-3-5-sonnet"],
        TaskType.GENERAL: ["gpt-4o-mini", "gemini-2-0-flash"],
        TaskType.CREATIVE: ["claude-3-5-sonnet", "gpt-4o"],
        TaskType.BATCH: ["gemini-2-0-flash", "claude-3-haiku"],
    }

    def __init__(self):
        self.logger = logger

    def select_model(self, task_type: TaskType) -> ModelConfig:
        """Select primary model for task type."""
        chain = self.FAILOVER_CHAINS.get(task_type, [TaskType.GENERAL])
        model_name = chain[0]
        return self.MODELS[model_name]

    def get_failover_chain(self, task_type: TaskType) -> list[ModelConfig]:
        """Get full failover chain for task type."""
        chain = self.FAILOVER_CHAINS.get(task_type, ["gpt-4o-mini"])
        return [self.MODELS[name] for name in chain]

    async def generate_with_failover(
        self,
        task_type: TaskType,
        prompt: str,
        **kwargs,
    ) -> str:
        """Generate with failover: try primary, fall back on failure."""
        chain = self.get_failover_chain(task_type)
        last_error = None

        for model in chain:
            try:
                result = await self._call_model(model, prompt, **kwargs)
                self.logger.info(f"model_success", model=model.name, task_type=task_type.value)
                return result
            except Exception as e:
                self.logger.warning(f"model_failed", model=model.name, error=str(e))
                last_error = e
                continue

        raise RuntimeError(f"All models in chain failed. Last error: {last_error}")

    async def _call_model(self, model: ModelConfig, prompt: str, **kwargs) -> str:
        """Call specific model."""
        if model.provider == "openai":
            from openai import AsyncOpenAI
            client = AsyncOpenAI()
            response = await client.chat.completions.create(
                model=model.name,
                messages=[{"role": "user", "content": prompt}],
                **kwargs,
            )
            return response.choices[0].message.content

        elif model.provider == "anthropic":
            from anthropic import AsyncAnthropic
            client = AsyncAnthropic()
            response = await client.messages.create(
                model=model.name,
                max_tokens=kwargs.get("max_tokens", 1024),
                messages=[{"role": "user", "content": prompt}],
            )
            return response.content[0].text

        elif model.provider == "google":
            import google.generativeai as genai
            model_gemini = genai.GenerativeModel(model.name)
            response = await model_gemini.generate_content(prompt)
            return response.text

        raise ValueError(f"Unknown provider: {model.provider}")
```

- [ ] **Step 2: Write model router unit tests**

```python
# backend/tests/unit/test_llm_gateway.py
import pytest

def test_select_model_complex_reasoning():
    """Complex reasoning task selects GPT-4o."""
    from app.services.llm_gateway import LLMGateway, TaskType

    gateway = LLMGateway()
    model = gateway.select_model(TaskType.COMPLEX_REASONING)

    assert model.name == "gpt-4o"
    assert model.supports_reasoning == True

def test_select_model_general():
    """General task selects GPT-4o-mini."""
    from app.services.llm_gateway import LLMGateway, TaskType

    gateway = LLMGateway()
    model = gateway.select_model(TaskType.GENERAL)

    assert model.name == "gpt-4o-mini"
    assert model.cost_tier == "medium"

def test_get_failover_chain():
    """Failover chain returns all models in priority order."""
    from app.services.llm_gateway import LLMGateway, TaskType

    gateway = LLMGateway()
    chain = gateway.get_failover_chain(TaskType.COMPLEX_REASONING)

    assert len(chain) == 2
    assert chain[0].name == "gpt-4o"
    assert chain[1].name == "claude-3-5-sonnet"

def test_model_config_attributes():
    """Model configs have correct attributes."""
    from app.services.llm_gateway import LLMGateway

    gateway = LLMGateway()
    gpt4o = gateway.MODELS["gpt-4o"]

    assert gpt4o.provider == "openai"
    assert gpt4o.context_window == 128000
    assert gpt4o.supports_reasoning == True
```

- [ ] **Step 3: Run tests**

Run: `cd backend && python -m pytest tests/unit/test_llm_gateway.py -v`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add backend/app/services/llm_gateway.py backend/tests/unit/test_llm_gateway.py
git commit -m "feat(llm): add model router with failover chains"
```

---

## Task 2: Knowledge Service State Machine Tests

**Files:**
- Modify: `backend/tests/unit/test_knowledge_service.py`
- Review: `backend/app/services/knowledge_service.py`

- [ ] **Step 1: Review existing knowledge_service.py**

Run: `cat backend/app/services/knowledge_service.py`

- [ ] **Step 2: Add state machine unit tests**

```python
# Add to backend/tests/unit/test_knowledge_service.py

def test_knowledge_state_draft_to_pending():
    """Draft can transition to pending_review."""
    from app.services.knowledge_service import Knowledge, KnowledgeStatus

    k = Knowledge(title="Test", content="Content")
    assert k.status == KnowledgeStatus.DRAFT

    k.submit_for_review()
    assert k.status == KnowledgeStatus.PENDING_REVIEW

def test_knowledge_state_pending_to_approved():
    """Pending can be approved."""
    from app.services.knowledge_service import Knowledge, KnowledgeStatus

    k = Knowledge(title="Test", content="Content", status=KnowledgeStatus.PENDING_REVIEW)
    k.approve()
    assert k.status == KnowledgeStatus.APPROVED

def test_knowledge_state_pending_to_rejected():
    """Pending can be rejected with reason."""
    from app.services.knowledge_service import Knowledge, KnowledgeStatus

    k = Knowledge(title="Test", content="Content", status=KnowledgeStatus.PENDING_REVIEW)
    k.reject("Needs more detail")
    assert k.status == KnowledgeStatus.REJECTED
    assert k.rejection_reason == "Needs more detail"

def test_knowledge_state_approved_to_published():
    """Approved can be published."""
    from app.services.knowledge_service import Knowledge, KnowledgeStatus

    k = Knowledge(title="Test", content="Content", status=KnowledgeStatus.APPROVED)
    k.publish()
    assert k.status == KnowledgeStatus.PUBLISHED

def test_knowledge_state_rejected_to_draft():
    """Rejected can return to draft."""
    from app.services.knowledge_service import Knowledge, KnowledgeStatus

    k = Knowledge(title="Test", content="Content", status=KnowledgeStatus.REJECTED)
    k.revise()
    assert k.status == KnowledgeStatus.DRAFT
    assert k.rejection_reason is None

def test_knowledge_state_invalid_transition():
    """Invalid state transitions raise ValueError."""
    from app.services.knowledge_service import Knowledge, KnowledgeStatus

    k = Knowledge(title="Test", content="Content", status=KnowledgeStatus.PUBLISHED)
    with pytest.raises(ValueError):
        k.submit_for_review()

def test_knowledge_state_approved_cannot_go_back():
    """Approved cannot go back to pending."""
    from app.services.knowledge_service import Knowledge, KnowledgeStatus

    k = Knowledge(title="Test", content="Content", status=KnowledgeStatus.APPROVED)
    with pytest.raises(ValueError):
        k.submit_for_review()
```

- [ ] **Step 3: Run tests**

Run: `cd backend && python -m pytest tests/unit/test_knowledge_service.py -v`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add backend/tests/unit/test_knowledge_service.py
git commit -m "test: expand knowledge service state machine tests"
```

---

## Task 3: PGVector RAG Integration

**Files:**
- Create: `backend/app/db/vector.py`
- Create: `backend/app/services/embedding_service.py`
- Create: `backend/tests/integration/test_rag_pipeline.py`

- [ ] **Step 1: Create embedding service**

```python
# backend/app/services/embedding_service.py
"""Embedding service for vector generation."""
from openai import AsyncOpenAI


class EmbeddingService:
    """Generate embeddings using OpenAI or other providers."""

    def __init__(self, model: str = "text-embedding-3-small"):
        self.model = model
        self.client = AsyncOpenAI()

    async def generate(self, text: str) -> list[float]:
        """Generate embedding for text."""
        response = await self.client.embeddings.create(
            model=self.model,
            input=text,
        )
        return response.data[0].embedding
```

- [ ] **Step 2: Create PGVector operations**

```python
# backend/app/db/vector.py
"""PGVector operations for RAG pipeline."""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import structlog

logger = structlog.get_logger()


class VectorStore:
    """PGVector operations for knowledge chunk storage and retrieval."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_chunk(
        self,
        knowledge_id: str,
        content: str,
        embedding: list[float],
        metadata: dict | None = None,
    ) -> str:
        """Create a knowledge chunk with vector embedding."""
        import uuid
        chunk_id = f"chunk-{uuid.uuid4()}"

        await self.session.execute(
            text("""
                INSERT INTO knowledge_chunks (id, knowledge_id, content, embedding, metadata)
                VALUES (:id, :knowledge_id, :content, (:embedding)::vector, :metadata)
            """),
            {
                "id": chunk_id,
                "knowledge_id": knowledge_id,
                "content": content,
                "embedding": str(embedding),
                "metadata": str(metadata) if metadata else None,
            }
        )
        await self.session.commit()
        return chunk_id

    async def similarity_search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        org_id: str | None = None,
    ) -> list[dict]:
        """Search for similar knowledge chunks."""
        filter_clause = ""
        if org_id:
            filter_clause = "AND k.org_id = :org_id"

        result = await self.session.execute(
            text(f"""
                SELECT
                    c.id,
                    c.content,
                    c.knowledge_id,
                    c.metadata,
                    1 - (c.embedding <=> (:embedding)::vector) as similarity
                FROM knowledge_chunks c
                JOIN knowledge k ON c.knowledge_id = k.id
                WHERE k.status = 'published'
                {filter_clause}
                ORDER BY c.embedding <=> (:embedding)::vector
                LIMIT :top_k
            """),
            {
                "embedding": str(query_embedding),
                "top_k": top_k,
                "org_id": org_id,
            }
        )

        rows = result.fetchall()
        return [
            {
                "id": row[0],
                "content": row[1],
                "knowledge_id": row[2],
                "metadata": row[3],
                "score": float(row[4]),
            }
            for row in rows
        ]

    async def delete_chunks_by_knowledge(self, knowledge_id: str) -> None:
        """Delete all chunks for a knowledge document."""
        await self.session.execute(
            text("DELETE FROM knowledge_chunks WHERE knowledge_id = :knowledge_id"),
            {"knowledge_id": knowledge_id}
        )
        await self.session.commit()
```

- [ ] **Step 3: Write RAG pipeline integration tests**

```python
# backend/tests/integration/test_rag_pipeline.py
import pytest

@pytest.mark.asyncio
async def test_knowledge_approval_workflow():
    """Knowledge approval transitions state correctly."""
    from app.services.knowledge_service import Knowledge, KnowledgeStatus

    k = Knowledge(title="Test", content="Content")
    k.submit_for_review()
    assert k.status == KnowledgeStatus.PENDING_REVIEW

    k.approve()
    assert k.status == KnowledgeStatus.APPROVED

@pytest.mark.asyncio
async def test_failover_chain_order():
    """Model failover tries models in correct order."""
    from app.services.llm_gateway import LLMGateway, TaskType

    gateway = LLMGateway()
    chain = gateway.get_failover_chain(TaskType.COMPLEX_REASONING)

    assert chain[0].name == "gpt-4o"
    assert chain[1].name == "claude-3-5-sonnet"
```

- [ ] **Step 4: Commit**

```bash
git add backend/app/db/vector.py backend/app/services/embedding_service.py backend/tests/integration/test_rag_pipeline.py
git commit -m "feat(rag): add PGVector operations and embedding service"
```

---

## Task 4: RAG Endpoint Enhancement

**Files:**
- Modify: `backend/app/api/v1/rag.py`
- Test: `backend/tests/unit/test_rag_api.py`

- [ ] **Step 1: Review existing RAG endpoint**

Run: `cat backend/app/api/v1/rag.py`

- [ ] **Step 2: Expand RAG endpoint with embedding and LLM generation**

```python
# backend/app/api/v1/rag.py (update existing)
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_permission, CurrentUser
from app.core.rbac import Permission
from app.services.llm_gateway import LLMGateway, TaskType
from app.db.vector import VectorStore
from app.services.embedding_service import EmbeddingService

router = APIRouter(prefix="/rag", tags=["rag"])


class QueryRequest(BaseModel):
    query: str
    top_k: int = 5
    org_id: str = None


class ChunkResult(BaseModel):
    content: str
    knowledge_id: str
    score: float


class QueryResponse(BaseModel):
    query: str
    results: list[ChunkResult]
    context: str = None
    generated_response: str = None


@router.post("/query", response_model=QueryResponse, dependencies=[Depends(require_permission(Permission.KNOWLEDGE_READ))])
async def query_knowledge(
    request: QueryRequest,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> QueryResponse:
    """Query knowledge base with RAG for relevant context."""
    embedding_service = EmbeddingService()
    query_vector = await embedding_service.generate(request.query)

    vector_store = VectorStore(db)
    chunks = await vector_store.similarity_search(
        query_embedding=query_vector,
        top_k=request.top_k,
        org_id=request.org_id or user.tenant_id,
    )

    context = "\n\n".join([c["content"] for c in chunks])

    llm = LLMGateway()
    prompt = f"Context:\n{context}\n\nQuestion: {request.query}"
    response = await llm.generate_with_failover(TaskType.GENERAL, prompt)

    return QueryResponse(
        query=request.query,
        results=[ChunkResult(**c) for c in chunks],
        context=context,
        generated_response=response,
    )
```

- [ ] **Step 3: Write RAG API tests**

```python
# backend/tests/unit/test_rag_api.py
import pytest

def test_rag_query_requires_read_permission():
    """RAG query endpoint requires knowledge:read permission."""
    # Test that unauthenticated requests are rejected
    pass
```

- [ ] **Step 4: Commit**

```bash
git add backend/app/api/v1/rag.py
git commit -m "feat(rag): enhance RAG endpoint with embedding and LLM generation"
```

---

## Verification

1. **LLM Gateway tests**: `cd backend && python -m pytest tests/unit/test_llm_gateway.py -v`
2. **Knowledge service tests**: `cd backend && python -m pytest tests/unit/test_knowledge_service.py -v`
3. **RAG pipeline tests**: `cd backend && python -m pytest tests/integration/test_rag_pipeline.py -v`
4. **BDD Feature C**: `cd backend && python -m behave tests/bdd/features/C-knowledge-contribution.feature --format=pretty`

**Expected Results:** All PASS

**Spec Coverage:**
- [x] Model router selection — Task 1
- [x] Model failover chain — Task 1
- [x] Embedding generation — Task 3
- [x] Vector similarity search — Task 3
- [x] Knowledge state machine — Task 2
- [x] RAG query with context — Task 4
- [x] Feature C BDD scenarios — Verification