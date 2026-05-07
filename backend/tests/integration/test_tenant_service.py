"""Integration tests for Tenant Service - Org/Dept/User with RBAC."""
import pytest
from uuid import uuid4

from app.services.tenant_service import (
    OrganizationService,
    DepartmentService,
    UserService,
    RbacEngine,
    InMemoryOrganizationRepository,
    InMemoryDepartmentRepository,
    InMemoryUserRepository,
)
from app.core.exceptions import (
    ResourceNotFoundException,
    DuplicateResourceException,
    PermissionDeniedException,
)


@pytest.fixture
def org_repo():
    return InMemoryOrganizationRepository()


@pytest.fixture
def dept_repo():
    return InMemoryDepartmentRepository()


@pytest.fixture
def user_repo():
    return InMemoryUserRepository()


@pytest.fixture
def org_service(org_repo):
    return OrganizationService(repo=org_repo)


@pytest.fixture
def dept_service(dept_repo):
    return DepartmentService(repo=dept_repo)


@pytest.fixture
def user_service(user_repo):
    return UserService(repo=user_repo)


@pytest.fixture
def rbac_engine():
    return RbacEngine()


class TestCreateUserWithOrg:
    """Integration test: Create user with organization association."""

    def test_create_user_with_org(self, org_service, user_service):
        """Test creating a user associated with an organization."""
        org = org_service.create_org({
            "name": "Test Corp",
            "slug": "test-corp",
            "plan": "pro"
        })
        assert org["id"] is not None
        assert org["name"] == "Test Corp"

        user = user_service.create_user({
            "org_id": org["id"],
            "email": "john@test-corp.com",
            "password": "SecurePass123!",
            "role": "admin"
        })
        assert user["email"] == "john@test-corp.com"
        assert user["role"] == "admin"
        assert user["org_id"] == org["id"]
        assert user["status"] == "active"
        assert "password_hash" not in user

    def test_user_belongs_to_correct_org(self, org_service, user_service):
        """Test user belongs to the correct organization."""
        org1 = org_service.create_org({"name": "Org One", "slug": "org-one"})
        org2 = org_service.create_org({"name": "Org Two", "slug": "org-two"})

        user1 = user_service.create_user({
            "org_id": org1["id"],
            "email": "user1@org1.com",
            "password": "Pass123!",
            "role": "member"
        })
        user2 = user_service.create_user({
            "org_id": org2["id"],
            "email": "user2@org2.com",
            "password": "Pass123!",
            "role": "member"
        })

        assert user1["org_id"] == org1["id"]
        assert user2["org_id"] == org2["id"]

        org1_users = user_service.get_org_users(org1["id"])
        org2_users = user_service.get_org_users(org2["id"])

        assert len(org1_users) == 1
        assert org1_users[0]["email"] == "user1@org1.com"
        assert len(org2_users) == 1
        assert org2_users[0]["email"] == "user2@org2.com"


class TestDeptHierarchyDelete:
    """Integration test: Delete department maintaining hierarchy."""

    def test_dept_hierarchy_delete(self, org_service, dept_service):
        """Test deleting a department preserves child departments."""
        org = org_service.create_org({"name": "Test Org", "slug": "test-hierarchy"})

        engineering = dept_service.create_dept({
            "org_id": org["id"],
            "name": "Engineering",
            "parent_id": None
        })
        backend = dept_service.create_dept({
            "org_id": org["id"],
            "name": "Backend",
            "parent_id": engineering["id"]
        })
        frontend = dept_service.create_dept({
            "org_id": org["id"],
            "name": "Frontend",
            "parent_id": engineering["id"]
        })

        result = dept_service.delete_dept(engineering["id"])
        assert result is True

        tree = dept_service.get_dept_tree(org["id"])
        root_names = [d["name"] for d in tree]
        assert "Backend" in root_names
        assert "Frontend" in root_names
        assert "Engineering" not in root_names

        updated_backend = dept_service.get_dept(backend["id"])
        assert updated_backend["parent_id"] is None

    def test_delete_leaf_department(self, org_service, dept_service):
        """Test deleting a leaf department (no children)."""
        org = org_service.create_org({"name": "Test Org", "slug": "test-leaf"})

        leaf = dept_service.create_dept({
            "org_id": org["id"],
            "name": "Single Dept",
            "parent_id": None
        })

        result = dept_service.delete_dept(leaf["id"])
        assert result is True

        with pytest.raises(ResourceNotFoundException):
            dept_service.get_dept(leaf["id"])


class TestRbacAdminBypass:
    """Integration test: Admin role bypasses permission checks."""

    def test_admin_bypass_permission_check(self, rbac_engine):
        """Test admin can perform all actions."""
        admin_role = "admin"
        assert rbac_engine.check_permission(admin_role, "manage_org_settings") is True
        assert rbac_engine.check_permission(admin_role, "publish_knowledge") is True
        assert rbac_engine.check_permission(admin_role, "manage_members") is True

    def test_admin_no_exception_on_require_permission(self, rbac_engine):
        """Test admin passes require_permission without exception."""
        admin_role = "admin"
        rbac_engine.require_permission(admin_role, "manage_org_settings")
        rbac_engine.require_permission(admin_role, "publish_knowledge")
        rbac_engine.require_permission(admin_role, "submit_knowledge")

    def test_admin_can_perform_all_actions(self, rbac_engine):
        """Test admin has all permissions."""
        admin_permissions = rbac_engine.get_role_permissions("admin")
        assert admin_permissions["manage_org_settings"] is True
        assert admin_permissions["manage_departments"] is True
        assert admin_permissions["manage_members"] is True
        assert admin_permissions["invite_members"] is True
        assert admin_permissions["submit_knowledge"] is True
        assert admin_permissions["review_knowledge"] is True
        assert admin_permissions["publish_knowledge"] is True


class TestRbacMemberRestricted:
    """Integration test: Member role is restricted."""

    def test_member_cannot_manage_org(self, rbac_engine):
        """Test member cannot manage organization settings."""
        assert rbac_engine.check_permission("member", "manage_org_settings") is False

    def test_member_cannot_manage_departments(self, rbac_engine):
        """Test member cannot manage departments."""
        assert rbac_engine.check_permission("member", "manage_departments") is False

    def test_member_cannot_manage_members(self, rbac_engine):
        """Test member cannot manage members."""
        assert rbac_engine.check_permission("member", "manage_members") is False

    def test_member_cannot_invite_members(self, rbac_engine):
        """Test member cannot invite members."""
        assert rbac_engine.check_permission("member", "invite_members") is False

    def test_member_cannot_review_knowledge(self, rbac_engine):
        """Test member cannot review knowledge."""
        assert rbac_engine.check_permission("member", "review_knowledge") is False

    def test_member_cannot_publish_knowledge(self, rbac_engine):
        """Test member cannot publish knowledge."""
        assert rbac_engine.check_permission("member", "publish_knowledge") is False

    def test_member_can_submit_knowledge(self, rbac_engine):
        """Test member can submit knowledge."""
        assert rbac_engine.check_permission("member", "submit_knowledge") is True

    def test_member_exception_on_require_admin_action(self, rbac_engine):
        """Test member raises exception on admin-only action."""
        with pytest.raises(PermissionDeniedException):
            rbac_engine.require_permission("member", "manage_org_settings")

    def test_member_permissions_only_submit(self, rbac_engine):
        """Test member only has submit_knowledge permission."""
        member_permissions = rbac_engine.get_role_permissions("member")
        assert member_permissions["submit_knowledge"] is True
        assert member_permissions["manage_org_settings"] is False
        assert member_permissions["manage_departments"] is False
        assert member_permissions["manage_members"] is False
        assert member_permissions["invite_members"] is False
        assert member_permissions["review_knowledge"] is False
        assert member_permissions["publish_knowledge"] is False


class TestRbacManagerBalanced:
    """Integration test: Manager role has balanced permissions."""

    def test_manager_can_manage_departments(self, rbac_engine):
        """Test manager can manage departments."""
        assert rbac_engine.check_permission("manager", "manage_departments") is True

    def test_manager_can_manage_members(self, rbac_engine):
        """Test manager can manage members."""
        assert rbac_engine.check_permission("manager", "manage_members") is True

    def test_manager_can_invite_members(self, rbac_engine):
        """Test manager can invite members."""
        assert rbac_engine.check_permission("manager", "invite_members") is True

    def test_manager_can_submit_knowledge(self, rbac_engine):
        """Test manager can submit knowledge."""
        assert rbac_engine.check_permission("manager", "submit_knowledge") is True

    def test_manager_can_review_knowledge(self, rbac_engine):
        """Test manager can review knowledge."""
        assert rbac_engine.check_permission("manager", "review_knowledge") is True

    def test_manager_cannot_manage_org_settings(self, rbac_engine):
        """Test manager cannot manage org settings."""
        assert rbac_engine.check_permission("manager", "manage_org_settings") is False

    def test_manager_cannot_publish_knowledge(self, rbac_engine):
        """Test manager cannot publish knowledge."""
        assert rbac_engine.check_permission("manager", "publish_knowledge") is False


class TestFullWorkflow:
    """Integration test: Full org-dept-user workflow."""

    def test_full_tenant_workflow(self, org_service, dept_service, user_service, rbac_engine):
        """Test complete tenant creation with org, dept, user and RBAC."""
        org = org_service.create_org({
            "name": "Acme Corporation",
            "slug": "acme-corp",
            "plan": "enterprise"
        })
        assert org["plan"] == "enterprise"

        engineering = dept_service.create_dept({
            "org_id": org["id"],
            "name": "Engineering",
            "parent_id": None
        })
        backend = dept_service.create_dept({
            "org_id": org["id"],
            "name": "Backend",
            "parent_id": engineering["id"]
        })

        admin_user = user_service.create_user({
            "org_id": org["id"],
            "email": "admin@acme.com",
            "password": "AdminPass123!",
            "role": "admin"
        })
        manager_user = user_service.create_user({
            "org_id": org["id"],
            "dept_id": engineering["id"],
            "email": "manager@acme.com",
            "password": "ManagerPass123!",
            "role": "manager"
        })
        member_user = user_service.create_user({
            "org_id": org["id"],
            "dept_id": backend["id"],
            "email": "developer@acme.com",
            "password": "DevPass123!",
            "role": "member"
        })

        assert rbac_engine.check_permission(admin_user["role"], "manage_org_settings") is True
        assert rbac_engine.check_permission(manager_user["role"], "manage_departments") is True
        assert rbac_engine.check_permission(member_user["role"], "submit_knowledge") is True
        assert rbac_engine.check_permission(member_user["role"], "publish_knowledge") is False

        tree = dept_service.get_dept_tree(org["id"])
        assert len(tree) == 1
        assert len(tree[0]["children"]) == 1

        updated_user = user_service.update_user(member_user["id"], {"role": "manager"})
        assert updated_user["role"] == "manager"
        assert rbac_engine.check_permission(updated_user["role"], "manage_departments") is True

        suspended_user = user_service.update_user(member_user["id"], {"status": "suspended"})
        assert suspended_user["status"] == "suspended"
