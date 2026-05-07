"""Department model for organizational hierarchy."""
from __future__ import annotations

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
        "Department", remote_side="Department.id", back_populates="children", foreign_keys=[parent_id]
    )
    children: Mapped[list["Department"]] = relationship(
        "Department", back_populates="parent", foreign_keys=[parent_id]
    )
    users: Mapped[list["User"]] = relationship(
        "User", back_populates="department"
    )