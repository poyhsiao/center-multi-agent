"""Knowledge Pydantic schemas."""
from datetime import datetime
from pydantic import BaseModel, ConfigDict


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
    pass


class KnowledgeApprove(BaseModel):
    pass


class KnowledgeReject(BaseModel):
    reason: str


class KnowledgePublish(BaseModel):
    pass
