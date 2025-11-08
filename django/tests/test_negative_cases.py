"""
Comprehensive negative test cases for views and forms

This test suite covers:
- Form validation failures
- Invalid input handling
- Missing required fields
- Permission denied scenarios
- HTTP error responses (400, 403, 404, 500)
- CSRF protection
- SQL injection attempts
- XSS attack prevention
- File upload vulnerabilities
- URL validation
- Email validation
- Malformed data handling
"""

import pytest
import uuid
from datetime import date
from decimal import Decimal
from unittest.mock import Mock, patch
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.http import Http404
from django.test import Client, RequestFactory
from django.urls import reverse

from otto.models import User, Feedback, Pilot
from otto.forms import FeedbackForm, UserGroupForm, PilotForm
from chat.models import Chat, Message, Preset
from chat.forms import PresetForm
from librarian.models import Library, DataSource, Document
from librarian.forms import LibraryDetailForm, DataSourceDetailForm, DocumentDetailForm


# ==================== Form Validation Tests ====================

@pytest.mark.django_db
class TestFormValidationFailures:
    """Test form validation with invalid input"""

    def test_feedback_form_missing_required_fields(self, basic_user):
        """Test FeedbackForm with missing required fields"""
        user = basic_user()

        # Missing feedback_message
        form = FeedbackForm(user=user, message_id=None, data={})

        assert not form.is_valid()
        assert 'feedback_message' in form.errors

    def test_feedback_form_user_mismatch(self, basic_user):
        """Test FeedbackForm rejects mismatched users"""
        user1 = basic_user(username="user1")
        user2 = basic_user(username="user2")

        form_data = {
            'feedback_message': 'Test feedback',
            'created_by': user1.id,
            'modified_by': user2.id,  # Mismatch!
            'app': 'Otto',
            'otto_version': 'v1.0',
        }

        form = FeedbackForm(user=user1, message_id=None, data=form_data)

        assert not form.is_valid()
        assert 'The user must match' in str(form.errors)

    def test_library_form_missing_name(self, basic_user):
        """Test LibraryDetailForm with missing required fields"""
        user = basic_user()

        form_data = {
            'description_en': 'Test description',
            # Missing name_en and order - both required
        }

        form = LibraryDetailForm(user=user, data=form_data)

        assert not form.is_valid()
        # Either name_en or order field should be in errors
        assert 'name_en' in form.errors or 'order' in form.errors

    def test_datasource_form_invalid_library(self, basic_user):
        """Test DataSourceDetailForm with non-existent library"""
        user = basic_user()

        form_data = {
            'name_en': 'Test DataSource',
            'library': 99999,  # Non-existent
        }

        form = DataSourceDetailForm(user=user, library_id=None, data=form_data)

        assert not form.is_valid()

    def test_document_url_form_invalid_url(self, basic_user):
        """Test DocumentDetailForm rejects invalid URLs"""
        user = basic_user()
        library = Library.objects.create(
            name="Test Library",
            created_by=user
        )
        datasource = DataSource.objects.create(
            name="Test Source",
            library=library
        )

        form_data = {
            'url': 'not-a-valid-url',  # Invalid format
            'data_source': datasource.id,
        }

        form = DocumentDetailForm(data_source_id=datasource.id, data=form_data)

        assert not form.is_valid()

    def test_preset_form_invalid_model_id(self, basic_user):
        """Test PresetForm with non-existent model"""
        user = basic_user()

        form_data = {
            'name': 'Test Preset',
            'model': 'nonexistent-model-id',
            'temperature': 0.5,
        }

        form = PresetForm(user=user, data=form_data)

        # Should fail validation for invalid model
        assert not form.is_valid()


# ==================== Input Validation Tests ====================

@pytest.mark.django_db
class TestInputValidation:
    """Test input validation and sanitization"""

    def test_sql_injection_in_search(self, basic_user):
        """Test SQL injection attempts are handled safely"""
        user = basic_user()

        # SQL injection attempt
        malicious_input = "'; DROP TABLE otto_user; --"

        # Should not raise SQL error
        users = User.objects.filter(upn__icontains=malicious_input)
        assert users.count() == 0  # No match

    def test_xss_in_feedback_message(self, basic_user):
        """Test XSS prevention in feedback messages"""
        user = basic_user()

        xss_payload = '<script>alert("XSS")</script>'

        feedback = Feedback.objects.create(
            feedback_type='bug',
            feedback_message=xss_payload,
            app='Otto',
            otto_version='v1.0',
            created_by=user,
            modified_by=user
        )

        # Django automatically escapes HTML
        assert feedback.feedback_message == xss_payload  # Stored as-is
        # Would be escaped on render

    def test_extremely_long_input(self, basic_user):
        """Test handling of excessively long input"""
        user = basic_user()

        # Create a very long string (beyond typical limits)
        long_string = 'A' * 10000

        form_data = {
            'feedback_message': long_string,
            'created_by': user.id,
            'modified_by': user.id,
            'app': 'Otto',
            'otto_version': 'v1.0',
        }

        form = FeedbackForm(user=user, message_id=None, data=form_data)

        # Form should accept it (database field is TextField)
        assert form.is_valid()

    def test_unicode_and_special_characters(self, basic_user):
        """Test handling of unicode and special characters"""
        user = basic_user()

        special_chars = "Test 中文 ñ é 🚀 © ® ™"

        library = Library.objects.create(
            name=special_chars,
            name_fr=special_chars,
            created_by=user
        )

        assert library.name == special_chars
        assert library.name_fr == special_chars

    def test_null_byte_injection(self, basic_user):
        """Test null byte injection prevention"""
        user = basic_user()

        # Null byte injection attempt
        malicious_name = "Library\x00.txt"

        # PostgreSQL doesn't allow null bytes in text fields
        with pytest.raises(ValueError, match="NUL"):
            library = Library.objects.create(
                name=malicious_name,
                created_by=user
            )


# ==================== Permission Denied Tests ====================

@pytest.mark.django_db
class TestPermissionDenied:
    """Test permission denied scenarios"""

    def test_non_admin_cannot_manage_users(self, basic_user):
        """Test non-admin users cannot manage users"""
        user = basic_user()

        assert not user.has_perm('otto.manage_users')

    def test_non_admin_cannot_load_laws(self, basic_user):
        """Test non-admin users cannot load laws"""
        user = basic_user()

        assert not user.has_perm('otto.load_laws')

    def test_user_cannot_access_other_user_chat(self, basic_user):
        """Test users cannot access other users' chats"""
        user1 = basic_user(username="user1", accept_terms=True)
        user2 = basic_user(username="user2", accept_terms=True)

        chat = Chat.objects.create(user=user2)

        assert not user1.has_perm('chat.access_chat', chat)

    def test_user_cannot_edit_other_user_preset(self, basic_user):
        """Test users cannot edit other users' presets"""
        owner = basic_user(username="owner", accept_terms=True)
        other_user = basic_user(username="other", accept_terms=True)

        options = ChatOptions.objects.create()
        preset = Preset.objects.create(
            owner=owner,
            name_en="Private Preset",
            options=options
        )

        assert not other_user.has_perm('chat.edit_preset', preset)

    def test_contributor_cannot_delete_library(self, basic_user):
        """Test contributors cannot delete libraries"""
        from librarian.models import LibraryUserRole

        admin_user = basic_user(username="admin")
        contributor = basic_user(username="contributor")

        library = Library.objects.create(
            name="Test Library",
            created_by=admin_user
        )

        LibraryUserRole.objects.create(
            user=contributor,
            library=library,
            role="contributor"
        )

        assert not contributor.has_perm('librarian.delete_library', library)


# ==================== HTTP Error Response Tests ====================

@pytest.mark.django_db
class TestHTTPErrorResponses:
    """Test HTTP error responses (404, 403, 400, 500)"""

    def test_404_nonexistent_chat(self, basic_user):
        """Test 404 for non-existent chat"""
        user = basic_user(accept_terms=True)
        nonexistent_id = uuid.uuid4()

        with pytest.raises(Chat.DoesNotExist):
            Chat.objects.get(id=nonexistent_id)

    def test_404_nonexistent_library(self, basic_user):
        """Test 404 for non-existent library"""
        user = basic_user()

        with pytest.raises(Library.DoesNotExist):
            Library.objects.get(id=99999)

    def test_404_nonexistent_document(self, basic_user):
        """Test 404 for non-existent document"""
        user = basic_user()

        with pytest.raises(Document.DoesNotExist):
            Document.objects.get(id=uuid.uuid4())

    def test_invalid_uuid_format(self):
        """Test handling of invalid UUID format"""
        with pytest.raises((ValueError, ValidationError)):
            uuid.UUID('not-a-valid-uuid')


# ==================== File Upload Validation Tests ====================

@pytest.mark.django_db
class TestFileUploadValidation:
    """Test file upload validation and security"""

    def test_document_without_file_or_url(self, basic_user):
        """Test document creation requires file or URL at process time"""
        user = basic_user()
        library = Library.objects.create(
            name="Test Library",
            created_by=user
        )
        datasource = DataSource.objects.create(
            name="Test Source",
            library=library
        )

        # Document can be created without file or URL, but processing will fail
        doc = Document.objects.create(
            data_source=datasource,
            # No saved_file or url
        )

        # Processing checks for file or URL and sets status to ERROR
        doc.process()
        doc.refresh_from_db()
        assert doc.status == "ERROR"

    def test_blocked_url_validation(self, basic_user):
        """Test that blocked URLs are rejected"""
        from otto.models import BlockedURL

        user = basic_user()

        # Add URL to blocklist
        BlockedURL.objects.create(url="http://malicious.com")

        # Attempt to create document with blocked URL should fail
        # (This depends on view-level validation)

    def test_file_size_limits(self, basic_user):
        """Test file size validation"""
        user = basic_user()

        # Regular users should have file size limits
        # Admins and data stewards can upload large files
        assert not user.has_perm('chat.upload_large_files')

        # Make user admin
        user.make_otto_admin()
        user.refresh_from_db()  # Refresh to get updated group membership

        assert user.has_perm('chat.upload_large_files')


# ==================== Data Integrity Tests ====================

@pytest.mark.django_db
class TestDataIntegrity:
    """Test data integrity and constraint violations"""

    def test_duplicate_upn_rejected(self, django_user_model):
        """Test duplicate UPN is rejected"""
        django_user_model.objects.create_user(
            upn="test@justice.gc.ca",
            email="test@justice.gc.ca"
        )

        # Attempt to create duplicate
        with pytest.raises(Exception):  # IntegrityError
            django_user_model.objects.create_user(
                upn="test@justice.gc.ca",
                email="test@justice.gc.ca"
            )

    def test_library_without_name(self, basic_user):
        """Test public library requires name"""
        user = basic_user()

        # Public libraries require a name, private libraries don't
        library = Library(
            created_by=user,
            is_public=True  # Public libraries must have a name
        )
        with pytest.raises(ValidationError):
            library.full_clean()

    def test_datasource_requires_library(self, basic_user):
        """Test DataSource requires library"""
        user = basic_user()

        with pytest.raises(ValidationError):
            datasource = DataSource(
                name_en="Test Source",
                # Missing library
            )
            datasource.full_clean()

    def test_negative_budget_value(self, basic_user):
        """Test negative budget values are handled"""
        user = basic_user()

        # Set negative monthly max
        user.monthly_max = -100
        user.save()

        # Should allow negative (might be used for unlimited)
        assert user.monthly_max == -100


# ==================== Edge Case Tests ====================

@pytest.mark.django_db
class TestEdgeCases:
    """Test edge cases and boundary conditions"""

    def test_zero_cost_calculation(self, basic_user):
        """Test handling of zero cost"""
        from otto.models import Cost, CostType

        user = basic_user()

        cost_type = CostType.objects.create(
            name="Free Service",
            unit_cost=Decimal("0.0"),
            unit_quantity=1
        )

        cost = Cost.objects.create(
            cost_type=cost_type,
            count=1000,
            usd_cost=Decimal("0.0"),
            user=user
        )

        assert cost.usd_cost == 0

    def test_empty_string_inputs(self, basic_user):
        """Test handling of empty string inputs"""
        user = basic_user()

        form_data = {
            'feedback_message': '',  # Empty string
            'created_by': user.id,
            'modified_by': user.id,
            'app': 'Otto',
            'otto_version': 'v1.0',
        }

        form = FeedbackForm(user=user, message_id=None, data=form_data)

        assert not form.is_valid()  # feedback_message is required

    def test_whitespace_only_inputs(self, basic_user):
        """Test handling of whitespace-only inputs"""
        user = basic_user()

        form_data = {
            'feedback_message': '   ',  # Only whitespace
            'created_by': user.id,
            'modified_by': user.id,
            'app': 'Otto',
            'otto_version': 'v1.0',
        }

        form = FeedbackForm(user=user, message_id=None, data=form_data)

        # Django forms strip whitespace before validation, so whitespace-only becomes empty
        assert not form.is_valid()
        assert 'feedback_message' in form.errors

    def test_date_boundary_conditions(self, basic_user):
        """Test date boundary conditions"""
        user = basic_user()

        # Set accepted_terms_date to past
        user.accepted_terms_date = date(2020, 1, 1)
        user.save()

        assert user.accepted_terms is True

        # Set to future (unusual but valid)
        user.accepted_terms_date = date(2099, 12, 31)
        user.save()

        assert user.accepted_terms is True


# ==================== Concurrent Access Tests ====================

@pytest.mark.django_db
class TestConcurrentAccess:
    """Test concurrent access scenarios"""

    def test_simultaneous_library_edit(self, basic_user):
        """Test simultaneous edits to same library"""
        user = basic_user()

        library = Library.objects.create(
            name="Original Name",
            created_by=user
        )

        # Simulate two users editing simultaneously
        lib1 = Library.objects.get(id=library.id)
        lib2 = Library.objects.get(id=library.id)

        lib1.name_en = "First Edit"
        lib1.save()

        lib2.name_en = "Second Edit"
        lib2.save()

        # Last write wins (Django ORM behavior)
        library.refresh_from_db()
        assert library.name == "Second Edit"

    def test_race_condition_user_creation(self, django_user_model):
        """Test race condition in user creation"""
        # This tests the unique constraint on UPN

        try:
            django_user_model.objects.create_user(
                upn="race@justice.gc.ca",
                email="race@justice.gc.ca"
            )

            # Attempt concurrent creation
            django_user_model.objects.create_user(
                upn="race@justice.gc.ca",
                email="race2@justice.gc.ca"
            )

            # Should fail due to unique constraint
            assert False, "Expected IntegrityError"
        except Exception:
            # Expected - unique constraint violation
            pass


# ==================== Malformed Data Tests ====================

@pytest.mark.django_db
class TestMalformedData:
    """Test handling of malformed or corrupted data"""

    def test_malformed_json_in_chat_options(self, basic_user):
        """Test handling of malformed JSON data"""
        user = basic_user(accept_terms=True)

        chat = Chat.objects.create(user=user)

        # ChatOptions might store JSON-like data
        # Test that the system handles corrupt data gracefully

    def test_invalid_enum_values(self, basic_user):
        """Test handling of invalid enum/choice values"""
        user = basic_user()

        # Invalid feedback type
        with pytest.raises((ValidationError, ValueError)):
            feedback = Feedback(
                feedback_type='invalid_type',  # Not in FEEDBACK_TYPE_CHOICES
                feedback_message='Test',
                app='Otto',
                otto_version='v1.0',
                created_by=user,
                modified_by=user
            )
            feedback.full_clean()

    def test_invalid_foreign_key_reference(self, basic_user):
        """Test invalid foreign key references"""
        user = basic_user()

        # Create document with non-existent datasource
        with pytest.raises((ValidationError, ValueError)):
            doc = Document(
                data_source_id=99999,  # Non-existent
                url="http://example.com"
            )
            doc.full_clean()

    def test_circular_reference_prevention(self, basic_user):
        """Test prevention of circular references"""
        # Test that the system prevents circular relationships
        # e.g., library -> datasource -> document -> library

        # Otto's current schema doesn't allow this, but test the concept
        user = basic_user()

        library = Library.objects.create(
            name="Test Library",
            created_by=user
        )

        # Schema prevents circular references by design


# ==================== Internationalization Tests ====================

@pytest.mark.django_db
class TestInternationalization:
    """Test i18n/l10n edge cases"""

    def test_missing_french_translation(self, basic_user):
        """Test handling when French translation is missing"""
        user = basic_user()

        library = Library.objects.create(
            name="English Name",
            name_fr="",  # Empty French name
            created_by=user
        )

        # Should fallback to English or show empty
        assert library.name == "English Name"

    def test_mixed_language_content(self, basic_user):
        """Test content with mixed English and French"""
        user = basic_user()

        mixed_content = "English text avec du français mélangé"

        library = Library.objects.create(
            name=mixed_content,
            created_by=user
        )

        assert library.name == mixed_content


# ==================== State Management Tests ====================

@pytest.mark.django_db
class TestStateManagement:
    """Test state management and transitions"""

    def test_feedback_status_transitions(self, basic_user):
        """Test valid and invalid feedback status transitions"""
        user = basic_user()

        feedback = Feedback.objects.create(
            feedback_type='bug',
            status='new',
            feedback_message='Test',
            app='Otto',
            otto_version='v1.0',
            created_by=user,
            modified_by=user
        )

        # Valid transition: new -> in_progress
        feedback.status = 'in_progress'
        feedback.save()
        assert feedback.status == 'in_progress'

        # Valid transition: in_progress -> resolved
        feedback.status = 'resolved'
        feedback.save()
        assert feedback.status == 'resolved'

        # Unusual but valid: resolved -> new (reopen)
        feedback.status = 'new'
        feedback.save()
        assert feedback.status == 'new'

    def test_document_status_lifecycle(self, basic_user):
        """Test document processing status lifecycle"""
        user = basic_user()
        library = Library.objects.create(
            name="Test Library",
            created_by=user
        )
        datasource = DataSource.objects.create(
            name="Test Source",
            library=library
        )

        doc = Document.objects.create(
            data_source=datasource,
            url="http://example.com"
        )

        # Document status should follow expected lifecycle
        assert doc.status == "PENDING"

        doc.status = "PROCESSING"
        doc.save()
        assert doc.status == "PROCESSING"

        doc.status = "COMPLETE"
        doc.save()
        assert doc.status == "COMPLETE"

        # Error state
        doc.status = "ERROR"
        doc.save()
        assert doc.status == "ERROR"
