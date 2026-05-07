"""Unit tests for database models."""
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


def test_organization_default_timestamps():
    from app.models.organization import Organization
    org = Organization(name="Test", slug="test-" + str(uuid4())[:8])
    assert org.created_at is not None
    assert org.updated_at is not None


def test_department_model_creation():
    from app.models.department import Department
    dept = Department(
        id=str(uuid4()),
        org_id=str(uuid4()),
        name="Engineering",
    )
    assert dept.name == "Engineering"


def test_user_model_creation():
    from app.models.user import User
    org_id = str(uuid4())
    user = User(
        id=str(uuid4()),
        org_id=org_id,
        email="test@example.com",
        password_hash="$2b$12$...",
        role="member",
        status="active",
        totp_enabled=False,
    )
    assert user.email == "test@example.com"
    assert user.role == "member"
    assert user.status == "active"
    assert user.totp_enabled is False


def test_user_totp_fields():
    from app.models.user import User
    user = User(email="test@example.com", password_hash="hash", org_id="org-1", totp_enabled=False, totp_secret=None)
    assert user.totp_enabled is False
    assert user.totp_secret is None


def test_knowledge_status_enum():
    """Test KnowledgeStatus enum values."""
    from app.models.knowledge import KnowledgeStatus

    assert KnowledgeStatus.DRAFT.value == "draft"
    assert KnowledgeStatus.PENDING_REVIEW.value == "pending_review"
    assert KnowledgeStatus.APPROVED.value == "approved"
    assert KnowledgeStatus.REJECTED.value == "rejected"
    assert KnowledgeStatus.PUBLISHED.value == "published"


def test_knowledge_model_creation():
    """Test Knowledge model instantiation."""
    from app.models.knowledge import Knowledge, KnowledgeStatus
    from sqlalchemy.orm import configure_mappers
    configure_mappers()

    user_id = str(uuid4())
    org_id = str(uuid4())
    knowledge = Knowledge(
        id=str(uuid4()),
        org_id=org_id,
        owner_id=user_id,
        title="Test Knowledge",
        content="Test content",
        status=KnowledgeStatus.DRAFT.value,
    )
    assert knowledge.title == "Test Knowledge"
    assert knowledge.status == KnowledgeStatus.DRAFT.value


def test_knowledge_chunk_embedding():
    """Test KnowledgeChunk with PGVector embedding."""
    from app.models.knowledge import KnowledgeChunk

    chunk = KnowledgeChunk(
        id=str(uuid4()),
        knowledge_id="know-1",
        content="chunk content",
        embedding=[0.1] * 1536,
    )
    assert len(chunk.embedding) == 1536
    assert chunk.knowledge_id == "know-1"
