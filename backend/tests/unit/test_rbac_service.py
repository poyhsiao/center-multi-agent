"""Unit tests for RBAC Service - Business logic for role and permission management."""
import pytest
from unittest.mock import MagicMock, AsyncMock
from app.core.rbac import (
    Role,
    Permission,
    ADMIN,
    MEMBER,
    VIEWER,
    PERMISSIONS,
)
from app.services.rbac_service import RbacService


class TestRbacService:
    """Test suite for RbacService."""

    @pytest.fixture
    def rbac_service(self):
        """Create RbacService instance."""
        return RbacService()

    @pytest.fixture
    def mock_user(self):
        """Create a mock user object."""
        user = MagicMock()
        user.id = "user-123"
        user.org_id = "org-456"
        user.role = "admin"
        return user

    @pytest.fixture
    def mock_member_user(self):
        """Create a mock member user."""
        user = MagicMock()
        user.id = "user-456"
        user.org_id = "org-456"
        user.role = "member"
        return user

    @pytest.fixture
    def mock_viewer_user(self):
        """Create a mock viewer user."""
        user = MagicMock()
        user.id = "user-789"
        user.org_id = "org-456"
        user.role = "viewer"
        return user

    # check_user_permission tests
    @pytest.mark.asyncio
    async def test_check_user_permission_admin_has_all(self, rbac_service, mock_user):
        """Admin user should have all permissions."""
        # Admin has all permissions
        assert await rbac_service.check_user_permission(
            mock_user, Permission.USERS_READ
        ) is True
        assert await rbac_service.check_user_permission(
            mock_user, Permission.USERS_WRITE
        ) is True
        assert await rbac_service.check_user_permission(
            mock_user, Permission.DEPT_WRITE
        ) is True
        assert await rbac_service.check_user_permission(
            mock_user, Permission.ORG_SETTINGS
        ) is True

    @pytest.mark.asyncio
    async def test_check_user_permission_member_has_subset(self, rbac_service, mock_member_user):
        """Member user should have limited permissions."""
        # Member has USERS_READ
        assert await rbac_service.check_user_permission(
            mock_member_user, Permission.USERS_READ
        ) is True
        # Member does NOT have ORG_SETTINGS
        assert await rbac_service.check_user_permission(
            mock_member_user, Permission.ORG_SETTINGS
        ) is False

    @pytest.mark.asyncio
    async def test_check_user_permission_viewer_read_only(self, rbac_service, mock_viewer_user):
        """Viewer user should have read-only permissions."""
        # Viewer has USERS_READ
        assert await rbac_service.check_user_permission(
            mock_viewer_user, Permission.USERS_READ
        ) is True
        # Viewer does NOT have USERS_WRITE
        assert await rbac_service.check_user_permission(
            mock_viewer_user, Permission.USERS_WRITE
        ) is False
        # Viewer does NOT have DEPT_WRITE
        assert await rbac_service.check_user_permission(
            mock_viewer_user, Permission.DEPT_WRITE
        ) is False

    # check_user_role tests
    @pytest.mark.asyncio
    async def test_check_user_role_exact_match(self, rbac_service, mock_user):
        """User with exact role should pass."""
        assert await rbac_service.check_user_role(mock_user, Role.ADMIN) is True

    @pytest.mark.asyncio
    async def test_check_user_role_higher_passes(self, rbac_service, mock_user):
        """Admin should satisfy MEMBER requirement."""
        assert await rbac_service.check_user_role(mock_user, Role.MEMBER) is True
        assert await rbac_service.check_user_role(mock_user, Role.VIEWER) is True

    @pytest.mark.asyncio
    async def test_check_user_role_member_fails_admin(self, rbac_service, mock_member_user):
        """Member should not satisfy ADMIN requirement."""
        assert await rbac_service.check_user_role(mock_member_user, Role.ADMIN) is False

    @pytest.mark.asyncio
    async def test_check_user_role_viewer_fails_member(self, rbac_service, mock_viewer_user):
        """Viewer should not satisfy MEMBER requirement."""
        assert await rbac_service.check_user_role(mock_viewer_user, Role.MEMBER) is False

    # get_user_permissions tests
    @pytest.mark.asyncio
    async def test_get_user_permissions_admin(self, rbac_service, mock_user):
        """Admin should have all permissions."""
        perms = await rbac_service.get_user_permissions(mock_user)
        admin_perms = PERMISSIONS[Role.ADMIN]
        assert perms == admin_perms

    @pytest.mark.asyncio
    async def test_get_user_permissions_member(self, rbac_service, mock_member_user):
        """Member should have member permissions."""
        perms = await rbac_service.get_user_permissions(mock_member_user)
        member_perms = PERMISSIONS[Role.MEMBER]
        assert perms == member_perms

    @pytest.mark.asyncio
    async def test_get_user_permissions_viewer(self, rbac_service, mock_viewer_user):
        """Viewer should have viewer permissions."""
        perms = await rbac_service.get_user_permissions(mock_viewer_user)
        viewer_perms = PERMISSIONS[Role.VIEWER]
        assert perms == viewer_perms

    # is_org_admin tests
    @pytest.mark.asyncio
    async def test_is_org_admin_true(self, rbac_service, mock_user):
        """Admin of the org should return True."""
        mock_user.role = "admin"
        result = await rbac_service.is_org_admin(mock_user, "org-456")
        assert result is True

    @pytest.mark.asyncio
    async def test_is_org_admin_member_not_admin(self, rbac_service, mock_member_user):
        """Member is not org admin."""
        mock_member_user.role = "member"
        result = await rbac_service.is_org_admin(mock_member_user, "org-456")
        assert result is False

    @pytest.mark.asyncio
    async def test_is_org_admin_different_org(self, rbac_service, mock_user):
        """User checking admin status for different org should fail."""
        mock_user.role = "admin"
        result = await rbac_service.is_org_admin(mock_user, "org-different")
        assert result is False

    # can_access_resource tests
    @pytest.mark.asyncio
    async def test_can_access_resource_same_org(self, rbac_service, mock_user):
        """User should access resource in their org."""
        result = await rbac_service.can_access_resource(mock_user, "org-456")
        assert result is True

    @pytest.mark.asyncio
    async def test_can_access_resource_different_org(self, rbac_service, mock_user):
        """Admin bypasses org check - can access resources in different orgs."""
        result = await rbac_service.can_access_resource(mock_user, "org-other")
        assert result is True

    @pytest.mark.asyncio
    async def test_can_access_resource_member_same_org(self, rbac_service, mock_member_user):
        """Member should access resource in their org."""
        result = await rbac_service.can_access_resource(mock_member_user, "org-456")
        assert result is True

    # Edge cases
    @pytest.mark.asyncio
    async def test_unknown_role_gets_no_permissions(self, rbac_service):
        """User with unknown role should have no permissions."""
        unknown_user = MagicMock()
        unknown_user.role = "unknown_role"
        perms = await rbac_service.get_user_permissions(unknown_user)
        assert perms == frozenset()

    @pytest.mark.asyncio
    async def test_unknown_role_cannot_access(self, rbac_service):
        """User with unknown role should not pass role checks."""
        unknown_user = MagicMock()
        unknown_user.role = "unknown_role"
        assert await rbac_service.check_user_role(unknown_user, Role.ADMIN) is False
        assert await rbac_service.check_user_permission(
            unknown_user, Permission.USERS_READ
        ) is False