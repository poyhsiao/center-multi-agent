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