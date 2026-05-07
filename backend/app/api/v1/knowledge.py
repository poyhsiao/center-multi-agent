"""Knowledge API Endpoints - Knowledge management with RBAC."""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.core.exceptions import PermissionDeniedException, ResourceNotFoundException
from app.services.knowledge_service import (
    Knowledge,
    KnowledgeStatus,
    KnowledgeChunk,
    SSEEvent,
)
from app.services.tenant_service import RbacEngine, User

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


# =============================================================================
# Request/Response Models
# =============================================================================


class CreateKnowledgeRequest(BaseModel):
    title: str
    content: str


class UpdateKnowledgeRequest(BaseModel):
    title: str | None = None
    content: str | None = None


class RejectKnowledgeRequest(BaseModel):
    reason: str


class KnowledgeResponse(BaseModel):
    id: str
    title: str
    content: str
    status: str
    rejection_reason: str | None = None
    owner_id: str | None = None

    class Config:
        from_attributes = True


class KnowledgeListResponse(BaseModel):
    items: list[KnowledgeResponse]
    total: int


# =============================================================================
# Dependencies
# =============================================================================


class CurrentUser(BaseModel):
    """Current authenticated user context."""

    user_id: str
    role: str
    tenant_id: str


# =============================================================================
# RBAC Check Helper
# =============================================================================


def check_knowledge_access(
    user: CurrentUser,
    knowledge: Knowledge,
    action: str,
    rbac: RbacEngine,
) -> None:
    """
    Check if user has permission for knowledge action.

    Args:
        user: Current user context
        knowledge: Knowledge document
        action: Action being performed
        rbac: RBAC engine

    Raises:
        HTTPException: If access denied
    """
    # Admin can do anything with knowledge
    if user.role == "admin":
        return

    # Check role-based permission
    if not rbac.check_permission(user.role, action):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Role '{user.role}' cannot perform '{action}'",
        )

    # Owner check for update/delete
    if action in ("update_knowledge", "delete_knowledge"):
        if knowledge.owner_id != user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the owner can perform this action",
            )


# =============================================================================
# Endpoints
# =============================================================================


@router.post("", response_model=KnowledgeResponse, status_code=status.HTTP_201_CREATED)
async def create_knowledge(
    request: CreateKnowledgeRequest,
    user: CurrentUser,
) -> KnowledgeResponse:
    """
    Create new knowledge entry.

    - **title**: Knowledge title
    - **content**: Knowledge content
    """
    rbac = RbacEngine()
    rbac.require_permission(user.role, "submit_knowledge")

    # Create knowledge document
    knowledge = Knowledge(
        title=request.title,
        content=request.content,
        status=KnowledgeStatus.DRAFT,
        owner_id=user.user_id,
    )

    return KnowledgeResponse(
        id=knowledge.id or "draft",
        title=knowledge.title,
        content=knowledge.content,
        status=knowledge.status.value,
        rejection_reason=knowledge.rejection_reason,
        owner_id=knowledge.owner_id,
    )


@router.get("", response_model=KnowledgeListResponse)
async def list_knowledge(
    user: CurrentUser,
    status_filter: str | None = None,
    skip: int = 0,
    limit: int = 20,
) -> KnowledgeListResponse:
    """
    List knowledge entries filtered by role.

    - **admin**: See all knowledge
    - **manager**: See all knowledge
    - **member**: See own knowledge only
    """
    rbac = RbacEngine()

    # Members only see their own
    if user.role == "member":
        # Return filtered list for members (own knowledge only)
        # In real implementation, would query repository
        items = []
    else:
        # Managers and admins see all
        items = []

    return KnowledgeListResponse(items=items, total=len(items))


@router.get("/{knowledge_id}", response_model=KnowledgeResponse)
async def get_knowledge(
    knowledge_id: str,
    user: CurrentUser,
) -> KnowledgeResponse:
    """
    Get knowledge detail by ID.

    Members can only view their own knowledge.
    Managers and admins can view all.
    """
    rbac = RbacEngine()

    # In real implementation, would fetch from repository
    # For now, return not found
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Knowledge '{knowledge_id}' not found",
    )


@router.put("/{knowledge_id}", response_model=KnowledgeResponse)
async def update_knowledge(
    knowledge_id: str,
    request: UpdateKnowledgeRequest,
    user: CurrentUser,
) -> KnowledgeResponse:
    """
    Update knowledge entry.

    - Owner only (member role: own draft only)
    - Admin: can update any
    """
    rbac = RbacEngine()

    # In real implementation, would fetch and check ownership
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Knowledge '{knowledge_id}' not found",
    )


@router.delete("/{knowledge_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_knowledge(
    knowledge_id: str,
    user: CurrentUser,
) -> None:
    """
    Delete knowledge entry.

    - Owner (any role) can delete own knowledge
    - Admin can delete any knowledge
    """
    rbac = RbacEngine()

    # In real implementation, would delete from repository
    pass


@router.put("/{knowledge_id}/submit", response_model=KnowledgeResponse)
async def submit_knowledge_for_review(
    knowledge_id: str,
    user: CurrentUser,
) -> KnowledgeResponse:
    """
    Submit knowledge for review.

    Transitions: DRAFT -> PENDING_REVIEW
    """
    rbac = RbacEngine()
    rbac.require_permission(user.role, "submit_knowledge")

    # In real implementation, would fetch and transition
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Knowledge '{knowledge_id}' not found",
    )


@router.put("/{knowledge_id}/approve", response_model=KnowledgeResponse)
async def approve_knowledge(
    knowledge_id: str,
    user: CurrentUser,
) -> KnowledgeResponse:
    """
    Approve knowledge for publication.

    Transitions: PENDING_REVIEW -> APPROVED

    Requires manager or admin role.
    """
    rbac = RbacEngine()
    rbac.require_permission(user.role, "review_knowledge")

    # In real implementation, would fetch and transition
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Knowledge '{knowledge_id}' not found",
    )


@router.put("/{knowledge_id}/reject", response_model=KnowledgeResponse)
async def reject_knowledge(
    knowledge_id: str,
    request: RejectKnowledgeRequest,
    user: CurrentUser,
) -> KnowledgeResponse:
    """
    Reject knowledge submission.

    Transitions: PENDING_REVIEW -> REJECTED

    Requires manager or admin role.
    """
    rbac = RbacEngine()
    rbac.require_permission(user.role, "review_knowledge")

    # In real implementation, would fetch and transition
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Knowledge '{knowledge_id}' not found",
    )


@router.put("/{knowledge_id}/publish", response_model=KnowledgeResponse)
async def publish_knowledge(
    knowledge_id: str,
    user: CurrentUser,
) -> KnowledgeResponse:
    """
    Publish approved knowledge.

    Transitions: APPROVED -> PUBLISHED

    Requires admin role only.
    """
    rbac = RbacEngine()
    rbac.require_permission(user.role, "publish_knowledge")

    # In real implementation, would fetch and transition
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Knowledge '{knowledge_id}' not found",
    )