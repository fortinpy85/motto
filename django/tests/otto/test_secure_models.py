"""
Comprehensive test suite for SecureModel framework (otto/secure_models.py)

This test suite covers:
- AccessKey creation and validation
- AccessControl grant/revoke/check permissions
- SecureManager queryset filtering with row-level security
- SecureModel CRUD operations with permission enforcement
- Edge cases and error conditions
- Logging and audit trail verification
"""

import pytest
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.db import IntegrityError

from otto.secure_models import AccessControl, AccessControlLog, AccessKey
from librarian.models import Library  # Using Library as example SecureModel

User = get_user_model()


# ==================== AccessKey Tests ====================

@pytest.mark.django_db
class TestAccessKey:
    """Test AccessKey creation and validation"""

    def test_access_key_with_user(self, basic_user):
        """Test creating AccessKey with valid user"""
        user = basic_user()
        access_key = AccessKey(user=user)
        assert access_key.user == user
        assert access_key.bypass is False

    def test_access_key_with_bypass(self):
        """Test creating AccessKey with bypass=True"""
        access_key = AccessKey(bypass=True)
        assert access_key.user is None
        assert access_key.bypass is True

    def test_access_key_no_user_no_bypass_raises_error(self):
        """Test that AccessKey without user or bypass raises ValueError"""
        with pytest.raises(ValueError, match="User or bypass must be provided"):
            AccessKey()

    def test_access_key_none_user_no_bypass_raises_error(self):
        """Test that AccessKey with None user and no bypass raises ValueError"""
        with pytest.raises(ValueError, match="User or bypass must be provided"):
            AccessKey(user=None, bypass=False)


# ==================== AccessControl Tests ====================

@pytest.mark.django_db
class TestAccessControl:
    """Test AccessControl model for permission management"""

    def test_grant_view_permission(self, basic_user):
        """Test granting view permission to a user"""
        user = basic_user()
        library = Library.objects.create(
            access_key=AccessKey(bypass=True),
            name_en="Test Library"
        )

        AccessControl.grant_permissions(
            user=user,
            content_object=library,
            required_permissions=[AccessControl.CAN_VIEW],
            reason="Test grant view"
        )

        # Verify permission was granted
        assert AccessControl.check_permissions(
            user=user,
            content_object=library,
            required_permissions=[AccessControl.CAN_VIEW]
        )

    def test_grant_multiple_permissions(self, basic_user):
        """Test granting multiple permissions at once"""
        user = basic_user()
        library = Library.objects.create(
            access_key=AccessKey(bypass=True),
            name_en="Test Library"
        )

        AccessControl.grant_permissions(
            user=user,
            content_object=library,
            required_permissions=[
                AccessControl.CAN_VIEW,
                AccessControl.CAN_CHANGE,
                AccessControl.CAN_DELETE
            ],
            reason="Test grant all"
        )

        # Verify all permissions were granted
        assert AccessControl.check_permissions(
            user=user,
            content_object=library,
            required_permissions=[
                AccessControl.CAN_VIEW,
                AccessControl.CAN_CHANGE,
                AccessControl.CAN_DELETE
            ]
        )

    def test_grant_empty_permissions_raises_error(self, basic_user):
        """Test that granting empty permissions list raises ValueError"""
        user = basic_user()
        library = Library.objects.create(
            access_key=AccessKey(bypass=True),
            name_en="Test Library"
        )

        with pytest.raises(ValueError, match="At least one permission should be granted"):
            AccessControl.grant_permissions(
                user=user,
                content_object=library,
                required_permissions=[],
                reason="Test invalid"
            )

    def test_grant_invalid_permission_raises_error(self, basic_user):
        """Test that granting invalid permission raises ValueError"""
        user = basic_user()
        library = Library.objects.create(
            access_key=AccessKey(bypass=True),
            name_en="Test Library"
        )

        with pytest.raises(ValueError, match="Invalid permissions specified"):
            AccessControl.grant_permissions(
                user=user,
                content_object=library,
                required_permissions=["invalid_permission"],
                reason="Test invalid"
            )

    def test_revoke_specific_permission(self, basic_user):
        """Test revoking a specific permission"""
        user = basic_user()
        library = Library.objects.create(
            access_key=AccessKey(bypass=True),
            name_en="Test Library"
        )

        # Grant all permissions
        AccessControl.grant_permissions(
            user=user,
            content_object=library,
            required_permissions=[
                AccessControl.CAN_VIEW,
                AccessControl.CAN_CHANGE,
                AccessControl.CAN_DELETE
            ]
        )

        # Revoke delete permission
        AccessControl.revoke_permissions(
            user=user,
            content_object=library,
            revoked_permissions=[AccessControl.CAN_DELETE],
            reason="Test revoke delete"
        )

        # Verify view and change remain, delete is gone
        assert AccessControl.check_permissions(
            user=user,
            content_object=library,
            required_permissions=[AccessControl.CAN_VIEW, AccessControl.CAN_CHANGE]
        )
        assert not AccessControl.check_permissions(
            user=user,
            content_object=library,
            required_permissions=[AccessControl.CAN_DELETE]
        )

    def test_revoke_all_permissions(self, basic_user):
        """Test revoking all permissions (no params)"""
        user = basic_user()
        library = Library.objects.create(
            access_key=AccessKey(bypass=True),
            name_en="Test Library"
        )

        # Grant permissions
        AccessControl.grant_permissions(
            user=user,
            content_object=library,
            required_permissions=[AccessControl.CAN_VIEW]
        )

        # Revoke all permissions
        AccessControl.revoke_permissions(
            user=user,
            content_object=library,
            reason="Test revoke all"
        )

        # Verify no permissions remain
        assert not AccessControl.check_permissions(
            user=user,
            content_object=library,
            required_permissions=[AccessControl.CAN_VIEW]
        )

    def test_revoke_invalid_permission_raises_error(self, basic_user):
        """Test that revoking invalid permission raises ValueError"""
        user = basic_user()
        library = Library.objects.create(
            access_key=AccessKey(bypass=True),
            name_en="Test Library"
        )

        with pytest.raises(ValueError, match="Invalid permissions specified"):
            AccessControl.revoke_permissions(
                user=user,
                content_object=library,
                revoked_permissions=["invalid_permission"]
            )

    def test_check_permissions_no_access_control(self, basic_user):
        """Test checking permissions when no AccessControl exists returns False"""
        user = basic_user()
        library = Library.objects.create(
            access_key=AccessKey(bypass=True),
            name_en="Test Library"
        )

        # Check permissions without granting any
        assert not AccessControl.check_permissions(
            user=user,
            content_object=library,
            required_permissions=[AccessControl.CAN_VIEW]
        )

    def test_access_control_logging_on_create(self, basic_user):
        """Test that AccessControlLog entry is created on permission grant"""
        user = basic_user()
        library = Library.objects.create(
            access_key=AccessKey(bypass=True),
            name_en="Test Library"
        )

        initial_log_count = AccessControlLog.objects.count()

        AccessControl.grant_permissions(
            user=user,
            content_object=library,
            required_permissions=[AccessControl.CAN_VIEW],
            reason="Test logging"
        )

        # Verify log entry was created
        assert AccessControlLog.objects.count() == initial_log_count + 1

        log_entry = AccessControlLog.objects.latest('modified_at')
        assert log_entry.upn == user.upn
        assert log_entry.action == "C"
        assert log_entry.can_view is True
        assert log_entry.reason == "Test logging"

    def test_access_control_unique_constraint(self, basic_user):
        """Test that unique constraint prevents duplicate AccessControl entries"""
        user = basic_user()
        library = Library.objects.create(
            access_key=AccessKey(bypass=True),
            name_en="Test Library"
        )
        content_type = ContentType.objects.get_for_model(library)

        # Create first AccessControl
        AccessControl.objects.create(
            user=user,
            content_type=content_type,
            object_id=library.id,
            can_view=True
        )

        # Attempt to create duplicate should update existing
        AccessControl.grant_permissions(
            user=user,
            content_object=library,
            required_permissions=[AccessControl.CAN_VIEW, AccessControl.CAN_CHANGE],
            reason="Update existing"
        )

        # Verify only one AccessControl exists
        assert AccessControl.objects.filter(
            user=user,
            content_type=content_type,
            object_id=library.id
        ).count() == 1


# ==================== SecureManager Tests ====================

@pytest.mark.django_db
class TestSecureManager:
    """Test SecureManager queryset filtering with row-level security"""

    def test_all_with_bypass_returns_all_objects(self):
        """Test that all() with bypass returns all objects"""
        # Create multiple libraries
        Library.objects.create(
            access_key=AccessKey(bypass=True),
            name_en="Library 1"
        )
        Library.objects.create(
            access_key=AccessKey(bypass=True),
            name_en="Library 2"
        )

        # Query with bypass
        access_key = AccessKey(bypass=True)
        libraries = Library.objects.all(access_key=access_key)

        assert libraries.count() >= 2

    def test_all_with_user_filters_by_permissions(self, basic_user):
        """Test that all() with user only returns objects user has access to"""
        user = basic_user()

        # Create libraries
        lib1 = Library.objects.create(
            access_key=AccessKey(bypass=True),
            name_en="Library 1"
        )
        lib2 = Library.objects.create(
            access_key=AccessKey(bypass=True),
            name_en="Library 2"
        )

        # Grant access to lib1 only
        AccessControl.grant_permissions(
            user=user,
            content_object=lib1,
            required_permissions=[AccessControl.CAN_VIEW]
        )

        # Query with user access key
        access_key = AccessKey(user=user)
        libraries = Library.objects.all(access_key=access_key)

        # Should only see lib1
        assert libraries.count() == 1
        assert libraries.first().id == lib1.id

    def test_get_with_permissions(self, basic_user):
        """Test get() with proper permissions"""
        user = basic_user()

        lib = Library.objects.create(
            access_key=AccessKey(bypass=True),
            name_en="Test Library"
        )

        # Grant access
        AccessControl.grant_permissions(
            user=user,
            content_object=lib,
            required_permissions=[AccessControl.CAN_VIEW]
        )

        # Get with user access key
        access_key = AccessKey(user=user)
        result = Library.objects.get(access_key=access_key, id=lib.id)

        assert result.id == lib.id

    def test_get_without_permissions_raises_error(self, basic_user):
        """Test get() without permissions raises DoesNotExist"""
        user = basic_user()

        lib = Library.objects.create(
            access_key=AccessKey(bypass=True),
            name_en="Test Library"
        )

        # Don't grant access

        # Get with user access key should fail
        access_key = AccessKey(user=user)
        with pytest.raises(Library.DoesNotExist):
            Library.objects.get(access_key=access_key, id=lib.id)

    def test_filter_with_permissions(self, basic_user):
        """Test filter() respects permissions"""
        user = basic_user()

        lib1 = Library.objects.create(
            access_key=AccessKey(bypass=True),
            name_en="Library 1"
        )
        lib2 = Library.objects.create(
            access_key=AccessKey(bypass=True),
            name_en="Library 2"
        )
        lib3 = Library.objects.create(
            access_key=AccessKey(bypass=True),
            name_en="Library 3"
        )

        # Grant access to lib1 and lib2 only
        for lib in [lib1, lib2]:
            AccessControl.grant_permissions(
                user=user,
                content_object=lib,
                required_permissions=[AccessControl.CAN_VIEW]
            )

        # Filter with user access key
        access_key = AccessKey(user=user)
        libraries = Library.objects.filter(access_key=access_key)

        assert libraries.count() == 2
        assert set(libraries.values_list('id', flat=True)) == {lib1.id, lib2.id}


# ==================== SecureModel CRUD Tests ====================

@pytest.mark.django_db
class TestSecureModelCRUD:
    """Test CRUD operations on SecureModel with permission enforcement"""

    def test_create_with_bypass(self):
        """Test creating object with bypass grants full permissions"""
        access_key = AccessKey(bypass=True)
        lib = Library.objects.create(
            access_key=access_key,
            name_en="Test Library"
        )

        assert lib.id is not None
        assert lib.name_en == "Test Library"

    def test_create_with_user_grants_permissions(self, basic_user):
        """Test creating object with user access_key grants permissions to user"""
        user = basic_user()
        access_key = AccessKey(user=user)

        lib = Library.objects.create(
            access_key=access_key,
            name_en="Test Library"
        )

        # Verify user has full permissions
        assert AccessControl.check_permissions(
            user=user,
            content_object=lib,
            required_permissions=[
                AccessControl.CAN_VIEW,
                AccessControl.CAN_CHANGE,
                AccessControl.CAN_DELETE
            ]
        )

    def test_save_with_bypass(self):
        """Test saving object with bypass"""
        lib = Library.objects.create(
            access_key=AccessKey(bypass=True),
            name_en="Original Name"
        )

        lib.name_en = "Updated Name"
        lib.save(access_key=AccessKey(bypass=True))

        lib.refresh_from_db()
        assert lib.name_en == "Updated Name"

    def test_save_with_change_permission(self, basic_user):
        """Test saving object with change permission"""
        user = basic_user()

        lib = Library.objects.create(
            access_key=AccessKey(bypass=True),
            name_en="Original Name"
        )

        # Grant change permission
        AccessControl.grant_permissions(
            user=user,
            content_object=lib,
            required_permissions=[AccessControl.CAN_VIEW, AccessControl.CAN_CHANGE]
        )

        # Update with user access key
        lib.name_en = "Updated Name"
        lib.save(access_key=AccessKey(user=user))

        lib.refresh_from_db()
        assert lib.name_en == "Updated Name"

    def test_save_without_change_permission_raises_error(self, basic_user):
        """Test saving without change permission raises PermissionDenied"""
        user = basic_user()

        lib = Library.objects.create(
            access_key=AccessKey(bypass=True),
            name_en="Original Name"
        )

        # Grant only view permission
        AccessControl.grant_permissions(
            user=user,
            content_object=lib,
            required_permissions=[AccessControl.CAN_VIEW]
        )

        # Attempt to update should fail
        lib.name_en = "Updated Name"
        with pytest.raises(PermissionDenied):
            lib.save(access_key=AccessKey(user=user))

    def test_delete_with_bypass(self):
        """Test deleting object with bypass"""
        lib = Library.objects.create(
            access_key=AccessKey(bypass=True),
            name_en="Test Library"
        )
        lib_id = lib.id

        lib.delete(access_key=AccessKey(bypass=True))

        assert not Library.objects.filter(id=lib_id).exists()

    def test_delete_with_delete_permission(self, basic_user):
        """Test deleting object with delete permission"""
        user = basic_user()

        lib = Library.objects.create(
            access_key=AccessKey(bypass=True),
            name_en="Test Library"
        )

        # Grant delete permission
        AccessControl.grant_permissions(
            user=user,
            content_object=lib,
            required_permissions=[AccessControl.CAN_VIEW, AccessControl.CAN_DELETE]
        )

        lib_id = lib.id
        lib.delete(access_key=AccessKey(user=user))

        assert not Library.objects.filter(id=lib_id).exists()

    def test_delete_without_delete_permission_raises_error(self, basic_user):
        """Test deleting without delete permission raises PermissionDenied"""
        user = basic_user()

        lib = Library.objects.create(
            access_key=AccessKey(bypass=True),
            name_en="Test Library"
        )

        # Grant only view permission
        AccessControl.grant_permissions(
            user=user,
            content_object=lib,
            required_permissions=[AccessControl.CAN_VIEW]
        )

        # Attempt to delete should fail
        with pytest.raises(PermissionDenied):
            lib.delete(access_key=AccessKey(user=user))


# ==================== Edge Cases and Error Conditions ====================

@pytest.mark.django_db
class TestEdgeCases:
    """Test edge cases and error conditions"""

    def test_multiple_users_different_permissions(self, basic_user):
        """Test that different users can have different permissions on same object"""
        user1 = basic_user(username="user1")
        user2 = basic_user(username="user2")

        lib = Library.objects.create(
            access_key=AccessKey(bypass=True),
            name_en="Shared Library"
        )

        # Grant view to user1, full permissions to user2
        AccessControl.grant_permissions(
            user=user1,
            content_object=lib,
            required_permissions=[AccessControl.CAN_VIEW]
        )
        AccessControl.grant_permissions(
            user=user2,
            content_object=lib,
            required_permissions=[
                AccessControl.CAN_VIEW,
                AccessControl.CAN_CHANGE,
                AccessControl.CAN_DELETE
            ]
        )

        # Verify user1 has limited access
        assert AccessControl.check_permissions(
            user=user1,
            content_object=lib,
            required_permissions=[AccessControl.CAN_VIEW]
        )
        assert not AccessControl.check_permissions(
            user=user1,
            content_object=lib,
            required_permissions=[AccessControl.CAN_DELETE]
        )

        # Verify user2 has full access
        assert AccessControl.check_permissions(
            user=user2,
            content_object=lib,
            required_permissions=[
                AccessControl.CAN_VIEW,
                AccessControl.CAN_CHANGE,
                AccessControl.CAN_DELETE
            ]
        )

    def test_permission_inheritance_not_automatic(self, basic_user):
        """Test that permissions are not inherited (e.g., from groups)"""
        user = basic_user()

        lib = Library.objects.create(
            access_key=AccessKey(bypass=True),
            name_en="Test Library"
        )

        # Don't grant permissions

        # User should not have access even if they might have group permissions
        assert not AccessControl.check_permissions(
            user=user,
            content_object=lib,
            required_permissions=[AccessControl.CAN_VIEW]
        )

    def test_cascade_deletion_removes_access_controls(self, basic_user):
        """Test that deleting an object cascades to AccessControl entries"""
        user = basic_user()

        lib = Library.objects.create(
            access_key=AccessKey(bypass=True),
            name_en="Test Library"
        )

        AccessControl.grant_permissions(
            user=user,
            content_object=lib,
            required_permissions=[AccessControl.CAN_VIEW]
        )

        content_type = ContentType.objects.get_for_model(Library)
        assert AccessControl.objects.filter(
            user=user,
            content_type=content_type,
            object_id=lib.id
        ).exists()

        # Delete the library
        lib.delete(access_key=AccessKey(bypass=True))

        # AccessControl entries should be removed
        assert not AccessControl.objects.filter(
            user=user,
            content_type=content_type,
            object_id=lib.id
        ).exists()

    def test_user_deletion_removes_access_controls(self, basic_user):
        """Test that deleting a user cascades to their AccessControl entries"""
        user = basic_user()

        lib = Library.objects.create(
            access_key=AccessKey(bypass=True),
            name_en="Test Library"
        )

        AccessControl.grant_permissions(
            user=user,
            content_object=lib,
            required_permissions=[AccessControl.CAN_VIEW]
        )

        assert AccessControl.objects.filter(user=user).exists()

        # Delete the user
        user.delete()

        # AccessControl entries should be removed
        assert not AccessControl.objects.filter(user=user).exists()

    def test_update_permissions_replaces_existing(self, basic_user):
        """Test that updating permissions replaces existing ones"""
        user = basic_user()

        lib = Library.objects.create(
            access_key=AccessKey(bypass=True),
            name_en="Test Library"
        )

        # Grant view permission
        AccessControl.grant_permissions(
            user=user,
            content_object=lib,
            required_permissions=[AccessControl.CAN_VIEW]
        )

        # Update to grant change and delete, but not view
        AccessControl.grant_permissions(
            user=user,
            content_object=lib,
            required_permissions=[AccessControl.CAN_CHANGE, AccessControl.CAN_DELETE]
        )

        # Verify view is gone, change and delete are present
        assert not AccessControl.check_permissions(
            user=user,
            content_object=lib,
            required_permissions=[AccessControl.CAN_VIEW]
        )
        assert AccessControl.check_permissions(
            user=user,
            content_object=lib,
            required_permissions=[AccessControl.CAN_CHANGE, AccessControl.CAN_DELETE]
        )
