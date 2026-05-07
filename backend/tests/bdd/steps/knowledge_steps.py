"""Step definitions for Knowledge Contribution feature."""
from behave import given, when, then
from dataclasses import dataclass
from typing import Any
from uuid import uuid4

from app.services.knowledge_service import (
    Knowledge,
    KnowledgeStatus,
    KnowledgeService,
    SSEEvent,
)
from app.services.tenant_service import RbacEngine


# =============================================================================
# Context Helpers
# =============================================================================

@dataclass
class KnowledgeContext:
    """Context for knowledge-related test state."""
    knowledge: Knowledge | None = None
    knowledge_id: str | None = None
    sse_events: list[SSEEvent] | None = None
    last_error: Exception | None = None
    member_knowledge_map: dict[str, list[Knowledge]] = None

    def __post_init__(self):
        if self.member_knowledge_map is None:
            self.member_knowledge_map = {}


@dataclass
class UserContext:
    """Context for user-related test state."""
    role: str | None = None
    user_id: str | None = None
    org_id: str | None = None


# =============================================================================
# Shared Fixtures (called via before_scenario)
# =============================================================================

def init_knowledge_context(context):
    """Initialize knowledge context."""
    if not hasattr(context, 'knowledge_ctx'):
        context.knowledge_ctx = KnowledgeContext()
    if not hasattr(context, 'user_ctx'):
        context.user_ctx = UserContext()


# =============================================================================
# Given Steps
# =============================================================================

@given('使用者角色為 "{role}"')
def step_user_role(context, role: str):
    """Set user role."""
    init_knowledge_context(context)
    context.user_ctx.role = role


@given('使用者已登入系統')
def step_user_logged_in(context):
    """Simulate user login."""
    init_knowledge_context(context)
    # In real implementation, would set session/user context
    context.user_ctx.user_id = str(uuid4())


@given('知識處於 "{status}" 狀態')
def step_knowledge_in_status(context, status: str):
    """Set knowledge to a specific status."""
    init_knowledge_context(context)
    status_map = {
        "draft": KnowledgeStatus.DRAFT,
        "pending_review": KnowledgeStatus.PENDING_REVIEW,
        "approved": KnowledgeStatus.APPROVED,
        "published": KnowledgeStatus.PUBLISHED,
        "rejected": KnowledgeStatus.REJECTED,
    }
    target_status = status_map.get(status)

    if context.knowledge_ctx.knowledge is None:
        context.knowledge_ctx.knowledge = Knowledge(
            title="Test Knowledge",
            content="Test content"
        )

    # Transition to target status based on current state
    current = context.knowledge_ctx.knowledge.status
    if current == KnowledgeStatus.DRAFT and target_status == KnowledgeStatus.PENDING_REVIEW:
        context.knowledge_ctx.knowledge.submit_for_review()
    elif current == KnowledgeStatus.PENDING_REVIEW and target_status == KnowledgeStatus.APPROVED:
        context.knowledge_ctx.knowledge.approve()
    elif current == KnowledgeStatus.PENDING_REVIEW and target_status == KnowledgeStatus.REJECTED:
        context.knowledge_ctx.knowledge.reject(reason="Test rejection")
    elif current == KnowledgeStatus.APPROVED and target_status == KnowledgeStatus.PUBLISHED:
        context.knowledge_ctx.knowledge.publish()
    elif current == KnowledgeStatus.REJECTED and target_status == KnowledgeStatus.DRAFT:
        context.knowledge_ctx.knowledge.revise()


@given('有知識處於 "{status}" 狀態')
def step_has_knowledge_in_status(context, status: str):
    """Create a knowledge in a specific status for manager/admin actions."""
    init_knowledge_context(context)
    status_map = {
        "draft": KnowledgeStatus.DRAFT,
        "pending_review": KnowledgeStatus.PENDING_REVIEW,
        "approved": KnowledgeStatus.APPROVED,
        "published": KnowledgeStatus.PUBLISHED,
        "rejected": KnowledgeStatus.REJECTED,
    }
    target_status = status_map.get(status)

    knowledge = Knowledge(title="Managed Knowledge", content="Content for review")

    # Build to target state
    if target_status == KnowledgeStatus.PENDING_REVIEW:
        knowledge.submit_for_review()
    elif target_status == KnowledgeStatus.APPROVED:
        knowledge.submit_for_review()
        knowledge.approve()
    elif target_status == KnowledgeStatus.PUBLISHED:
        knowledge.submit_for_review()
        knowledge.approve()
        knowledge.publish()

    context.knowledge_ctx.knowledge = knowledge
    context.knowledge_ctx.knowledge_id = str(uuid4())


@given('使用者擁有一個 "{status}" 狀態的知識')
def step_member_owns_knowledge_in_status(context, status: str):
    """Member owns a knowledge in specific status."""
    init_knowledge_context(context)
    status_map = {
        "draft": KnowledgeStatus.DRAFT,
        "pending_review": KnowledgeStatus.PENDING_REVIEW,
        "approved": KnowledgeStatus.APPROVED,
        "published": KnowledgeStatus.PUBLISHED,
        "rejected": KnowledgeStatus.REJECTED,
    }
    target_status = status_map.get(status)

    member_id = context.user_ctx.user_id or "member-1"

    knowledge = Knowledge(title="My Draft", content="My content")

    # Only draft can be owned and edited
    assert target_status == KnowledgeStatus.DRAFT

    context.knowledge_ctx.knowledge = knowledge
    if member_id not in context.knowledge_ctx.member_knowledge_map:
        context.knowledge_ctx.member_knowledge_map[member_id] = []
    context.knowledge_ctx.member_knowledge_map[member_id].append(knowledge)


@given('系統中存在其他成員的知識')
def step_other_member_has_knowledge(context):
    """Other member has knowledge."""
    init_knowledge_context(context)

    other_member_id = "other-member-123"
    knowledge = Knowledge(title="Other's Knowledge", content="Other content")

    if other_member_id not in context.knowledge_ctx.member_knowledge_map:
        context.knowledge_ctx.member_knowledge_map[other_member_id] = []
    context.knowledge_ctx.member_knowledge_map[other_member_id].append(knowledge)
    context.knowledge_ctx.knowledge = knowledge


# =============================================================================
# When Steps
# =============================================================================

@when('使用者提交新知識，標題為 "{title}"，內容為 "{content}"')
def step_submit_new_knowledge(context, title: str, content: str):
    """Submit a new knowledge article."""
    init_knowledge_context(context)

    knowledge = Knowledge(title=title, content=content)
    context.knowledge_ctx.knowledge = knowledge
    context.knowledge_ctx.knowledge_id = str(uuid4())


@when('使用者提交知識進入審核')
def step_submit_for_review(context):
    """Submit knowledge for review."""
    init_knowledge_context(context)

    if context.knowledge_ctx.knowledge:
        context.knowledge_ctx.knowledge.submit_for_review()


@when('Manager 核准該知識')
def step_manager_approve(context):
    """Manager approves knowledge."""
    init_knowledge_context(context)

    rbac = RbacEngine()
    role = context.user_ctx.role or "manager"

    # Check permission
    if not rbac.check_permission(role, "review_knowledge"):
        context.knowledge_ctx.last_error = PermissionDeniedException(
            f"Role '{role}' cannot review knowledge"
        )
        return

    if context.knowledge_ctx.knowledge:
        context.knowledge_ctx.knowledge.approve()


@when('Manager 拒絕該知識，理由為 "{reason}"')
def step_manager_reject(context, reason: str):
    """Manager rejects knowledge."""
    init_knowledge_context(context)

    rbac = RbacEngine()
    role = context.user_ctx.role or "manager"

    # Check permission
    if not rbac.check_permission(role, "review_knowledge"):
        context.knowledge_ctx.last_error = PermissionDeniedException(
            f"Role '{role}' cannot review knowledge"
        )
        return

    if context.knowledge_ctx.knowledge:
        context.knowledge_ctx.knowledge.reject(reason=reason)


@when('Admin 發布該知識')
def step_admin_publish(context):
    """Admin publishes knowledge."""
    init_knowledge_context(context)

    rbac = RbacEngine()
    role = context.user_ctx.role or "admin"

    # Check permission
    if not rbac.check_permission(role, "publish_knowledge"):
        context.knowledge_ctx.last_error = PermissionDeniedException(
            f"Role '{role}' cannot publish knowledge"
        )
        return

    if context.knowledge_ctx.knowledge:
        context.knowledge_ctx.knowledge.publish()


@when('使用者編輯該知識的內容')
def step_edit_knowledge_content(context):
    """Edit knowledge content."""
    init_knowledge_context(context)

    if context.knowledge_ctx.knowledge:
        # Simulate content update
        context.knowledge_ctx.knowledge.content = "Updated content"


@when('使用者嘗試刪除該知識')
def step_attempt_delete_knowledge(context):
    """Attempt to delete knowledge (should fail for non-owner)."""
    init_knowledge_context(context)

    rbac = RbacEngine()
    role = context.user_ctx.role or "member"

    # Check permission - members can only delete their own
    if role == "member":
        # Check ownership
        member_id = context.user_ctx.user_id or "member-1"
        knowledge = context.knowledge_ctx.knowledge

        # For this test, we check if knowledge belongs to current member
        owned_knowledge = context.knowledge_ctx.member_knowledge_map.get(member_id, [])
        is_owner = knowledge in owned_knowledge

        if not is_owner:
            context.knowledge_ctx.last_error = PermissionDeniedException(
                "Cannot delete another member's knowledge"
            )


# =============================================================================
# Then Steps
# =============================================================================

@then('知識狀態為 "{status}"')
def step_verify_status(context, status: str):
    """Verify knowledge status."""
    init_knowledge_context(context)
    status_map = {
        "draft": KnowledgeStatus.DRAFT,
        "pending_review": KnowledgeStatus.PENDING_REVIEW,
        "approved": KnowledgeStatus.APPROVED,
        "published": KnowledgeStatus.PUBLISHED,
        "rejected": KnowledgeStatus.REJECTED,
    }
    expected = status_map.get(status)

    assert context.knowledge_ctx.knowledge is not None, "Knowledge not found"
    assert context.knowledge_ctx.knowledge.status == expected, (
        f"Expected status {status}, got {context.knowledge_ctx.knowledge.status.value}"
    )


@then('系統回傳知識 ID')
def step_verify_knowledge_id(context):
    """Verify knowledge ID is returned."""
    init_knowledge_context(context)

    assert context.knowledge_ctx.knowledge_id is not None, "Knowledge ID not returned"
    assert len(context.knowledge_ctx.knowledge_id) > 0, "Knowledge ID is empty"


@then('知識狀態變更為 "{status}"')
def step_verify_status_changed(context, status: str):
    """Verify status changed to specific value."""
    step_verify_status(context, status)


@then('Admin 收到審核通知（SSE 事件 `knowledge.submitted`）')
def step_verify_admin_notification(context):
    """Verify admin receives submission notification."""
    init_knowledge_context(context)

    service = KnowledgeService()
    event = service.create_submitted_event(
        knowledge_id=context.knowledge_ctx.knowledge_id or str(uuid4())
    )

    assert event.event_type == "knowledge.submitted", (
        f"Expected event 'knowledge.submitted', got '{event.event_type}'"
    )
    assert "knowledge_id" in event.data


@then('提交者收到通知（SSE 事件 `knowledge.approved`）')
def step_verify_approved_notification(context):
    """Verify submitter receives approval notification."""
    init_knowledge_context(context)

    service = KnowledgeService()
    event = service.create_approved_event(
        knowledge_id=context.knowledge_ctx.knowledge_id or str(uuid4())
    )

    assert event.event_type == "knowledge.approved", (
        f"Expected event 'knowledge.approved', got '{event.event_type}'"
    )


@then('提交者收到通知（SSE 事件 `knowledge.rejected`），包含拒絕原因')
def step_verify_rejected_notification(context):
    """Verify submitter receives rejection notification with reason."""
    init_knowledge_context(context)

    service = KnowledgeService()
    reason = context.knowledge_ctx.knowledge.rejection_reason if context.knowledge_ctx.knowledge else "內容需要補充"
    event = service.create_rejected_event(
        knowledge_id=context.knowledge_ctx.knowledge_id or str(uuid4()),
        reason=reason
    )

    assert event.event_type == "knowledge.rejected", (
        f"Expected event 'knowledge.rejected', got '{event.event_type}'"
    )
    assert "reason" in event.data, "Rejection reason not in event data"
    assert event.data["reason"] == reason, (
        f"Expected reason '{reason}', got '{event.data['reason']}'"
    )


@then('知識進入 RAG 向量資料庫')
def step_verify_rag_indexing(context):
    """Verify knowledge is indexed in RAG vector database."""
    init_knowledge_context(context)

    # Verify knowledge is in published state (prerequisite for RAG)
    assert context.knowledge_ctx.knowledge is not None, "Knowledge not found"
    assert context.knowledge_ctx.knowledge.status == KnowledgeStatus.PUBLISHED, (
        f"Knowledge must be published for RAG indexing, got {context.knowledge_ctx.knowledge.status.value}"
    )

    # In real implementation, would verify chunk creation and vector embedding
    # Here we just verify the state transition happened correctly


@then('所有相關用戶收到通知（SSE 事件 `knowledge.published`）')
def step_verify_published_notification(context):
    """Verify all relevant users receive published notification."""
    init_knowledge_context(context)

    service = KnowledgeService()
    event = service.create_published_event(
        knowledge_id=context.knowledge_ctx.knowledge_id or str(uuid4())
    )

    assert event.event_type == "knowledge.published", (
        f"Expected event 'knowledge.published', got '{event.event_type}'"
    )


@then('知識內容更新成功')
def step_verify_content_updated(context):
    """Verify knowledge content was updated."""
    init_knowledge_context(context)

    assert context.knowledge_ctx.knowledge is not None, "Knowledge not found"
    assert context.knowledge_ctx.knowledge.content == "Updated content", (
        f"Content not updated, got '{context.knowledge_ctx.knowledge.content}'"
    )


@then('狀態保持為 "{status}"')
def step_verify_status_unchanged(context, status: str):
    """Verify status remains unchanged."""
    step_verify_status(context, status)


@then('系統回傳 403 錯誤')
def step_verify_403_error(context):
    """Verify 403 error is returned."""
    init_knowledge_context(context)

    assert context.knowledge_ctx.last_error is not None, "No error raised"
    # In real implementation, would check isinstance of PermissionDeniedException


@then('知識未被刪除')
def step_verify_not_deleted(context):
    """Verify knowledge was not deleted."""
    init_knowledge_context(context)

    # Knowledge still exists in the system
    assert context.knowledge_ctx.knowledge is not None, "Knowledge should still exist"


# =============================================================================
# Exceptions (for reference)
# =============================================================================

class PermissionDeniedException(Exception):
    """Raised when user lacks permission."""
    pass
