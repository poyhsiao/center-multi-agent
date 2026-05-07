"""Unit tests for Tenant Service - Organization, Department, User CRUD and RBAC."""
import pytest
from uuid import uuid4
from unittest.mock import MagicMock, patch


class TestOrganizationCrud:
    """Test Organization CRUD operations."""

    def test_create_organization_success(self):
        """Test successful organization creation."""
        from app.services.tenant_service import OrganizationService

        service = OrganizationService()
        org_data = {
            "name": "Test Org",
            "slug": "test-org",
            "plan": "free"
        }

        with patch.object(service, '_generate_id', return_value=str(uuid4())):
            with patch.object(service.repo, 'save') as mock_save:
                mock_save.return_value = {
                    "id": str(uuid4()),
                    **org_data,
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-01T00:00:00Z"
                }
                result = service.create_org(org_data)

        assert result["name"] == "Test Org"
        assert result["slug"] == "test-org"
        assert result["plan"] == "free"
        mock_save.assert_called_once()

    def test_get_organization_by_id(self):
        """Test retrieving organization by ID."""
        from app.services.tenant_service import OrganizationService

        service = OrganizationService()
        org_id = str(uuid4())
        mock_org = {
            "id": org_id,
            "name": "Test Org",
            "slug": "test-org",
            "plan": "pro",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        }

        with patch.object(service.repo, 'find_by_id', return_value=mock_org):
            result = service.get_org(org_id)

        assert result["id"] == org_id
        assert result["name"] == "Test Org"

    def test_get_organization_not_found(self):
        """Test retrieving non-existent organization."""
        from app.services.tenant_service import OrganizationService
        from app.core.exceptions import ResourceNotFoundException

        service = OrganizationService()
        org_id = str(uuid4())

        with patch.object(service.repo, 'find_by_id', return_value=None):
            with pytest.raises(ResourceNotFoundException):
                service.get_org(org_id)

    def test_update_organization(self):
        """Test updating organization details."""
        from app.services.tenant_service import OrganizationService

        service = OrganizationService()
        org_id = str(uuid4())
        mock_org = {
            "id": org_id,
            "name": "Old Name",
            "slug": "old-slug",
            "plan": "free",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        }
        updated_org = {**mock_org, "name": "New Name", "plan": "pro"}

        with patch.object(service.repo, 'find_by_id', return_value=mock_org):
            with patch.object(service.repo, 'save', return_value=updated_org) as mock_save:
                result = service.update_org(org_id, {"name": "New Name", "plan": "pro"})

        assert result["name"] == "New Name"
        assert result["plan"] == "pro"
        mock_save.assert_called_once()

    def test_delete_organization(self):
        """Test deleting organization."""
        from app.services.tenant_service import OrganizationService

        service = OrganizationService()
        org_id = str(uuid4())
        mock_org = {"id": org_id, "name": "Test Org"}

        with patch.object(service.repo, 'find_by_id', return_value=mock_org):
            with patch.object(service.repo, 'delete', return_value=True) as mock_delete:
                result = service.delete_org(org_id)

        assert result is True
        mock_delete.assert_called_once_with(org_id)


class TestDepartmentCrud:
    """Test Department CRUD with hierarchy support."""

    def test_create_department_success(self):
        """Test successful department creation."""
        from app.services.tenant_service import DepartmentService

        service = DepartmentService()
        dept_data = {
            "org_id": str(uuid4()),
            "name": "Engineering",
            "parent_id": None
        }

        with patch.object(service.repo, 'save') as mock_save:
            mock_save.return_value = {
                "id": str(uuid4()),
                **dept_data,
                "created_at": "2024-01-01T00:00:00Z"
            }
            result = service.create_dept(dept_data)

        assert result["name"] == "Engineering"
        assert result["parent_id"] is None
        mock_save.assert_called_once()

    def test_create_child_department(self):
        """Test creating child department."""
        from app.services.tenant_service import DepartmentService

        service = DepartmentService()
        parent_id = str(uuid4())
        org_id = str(uuid4())
        dept_data = {
            "org_id": org_id,
            "name": "Backend",
            "parent_id": parent_id
        }

        with patch.object(service.repo, 'save') as mock_save:
            mock_save.return_value = {
                "id": str(uuid4()),
                **dept_data,
                "created_at": "2024-01-01T00:00:00Z"
            }
            result = service.create_dept(dept_data)

        assert result["parent_id"] == parent_id

    def test_get_dept_tree(self):
        """Test getting department tree structure."""
        from app.services.tenant_service import DepartmentService

        service = DepartmentService()
        org_id = str(uuid4())

        mock_depts = [
            {"id": "dept-1", "org_id": org_id, "name": "Engineering", "parent_id": None},
            {"id": "dept-2", "org_id": org_id, "name": "Backend", "parent_id": "dept-1"},
            {"id": "dept-3", "org_id": org_id, "name": "Frontend", "parent_id": "dept-1"},
            {"id": "dept-4", "org_id": org_id, "name": "Sales", "parent_id": None},
        ]

        with patch.object(service.repo, 'find_by_org_id', return_value=mock_depts):
            tree = service.get_dept_tree(org_id)

        assert len(tree) == 2  # Two root departments
        engineering = next(d for d in tree if d["name"] == "Engineering")
        assert len(engineering["children"]) == 2
        assert engineering["children"][0]["name"] == "Backend"

    def test_delete_department_with_children(self):
        """Test deleting department with children re-assigns them."""
        from app.services.tenant_service import DepartmentService

        service = DepartmentService()
        org_id = str(uuid4())
        parent_id = str(uuid4())
        child_id = str(uuid4())

        parent_dept = {"id": parent_id, "org_id": org_id, "name": "Engineering", "parent_id": None}
        child_dept = {"id": child_id, "org_id": org_id, "name": "Backend", "parent_id": parent_id}

        with patch.object(service.repo, 'find_by_id', return_value=parent_dept):
            with patch.object(service.repo, 'find_children', return_value=[child_dept]):
                with patch.object(service.repo, 'save', return_value=child_dept) as mock_save:
                    with patch.object(service.repo, 'delete', return_value=True):
                        result = service.delete_dept(parent_id)

        # Child should be re-assigned to no parent
        assert mock_save.called
        # Delete should be called for parent
        assert result is True


class TestUserCrud:
    """Test User CRUD operations."""

    def test_create_user_success(self):
        """Test successful user creation."""
        from app.services.tenant_service import UserService
        from app.services.auth_service import hash_password

        service = UserService()
        org_id = str(uuid4())
        user_data = {
            "org_id": org_id,
            "email": "test@example.com",
            "password": "SecurePass123!",
            "role": "member"
        }

        with patch.object(service.repo, 'find_by_email', return_value=None):
            with patch.object(service.repo, 'save') as mock_save:
                mock_save.return_value = {
                    "id": str(uuid4()),
                    "org_id": org_id,
                    "email": "test@example.com",
                    "role": "member",
                    "status": "active",
                    "password_hash": hash_password("SecurePass123!"),
                    "totp_enabled": False,
                    "created_at": "2024-01-01T00:00:00Z"
                }
                result = service.create_user(user_data)

        assert result["email"] == "test@example.com"
        assert result["role"] == "member"
        assert result["status"] == "active"
        mock_save.assert_called_once()

    def test_create_user_duplicate_email(self):
        """Test creating user with duplicate email fails."""
        from app.services.tenant_service import UserService
        from app.core.exceptions import DuplicateResourceException

        service = UserService()
        existing_user = {"id": str(uuid4()), "email": "test@example.com"}

        with patch.object(service.repo, 'find_by_email', return_value=existing_user):
            with pytest.raises(DuplicateResourceException):
                service.create_user({
                    "org_id": str(uuid4()),
                    "email": "test@example.com",
                    "password": "SecurePass123!",
                    "role": "member"
                })

    def test_get_user_by_id(self):
        """Test retrieving user by ID."""
        from app.services.tenant_service import UserService

        service = UserService()
        user_id = str(uuid4())
        mock_user = {
            "id": user_id,
            "org_id": str(uuid4()),
            "email": "test@example.com",
            "role": "admin",
            "status": "active"
        }

        with patch.object(service.repo, 'find_by_id', return_value=mock_user):
            result = service.get_user(user_id)

        assert result["id"] == user_id
        assert result["email"] == "test@example.com"

    def test_update_user_role(self):
        """Test updating user role."""
        from app.services.tenant_service import UserService

        service = UserService()
        user_id = str(uuid4())
        mock_user = {
            "id": user_id,
            "org_id": str(uuid4()),
            "email": "test@example.com",
            "role": "member",
            "status": "active"
        }

        with patch.object(service.repo, 'find_by_id', return_value=mock_user):
            with patch.object(service.repo, 'save', return_value={**mock_user, "role": "manager"}) as mock_save:
                result = service.update_user(user_id, {"role": "manager"})

        assert result["role"] == "manager"
        mock_save.assert_called_once()

    def test_suspend_user(self):
        """Test suspending a user."""
        from app.services.tenant_service import UserService

        service = UserService()
        user_id = str(uuid4())
        mock_user = {
            "id": user_id,
            "org_id": str(uuid4()),
            "email": "test@example.com",
            "role": "member",
            "status": "active"
        }

        with patch.object(service.repo, 'find_by_id', return_value=mock_user):
            with patch.object(service.repo, 'save', return_value={**mock_user, "status": "suspended"}) as mock_save:
                result = service.update_user(user_id, {"status": "suspended"})

        assert result["status"] == "suspended"


class TestRbacEngine:
    """Test RBAC permission checking engine."""

    def test_admin_can_manage_org_settings(self):
        """Test admin role can manage organization settings."""
        from app.services.tenant_service import RbacEngine

        engine = RbacEngine()
        result = engine.check_permission("admin", "manage_org_settings")
        assert result is True

    def test_manager_cannot_manage_org_settings(self):
        """Test manager role cannot manage organization settings."""
        from app.services.tenant_service import RbacEngine

        engine = RbacEngine()
        result = engine.check_permission("manager", "manage_org_settings")
        assert result is False

    def test_member_cannot_manage_org_settings(self):
        """Test member role cannot manage organization settings."""
        from app.services.tenant_service import RbacEngine

        engine = RbacEngine()
        result = engine.check_permission("member", "manage_org_settings")
        assert result is False

    def test_admin_can_manage_departments(self):
        """Test admin role can manage departments."""
        from app.services.tenant_service import RbacEngine

        engine = RbacEngine()
        result = engine.check_permission("admin", "manage_departments")
        assert result is True

    def test_manager_can_manage_departments(self):
        """Test manager role can manage departments."""
        from app.services.tenant_service import RbacEngine
        engine = RbacEngine()
        result = engine.check_permission("manager", "manage_departments")
        assert result is True

    def test_member_cannot_manage_departments(self):
        """Test member role cannot manage departments."""
        from app.services.tenant_service import RbacEngine

        engine = RbacEngine()
        result = engine.check_permission("member", "manage_departments")
        assert result is False

    def test_admin_can_manage_members(self):
        """Test admin role can manage members."""
        from app.services.tenant_service import RbacEngine

        engine = RbacEngine()
        result = engine.check_permission("admin", "manage_members")
        assert result is True

    def test_manager_can_manage_members(self):
        """Test manager role can manage members."""
        from app.services.tenant_service import RbacEngine

        engine = RbacEngine()
        result = engine.check_permission("manager", "manage_members")
        assert result is True

    def test_member_cannot_manage_members(self):
        """Test member role cannot manage members."""
        from app.services.tenant_service import RbacEngine

        engine = RbacEngine()
        result = engine.check_permission("member", "manage_members")
        assert result is False

    def test_admin_can_invite_members(self):
        """Test admin role can invite members."""
        from app.services.tenant_service import RbacEngine

        engine = RbacEngine()
        result = engine.check_permission("admin", "invite_members")
        assert result is True

    def test_manager_can_invite_members(self):
        """Test manager role can invite members."""
        from app.services.tenant_service import RbacEngine

        engine = RbacEngine()
        result = engine.check_permission("manager", "invite_members")
        assert result is True

    def test_member_cannot_invite_members(self):
        """Test member role cannot invite members."""
        from app.services.tenant_service import RbacEngine

        engine = RbacEngine()
        result = engine.check_permission("member", "invite_members")
        assert result is False

    def test_all_roles_can_submit_knowledge(self):
        """Test all roles can submit knowledge."""
        from app.services.tenant_service import RbacEngine

        engine = RbacEngine()
        assert engine.check_permission("admin", "submit_knowledge") is True
        assert engine.check_permission("manager", "submit_knowledge") is True
        assert engine.check_permission("member", "submit_knowledge") is True

    def test_admin_can_review_knowledge(self):
        """Test admin role can review knowledge."""
        from app.services.tenant_service import RbacEngine

        engine = RbacEngine()
        result = engine.check_permission("admin", "review_knowledge")
        assert result is True

    def test_manager_can_review_knowledge(self):
        """Test manager role can review knowledge."""
        from app.services.tenant_service import RbacEngine

        engine = RbacEngine()
        result = engine.check_permission("manager", "review_knowledge")
        assert result is True

    def test_member_cannot_review_knowledge(self):
        """Test member role cannot review knowledge."""
        from app.services.tenant_service import RbacEngine

        engine = RbacEngine()
        result = engine.check_permission("member", "review_knowledge")
        assert result is False

    def test_only_admin_can_publish_knowledge(self):
        """Test only admin role can publish knowledge."""
        from app.services.tenant_service import RbacEngine

        engine = RbacEngine()
        assert engine.check_permission("admin", "publish_knowledge") is True
        assert engine.check_permission("manager", "publish_knowledge") is False
        assert engine.check_permission("member", "publish_knowledge") is False

    def test_invalid_role_defaults_to_no_permission(self):
        """Test invalid role returns False."""
        from app.services.tenant_service import RbacEngine

        engine = RbacEngine()
        result = engine.check_permission("invalid_role", "submit_knowledge")
        assert result is False

    def test_invalid_action_defaults_to_no_permission(self):
        """Test invalid action returns False."""
        from app.services.tenant_service import RbacEngine

        engine = RbacEngine()
        result = engine.check_permission("admin", "invalid_action")
        assert result is False

    def test_get_role_permissions(self):
        """Test getting all permissions for a role."""
        from app.services.tenant_service import RbacEngine

        engine = RbacEngine()
        admin_perms = engine.get_role_permissions("admin")

        assert "manage_org_settings" in admin_perms
        assert "manage_departments" in admin_perms
        assert admin_perms["manage_org_settings"] is True

    def test_check_permission_with_user_context(self):
        """Test permission check with full user context."""
        from app.services.tenant_service import RbacEngine

        engine = RbacEngine()
        user = {"id": str(uuid4()), "role": "manager", "org_id": str(uuid4())}

        result = engine.check_permission(user["role"], "manage_departments", user_context=user)
        assert result is True

        result = engine.check_permission(user["role"], "manage_org_settings", user_context=user)
        assert result is False
