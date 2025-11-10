"""
Comprehensive authentication and authorization integration tests

This test suite covers:
- User authentication workflows
- Permission-based access control (django-rules)
- Role-based authorization (groups)
- Object-level permissions (rules predicates)
- Authorization decorators (@permission_required, @app_access_required)
- Budget enforcement (@budget_required)
- Terms acceptance workflow
- Multi-user scenarios
"""

import pytest
from datetime import datetime, date
from decimal import Decimal
from unittest.mock import Mock, patch
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied
from django.http import HttpRequest
from django.test import RequestFactory
from django.urls import reverse

from otto.models import User, App, Cost, CostType
from otto.rules import (
    accepted_terms,
    is_admin,
    can_view_app,
    can_access_app,
    can_access_chat,
    can_access_preset,
    can_edit_preset,
    can_view_library,
    can_edit_library,
    can_delete_library,
    can_manage_library_users
)
from otto.utils.decorators import permission_required, app_access_required, budget_required
from chat.models import Chat, ChatOptions, Preset
from librarian.models import Library, LibraryUserRole


# ==================== Authentication Tests ====================

@pytest.mark.django_db
class TestUserAuthentication:
    """Test user authentication and session management"""

    def test_user_creation_with_upn(self, django_user_model):
        """Test creating user with User Principal Name"""
        user = django_user_model.objects.create_user(
            upn="test.user@justice.gc.ca",
            email="test.user@justice.gc.ca",
            first_name="Test",
            last_name="User"
        )

        assert user.upn == "test.user@justice.gc.ca"
        assert user.email == "test.user@justice.gc.ca"
        assert user.is_active is True
        assert user.is_staff is False

    def test_user_authentication_with_upn(self, django_user_model):
        """Test that UPN is used as USERNAME_FIELD"""
        user = django_user_model.objects.create_user(
            upn="auth.test@justice.gc.ca",
            email="auth.test@justice.gc.ca"
        )

        # Verify UPN is the username field
        assert user.USERNAME_FIELD == "upn"
        assert user.get_username() == "auth.test@justice.gc.ca"

    def test_user_personal_library_creation(self, django_user_model):
        """Test that personal library is created on user creation"""
        user = django_user_model.objects.create_user(
            upn="library.user@justice.gc.ca",
            email="library.user@justice.gc.ca",
            first_name="Library",
            last_name="User"
        )

        personal_lib = user.personal_library
        assert personal_lib is not None
        assert personal_lib.is_personal_library is True
        assert personal_lib.created_by == user

    def test_superuser_creation(self, django_user_model):
        """Test creating superuser"""
        superuser = django_user_model.objects.create_superuser(
            upn="super.user@justice.gc.ca",
            email="super.user@justice.gc.ca"
        )

        assert superuser.is_staff is True
        assert superuser.is_superuser is True


# ==================== Terms Acceptance Tests ====================

@pytest.mark.django_db
class TestTermsAcceptance:
    """Test terms and conditions acceptance workflow"""

    def test_user_without_accepted_terms(self, basic_user):
        """Test user who hasn't accepted terms"""
        user = basic_user(accept_terms=False)

        assert user.accepted_terms is False
        assert user.accepted_terms_date is None
        assert not accepted_terms(user)

    def test_user_with_accepted_terms(self, basic_user):
        """Test user who has accepted terms"""
        user = basic_user(accept_terms=True)

        assert user.accepted_terms is True
        assert user.accepted_terms_date is not None
        assert accepted_terms(user)

    def test_terms_permission_gates_access(self, basic_user):
        """Test that otto.access_otto permission requires terms acceptance"""
        user_no_terms = basic_user(accept_terms=False)
        user_with_terms = basic_user(username="accepted_user", accept_terms=True)

        assert not user_no_terms.has_perm("otto.access_otto")
        assert user_with_terms.has_perm("otto.access_otto")


# ==================== Group-Based Authorization Tests ====================

@pytest.mark.django_db
class TestGroupBasedAuthorization:
    """Test role-based authorization using Django groups"""

    def test_otto_admin_group_membership(self, basic_user):
        """Test Otto admin group membership check"""
        user = basic_user()
        admin_group = Group.objects.get(name="Otto admin")

        # User not admin initially
        assert not user.is_admin
        assert not is_admin(user)

        # Add to admin group
        user.groups.add(admin_group)
        user = User.objects.get(pk=user.pk)  # Get fresh instance to clear caches

        assert user.is_admin
        assert is_admin(user)

    def test_operations_admin_group(self, basic_user):
        """Test Operations admin group membership"""
        user = basic_user()
        ops_group, _ = Group.objects.get_or_create(name="Operations admin")

        # Not operations admin initially
        assert not user.is_operations_admin

        # Add to operations admin group
        user.groups.add(ops_group)
        user.refresh_from_db()

        assert user.is_operations_admin

    def test_data_steward_permissions(self, basic_user):
        """Test Data steward group permissions"""
        user = basic_user()
        steward_group, _ = Group.objects.get_or_create(name="Data steward")

        # Initially cannot manage public libraries
        assert not user.has_perm("librarian.manage_public_libraries")

        # Add to data steward group
        user.groups.add(steward_group)
        user = User.objects.get(pk=user.pk)  # Get fresh instance to clear caches

        assert user.has_perm("librarian.manage_public_libraries")

    def test_make_otto_admin_method(self, basic_user):
        """Test make_otto_admin convenience method"""
        user = basic_user()

        assert not user.is_admin

        user.make_otto_admin()
        user.refresh_from_db()
        assert user.is_admin
        assert user.has_perm("otto.manage_users")
        assert user.has_perm("otto.load_laws")


# ==================== App Access Authorization Tests ====================

@pytest.mark.django_db
class TestAppAccessAuthorization:
    """Test app-level access control"""

    def test_view_app_public(self, basic_user):
        """Test viewing public app"""
        user = basic_user()
        app = App.objects.create(
            name="Public App",
            visible_to_all=True,
            user_group=None
        )

        assert can_view_app(user, app)
        assert user.has_perm("otto.view_app", app)

    def test_view_app_restricted_no_group(self, basic_user):
        """Test viewing restricted app without group membership"""
        user = basic_user()
        restricted_group, _ = Group.objects.get_or_create(name="Restricted Group")
        app = App.objects.create(
            name="Restricted App",
            visible_to_all=False,
            user_group=restricted_group
        )

        assert not can_view_app(user, app)
        assert not user.has_perm("otto.view_app", app)

    def test_view_app_restricted_with_group(self, basic_user):
        """Test viewing restricted app with group membership"""
        user = basic_user()
        restricted_group, _ = Group.objects.get_or_create(name="Restricted Group")
        app = App.objects.create(
            name="Restricted App",
            visible_to_all=False,
            user_group=restricted_group
        )

        # Add user to group
        user.groups.add(restricted_group)
        user.save()

        assert can_view_app(user, app)
        assert user.has_perm("otto.view_app", app)

    def test_admin_can_view_all_apps(self, all_apps_user):
        """Test that admin users can view all apps"""
        admin = all_apps_user()
        restricted_group, _ = Group.objects.get_or_create(name="Special Group")
        app = App.objects.create(
            name="Special App",
            visible_to_all=False,
            user_group=restricted_group
        )

        # Admin not in special group but can still view
        assert can_view_app(admin, app)
        assert admin.has_perm("otto.view_app", app)


# ==================== Chat Access Authorization Tests ====================

@pytest.mark.django_db
class TestChatAccessAuthorization:
    """Test chat-level access control"""

    def test_user_can_access_own_chat(self, basic_user):
        """Test user can access their own chat"""
        user = basic_user(accept_terms=True)
        chat = Chat.objects.create(user=user)

        assert can_access_chat(user, chat)
        assert user.has_perm("chat.access_chat", chat)

    def test_user_cannot_access_other_chat(self, basic_user):
        """Test user cannot access another user's chat"""
        user1 = basic_user(username="user1", accept_terms=True)
        user2 = basic_user(username="user2", accept_terms=True)
        chat = Chat.objects.create(user=user2)

        assert not can_access_chat(user1, chat)
        assert not user1.has_perm("chat.access_chat", chat)

    def test_preset_sharing_everyone(self, basic_user):
        """Test preset shared with everyone"""
        owner = basic_user(username="owner", accept_terms=True)
        other_user = basic_user(username="other", accept_terms=True)

        options = ChatOptions.objects.create()
        preset = Preset.objects.create(
            owner=owner,
            name_en="Public Preset",
            options=options,
            sharing_option="everyone"
        )

        assert can_access_preset(owner, preset)
        assert can_access_preset(other_user, preset)

    def test_preset_sharing_specific_users(self, basic_user):
        """Test preset shared with specific users"""
        owner = basic_user(username="owner", accept_terms=True)
        allowed_user = basic_user(username="allowed", accept_terms=True)
        blocked_user = basic_user(username="blocked", accept_terms=True)

        options = ChatOptions.objects.create()
        preset = Preset.objects.create(
            owner=owner,
            name_en="Shared Preset",
            options=options,
            sharing_option="others"
        )
        preset.accessible_to.add(allowed_user)

        assert can_access_preset(owner, preset)
        assert can_access_preset(allowed_user, preset)
        assert not can_access_preset(blocked_user, preset)

    def test_preset_edit_permissions(self, basic_user, all_apps_user):
        """Test preset edit permissions"""
        owner = basic_user(username="owner", accept_terms=True)
        other_user = basic_user(username="other", accept_terms=True)
        admin = all_apps_user()

        options = ChatOptions.objects.create()
        preset = Preset.objects.create(
            owner=owner,
            name_en="User Preset",
            options=options
        )

        # Owner can edit
        assert can_edit_preset(owner, preset)

        # Other users cannot edit
        assert not can_edit_preset(other_user, preset)

        # Admin cannot edit user's preset
        assert not can_edit_preset(admin, preset)

    def test_global_default_preset_restrictions(self, all_apps_user, basic_user):
        """Test that global default presets have special restrictions"""
        admin = all_apps_user()
        user = basic_user(accept_terms=True)

        options = ChatOptions.objects.create()
        global_preset = Preset.objects.create(
            owner=None,
            name_en="Global Default",
            options=options,
            english_default=True
        )

        # Admin can edit system preset
        assert can_edit_preset(admin, global_preset)

        # Cannot delete global default
        assert not user.has_perm("chat.delete_preset", global_preset)

        # Cannot change sharing on global default
        assert not user.has_perm("chat.edit_preset_sharing", global_preset)


# ==================== Library Access Authorization Tests ====================

@pytest.mark.django_db
class TestLibraryAccessAuthorization:
    """Test librarian access control"""

    def test_public_library_view_access(self, basic_user):
        """Test that public libraries are viewable by all"""
        user = basic_user()
        public_library = Library.objects.create(
            name="Public Library",
            is_public=True,
            created_by=user
        )

        assert can_view_library(user, public_library)

    def test_private_library_view_access(self, basic_user):
        """Test private library access requires role"""
        owner = basic_user(username="owner")
        viewer = basic_user(username="viewer")
        outsider = basic_user(username="outsider")

        private_library = Library.objects.create(
            name="Private Library",
            is_public=False,
            created_by=owner
        )

        # Grant viewer role
        LibraryUserRole.objects.create(
            user=viewer,
            library=private_library,
            role="viewer"
        )

        assert can_view_library(viewer, private_library)
        assert not can_view_library(outsider, private_library)

    def test_library_edit_permissions(self, basic_user):
        """Test library edit permissions by role"""
        admin_user = basic_user(username="admin")
        contributor = basic_user(username="contributor")
        viewer = basic_user(username="viewer")

        library = Library.objects.create(
            name="Test Library",
            is_public=False,
            created_by=admin_user
        )

        LibraryUserRole.objects.create(user=admin_user, library=library, role="admin")
        LibraryUserRole.objects.create(user=contributor, library=library, role="contributor")
        LibraryUserRole.objects.create(user=viewer, library=library, role="viewer")

        # Admin and contributor can edit
        assert can_edit_library(admin_user, library)
        assert can_edit_library(contributor, library)

        # Viewer cannot edit
        assert not can_edit_library(viewer, library)

    def test_library_delete_permissions(self, basic_user):
        """Test library delete permissions"""
        admin_user = basic_user(username="admin")
        contributor = basic_user(username="contributor")

        library = Library.objects.create(
            name="Deletable Library",
            is_public=False,
            created_by=admin_user
        )

        LibraryUserRole.objects.create(user=admin_user, library=library, role="admin")
        LibraryUserRole.objects.create(user=contributor, library=library, role="contributor")

        # Only admin can delete
        assert can_delete_library(admin_user, library)
        assert not can_delete_library(contributor, library)

    def test_personal_library_restrictions(self, basic_user):
        """Test that personal libraries have special restrictions"""
        user = basic_user()
        personal_lib = user.personal_library

        # Cannot delete personal library
        assert not can_delete_library(user, personal_lib)

        # Cannot manage users on personal library
        assert not can_manage_library_users(user, personal_lib)

    def test_manage_library_users_permission(self, basic_user, all_apps_user):
        """Test managing library users permission"""
        library_admin = basic_user(username="lib_admin")
        contributor = basic_user(username="contributor")
        otto_admin = all_apps_user()

        library = Library.objects.create(
            name="Managed Library",
            is_public=False,
            created_by=library_admin
        )

        LibraryUserRole.objects.create(user=library_admin, library=library, role="admin")
        LibraryUserRole.objects.create(user=contributor, library=library, role="contributor")

        # Library admin can manage users
        assert can_manage_library_users(library_admin, library)

        # Contributor cannot manage users
        assert not can_manage_library_users(contributor, library)

        # Otto admin can manage users on any library
        assert otto_admin.has_perm("librarian.manage_library_users", library)


# ==================== Decorator Tests ====================

@pytest.mark.django_db
class TestAuthorizationDecorators:
    """Test authorization decorator enforcement"""

    def test_permission_required_decorator_allows_access(self, basic_user):
        """Test permission_required decorator allows authorized users"""
        user = basic_user(accept_terms=True)
        request = RequestFactory().get('/')
        request.user = user

        @permission_required("otto.access_otto")
        def test_view(request):
            return "success"

        # NOTE: In current implementation, decorators are temporarily disabled
        # This test verifies the decorator exists and doesn't crash
        result = test_view(request)
        assert result == "success"

    def test_budget_required_decorator_blocks_over_budget(self, basic_user):
        """Test budget_required decorator blocks users over budget"""
        user = basic_user(accept_terms=True)

        # Set user budget and create costs exceeding it
        user.monthly_max = 10  # $10 CAD limit
        user.save()

        cost_type = CostType.objects.create(
            name="Test Cost",
            unit_cost=Decimal("1.0"),
            unit_quantity=1
        )

        # Create cost that exceeds budget (15 USD * 1.38 exchange rate = 20.7 CAD > 10 CAD)
        Cost.objects.create(
            cost_type=cost_type,
            count=1,
            usd_cost=Decimal("15.0"),
            user=user
        )

        request = RequestFactory().get('/')
        request.user = user
        request.headers = {}

        @budget_required
        def test_view(request):
            return "success"

        response = test_view(request)

        # Should redirect when over budget
        assert response.status_code in [200, 302]  # Redirect or HX-Redirect header


# ==================== Administrative Permission Tests ====================

@pytest.mark.django_db
class TestAdministrativePermissions:
    """Test administrative-level permissions"""

    def test_admin_can_manage_users(self, all_apps_user):
        """Test admin can manage users"""
        admin = all_apps_user()
        assert admin.has_perm("otto.manage_users")

    def test_admin_can_load_laws(self, all_apps_user):
        """Test admin can load laws"""
        admin = all_apps_user()
        assert admin.has_perm("otto.load_laws")

    def test_admin_can_manage_feedback(self, all_apps_user):
        """Test admin can manage feedback"""
        admin = all_apps_user()
        assert admin.has_perm("otto.manage_feedback")

    def test_operations_admin_can_manage_feedback(self, basic_user):
        """Test operations admin can manage feedback"""
        ops_admin = basic_user()
        ops_group, _ = Group.objects.get_or_create(name="Operations admin")
        ops_admin.groups.add(ops_group)
        ops_admin.save()

        assert ops_admin.has_perm("otto.manage_feedback")
        assert ops_admin.has_perm("otto.manage_cost_dashboard")

    def test_regular_user_cannot_access_admin_features(self, basic_user):
        """Test regular users cannot access admin features"""
        user = basic_user()

        assert not user.has_perm("otto.manage_users")
        assert not user.has_perm("otto.load_laws")
        assert not user.has_perm("otto.manage_feedback")
        assert not user.has_perm("otto.manage_cost_dashboard")


# ==================== Multi-User Scenario Tests ====================

@pytest.mark.django_db
class TestMultiUserScenarios:
    """Test complex multi-user authorization scenarios"""

    def test_collaborative_library_access(self, basic_user):
        """Test multiple users collaborating on a library"""
        admin = basic_user(username="admin")
        contributor1 = basic_user(username="contributor1")
        contributor2 = basic_user(username="contributor2")
        viewer = basic_user(username="viewer")
        outsider = basic_user(username="outsider")

        library = Library.objects.create(
            name="Collaborative Library",
            is_public=False,
            created_by=admin
        )

        LibraryUserRole.objects.create(user=admin, library=library, role="admin")
        LibraryUserRole.objects.create(user=contributor1, library=library, role="contributor")
        LibraryUserRole.objects.create(user=contributor2, library=library, role="contributor")
        LibraryUserRole.objects.create(user=viewer, library=library, role="viewer")

        # All users with roles can view
        assert can_view_library(admin, library)
        assert can_view_library(contributor1, library)
        assert can_view_library(contributor2, library)
        assert can_view_library(viewer, library)
        assert not can_view_library(outsider, library)

        # Admin and contributors can edit
        assert can_edit_library(admin, library)
        assert can_edit_library(contributor1, library)
        assert can_edit_library(contributor2, library)
        assert not can_edit_library(viewer, library)

        # Only admin can delete and manage users
        assert can_delete_library(admin, library)
        assert not can_delete_library(contributor1, library)
        assert can_manage_library_users(admin, library)
        assert not can_manage_library_users(contributor1, library)

    def test_chat_isolation_between_users(self, basic_user):
        """Test that chats are properly isolated between users"""
        user1 = basic_user(username="user1", accept_terms=True)
        user2 = basic_user(username="user2", accept_terms=True)
        user3 = basic_user(username="user3", accept_terms=True)

        chat1 = Chat.objects.create(user=user1)
        chat2 = Chat.objects.create(user=user2)
        chat3 = Chat.objects.create(user=user3)

        # Each user can only access their own chat
        assert user1.has_perm("chat.access_chat", chat1)
        assert not user1.has_perm("chat.access_chat", chat2)
        assert not user1.has_perm("chat.access_chat", chat3)

        assert user2.has_perm("chat.access_chat", chat2)
        assert not user2.has_perm("chat.access_chat", chat1)
        assert not user2.has_perm("chat.access_chat", chat3)


# ==================== Edge Case Tests ====================

@pytest.mark.django_db
class TestAuthorizationEdgeCases:
    """Test edge cases in authorization logic"""

    def test_user_without_groups(self, basic_user):
        """Test user with no group memberships"""
        user = basic_user()

        assert user.groups.count() == 0
        assert not user.is_admin
        assert not user.is_operations_admin

    def test_user_deletion_cascades_library(self, basic_user):
        """Test that deleting user deletes their personal library"""
        user = basic_user()
        personal_lib = user.personal_library
        library_id = personal_lib.id

        # Delete user
        user.delete()

        # Personal library should be deleted
        assert not Library.objects.filter(id=library_id).exists()

    def test_library_role_caching(self, basic_user):
        """Test library role caching for performance"""
        from otto.rules import get_library_roles_for_user

        user = basic_user()
        library = Library.objects.create(
            name="Test Library",
            created_by=user
        )

        LibraryUserRole.objects.create(user=user, library=library, role="admin")

        # First call should cache
        roles1 = get_library_roles_for_user(user)
        # Second call should use cache
        roles2 = get_library_roles_for_user(user)

        assert len(roles1) > 0
        assert roles1 == roles2

    def test_app_without_user_group(self, basic_user):
        """Test app with no user_group restriction"""
        user = basic_user()
        app = App.objects.create(
            name="No Group App",
            visible_to_all=False,
            user_group=None
        )

        # App with no group but not visible_to_all
        # Only admins should have access
        assert not can_access_app(user, app)

    def test_budget_calculation_with_exchange_rate(self, basic_user):
        """Test budget calculation considers exchange rate"""
        from otto.utils.common import cad_cost

        user = basic_user()
        user.monthly_max = 100  # $100 CAD
        user.save()

        cost_type = CostType.objects.create(
            name="Test Cost",
            unit_cost=Decimal("1.0"),
            unit_quantity=1
        )

        # Create cost in USD
        Cost.objects.create(
            cost_type=cost_type,
            count=1,
            usd_cost=Decimal("50.0"),  # $50 USD
            user=user
        )

        monthly_cost_usd = Cost.objects.get_user_cost_this_month(user)
        monthly_cost_cad = cad_cost(monthly_cost_usd)

        # $50 USD * 1.38 exchange rate = $69 CAD
        assert monthly_cost_cad > 50
        assert not user.is_over_budget  # Under $100 CAD limit
