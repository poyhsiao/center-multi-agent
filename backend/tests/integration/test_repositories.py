"""Integration tests for database repositories using PostgreSQL."""
import pytest
from uuid import uuid4

from sqlalchemy import select

from app.models.organization import Organization
from app.models.department import Department
from app.models.knowledge import Knowledge, KnowledgeChunk, KnowledgeStatus


@pytest.mark.asyncio
async def test_create_organization(db_session):
    """Test creating an organization in the database."""
    org = Organization(
        id=str(uuid4()),
        name="Test Organization",
        slug="test-" + str(uuid4())[:8],
    )
    db_session.add(org)
    await db_session.commit()

    result = await db_session.execute(
        select(Organization).where(Organization.name == "Test Organization")
    )
    found = result.scalar_one_or_none()
    assert found is not None
    assert found.name == "Test Organization"
    assert found.plan == "free"


@pytest.mark.asyncio
async def test_create_department_with_org(db_session):
    """Test creating a department with organization relationship."""
    org = Organization(
        id=str(uuid4()),
        name="Test Org",
        slug="test-" + str(uuid4())[:8],
    )
    db_session.add(org)
    await db_session.flush()

    dept = Department(
        id=str(uuid4()),
        org_id=org.id,
        name="Engineering",
    )
    db_session.add(dept)
    await db_session.commit()

    result = await db_session.execute(
        select(Department).where(Department.name == "Engineering")
    )
    found = result.scalar_one_or_none()
    assert found is not None
    assert found.organization.name == "Test Org"


@pytest.mark.asyncio
async def test_organization_departments_relationship(db_session):
    """Test organization-department one-to-many relationship."""
    org = Organization(
        id=str(uuid4()),
        name="Test Org",
        slug="test-" + str(uuid4())[:8],
    )
    db_session.add(org)
    await db_session.flush()

    dept1 = Department(id=str(uuid4()), org_id=org.id, name="Dept 1")
    dept2 = Department(id=str(uuid4()), org_id=org.id, name="Dept 2")
    db_session.add_all([dept1, dept2])
    await db_session.commit()

    result = await db_session.execute(
        select(Organization).where(Organization.id == org.id)
    )
    found_org = result.scalar_one()
    assert len(found_org.departments) == 2


@pytest.mark.asyncio
async def test_create_knowledge(db_session):
    """Test creating a knowledge article."""
    org = Organization(
        id=str(uuid4()),
        name="Test Org",
        slug="test-" + str(uuid4())[:8],
    )
    db_session.add(org)
    await db_session.flush()

    knowledge = Knowledge(
        id=str(uuid4()),
        org_id=org.id,
        owner_id=str(uuid4()),
        title="Test Article",
        content="This is test content for the knowledge article.",
        status=KnowledgeStatus.DRAFT.value,
    )
    db_session.add(knowledge)
    await db_session.commit()

    result = await db_session.execute(
        select(Knowledge).where(Knowledge.title == "Test Article")
    )
    found = result.scalar_one_or_none()
    assert found is not None
    assert found.status == KnowledgeStatus.DRAFT.value


@pytest.mark.asyncio
async def test_create_knowledge_chunk(db_session):
    """Test creating a knowledge chunk with embedding."""
    org = Organization(
        id=str(uuid4()),
        name="Test Org",
        slug="test-" + str(uuid4())[:8],
    )
    db_session.add(org)
    await db_session.flush()

    knowledge = Knowledge(
        id=str(uuid4()),
        org_id=org.id,
        owner_id=str(uuid4()),
        title="RAG Article",
        content="Content for vector search testing.",
        status=KnowledgeStatus.PUBLISHED.value,
    )
    db_session.add(knowledge)
    await db_session.flush()

    chunk = KnowledgeChunk(
        id=str(uuid4()),
        knowledge_id=knowledge.id,
        content="Chunk 1: Content for vector search testing.",
        embedding=[0.1] * 1536,
        meta={"chunk_index": 0},
    )
    db_session.add(chunk)
    await db_session.commit()

    result = await db_session.execute(
        select(KnowledgeChunk).where(KnowledgeChunk.knowledge_id == knowledge.id)
    )
    found = result.scalar_one_or_none()
    assert found is not None
    assert len(found.embedding) == 1536


@pytest.mark.asyncio
async def test_knowledge_cascade_delete(db_session):
    """Test that deleting knowledge deletes its chunks."""
    org = Organization(
        id=str(uuid4()),
        name="Test Org",
        slug="test-" + str(uuid4())[:8],
    )
    db_session.add(org)
    await db_session.flush()

    knowledge = Knowledge(
        id=str(uuid4()),
        org_id=org.id,
        owner_id=str(uuid4()),
        title="To Be Deleted",
        content="This article will be deleted.",
    )
    db_session.add(knowledge)
    await db_session.flush()

    chunk = KnowledgeChunk(
        id=str(uuid4()),
        knowledge_id=knowledge.id,
        content="Orphaned chunk",
        embedding=[0.1] * 1536,
    )
    db_session.add(chunk)
    await db_session.commit()

    knowledge_id = knowledge.id
    await db_session.delete(knowledge)
    await db_session.commit()

    result = await db_session.execute(
        select(KnowledgeChunk).where(KnowledgeChunk.knowledge_id == knowledge_id)
    )
    found = result.scalar_one_or_none()
    assert found is None