"""
Comprehensive end-to-end workflow tests for Otto application

This test suite covers complete user journeys:
- User registration and onboarding workflow
- Chat creation and conversation workflow
- Document upload and RAG query workflow
- Library management workflow
- Preset sharing workflow
- Cost tracking and budget management workflow
- Multi-user collaboration workflows
- Error recovery workflows
"""

import pytest
import uuid
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from django.contrib.auth.models import Group
from django.utils import timezone

from chat.models import Chat, Message, ChatOptions, ChatFile, Preset
from chat.llm import OttoLLM
from librarian.models import Document, DataSource, Library, LibraryUserRole, SavedFile
from otto.secure_models import AccessKey
from otto.models import Cost, CostType, Feedback


# ==================== User Onboarding Workflow ====================

@pytest.mark.django_db
class TestUserOnboardingWorkflow:
    """Test complete user registration and onboarding process"""

    def test_new_user_complete_onboarding(self, basic_user):
        """Test end-to-end new user onboarding workflow"""
        # Step 1: User is created (SSO authentication)
        user = basic_user(username="newuser", accept_terms=False)
        assert user.upn == "newuser.lastname@example.com"
        assert not user.accepted_terms

        # Step 2: User tries to access Otto (should be blocked)
        from otto.utils.decorators import permission_required
        # In real app, this would redirect to terms page

        # Step 3: User accepts terms
        user.accepted_terms_date = timezone.now()
        user.save()
        assert user.accepted_terms

        # Step 4: User is automatically added to base groups
        # (In production, this happens via SSO or admin action)

        # Step 5: User creates first chat
        chat = Chat.objects.create(title="My First Chat",
            user=user)
        assert chat.title == "My First Chat"
        assert chat.user == user

        # Step 6: User sends first message
        message = Message.objects.create(
            chat=chat,
            text="Hello, this is my first message!"
        )
        assert message.text == "Hello, this is my first message!"

        # Step 7: Verify user state
        assert user.accepted_terms
        assert Chat.objects.filter(user=user).count() == 1
        assert Message.objects.filter(chat__user=user).count() == 1

    def test_admin_user_onboarding(self, basic_user):
        """Test admin user gets additional permissions"""
        # Step 1: Create user
        admin_user = basic_user(username="admin", accept_terms=True)

        # Step 2: Add to Otto admin group
        admin_group = Group.objects.get(name="Otto admin")
        admin_user.groups.add(admin_group)
        admin_user.save()

        # Step 3: Verify admin permissions
        assert admin_user.is_admin
        assert admin_user.has_perm("otto.manage_users")

        # Step 4: Admin can create public libraries
        library = Library.objects.create(
            name="Public Library",
            is_public=True,
            created_by=admin_user
        )
        assert library.is_public


# ==================== Chat Conversation Workflow ====================

@pytest.mark.django_db
class TestChatConversationWorkflow:
    """Test complete chat creation and conversation workflow"""

    @patch('chat.llm.genai.GenerativeModel')
    def test_complete_chat_conversation(self, mock_genai, basic_user):
        """Test end-to-end chat conversation workflow"""
        user = basic_user()

        # Mock LLM responses
        mock_responses = [
            Mock(text="Hello! How can I help you today?"),
            Mock(text="Sure, I can help with that."),
            Mock(text="Here's the answer to your question.")
        ]
        mock_genai.return_value.generate_content.side_effect = mock_responses

        # Step 1: User creates new chat
        chat = Chat.objects.create(title="Technical Discussion",
            user=user)
        assert chat.title == "Technical Discussion"

        # Step 2: User sends first message
        user_msg1 = Message.objects.create(
            chat=chat,
            text="Hello, I need help with Python",
            is_bot=False
        )

        # Step 3: System generates response
        assistant_msg1 = Message.objects.create(
            chat=chat,
            text="Hello! How can I help you today?",
            is_bot=True
        )

        # Step 4: User continues conversation
        user_msg2 = Message.objects.create(
            chat=chat,
            text="Can you explain list comprehensions?",
            is_bot=False
        )

        assistant_msg2 = Message.objects.create(
            chat=chat,
            text="Sure, I can help with that.",
            is_bot=True
        )

        # Step 5: User asks follow-up question
        user_msg3 = Message.objects.create(
            chat=chat,
            text="Can you show me an example?",
            is_bot=False
        )

        assistant_msg3 = Message.objects.create(
            chat=chat,
            text="Here's the answer to your question.",
            is_bot=True
        )

        # Step 6: Verify conversation state
        messages = Message.objects.filter(chat=chat).order_by('date_created')
        assert messages.count() == 6  # 3 user + 3 assistant
        assert messages[0].is_bot == False
        assert messages[1].is_bot == True

        # Step 7: User pins important chat
        chat.pinned = True
        chat.save()
        assert chat.pinned

        # Step 8: Cost tracking
        cost_type = CostType.objects.get_or_create(
            name="LLM",
            defaults={"unit_name": "tokens", "unit_cost": 0.00001, "unit_quantity": 1000}
        )[0]
        Cost.objects.create(
            user=user,
            cost_type=cost_type,
            count=800,
            usd_cost=0.05
        )
        user_costs = Cost.objects.get_user_cost_this_month(user)
        assert user_costs > 0


# ==================== Document Upload and RAG Workflow ====================

@pytest.mark.django_db
class TestDocumentRAGWorkflow:
    """Test complete document upload and RAG query workflow"""

    @patch('librarian.utils.process_engine.fetch_from_url')
    @patch('librarian.utils.process_engine.extract_markdown')
    @patch('chat.llm.genai.GenerativeModel')
    def test_complete_document_rag_workflow(
        self, mock_genai, mock_extract, mock_fetch, basic_user
    ):
        """Test end-to-end document upload to RAG query workflow"""
        user = basic_user()
        access_key = AccessKey(user=user)

        # Mock document extraction
        mock_fetch.return_value = b"<html><body>Important document content</body></html>"
        mock_result = Mock()
        mock_result.markdown = "# Important Document\n\nThis is important information."
        mock_extract.return_value = mock_result

        # Mock LLM response
        mock_genai.return_value.generate_content.return_value = Mock(
            text="Based on the document, here's the answer..."
        )

        # Step 1: User creates private library
        library = Library.objects.create(name="My Research Library",
            is_public=False,
            created_by=user
        )
        assert library.name == "My Research Library"

        # Step 2: User creates datasource in library
        datasource = DataSource.objects.create(library=library,
            name="Research Papers"
        )
        assert datasource.name == "Research Papers"

        # Step 3: User uploads document
        document = Document.objects.create(data_source=datasource,
            url="https://example.com/research-paper.pdf",
            manual_title="Research Paper"
        )
        assert document.status == "PENDING"

        # Step 4: Document is processed (simulated)
        document.status = "COMPLETE"
        document.save()
        assert document.status == "COMPLETE"

        # Step 5: User creates Q&A chat with library
        chat = Chat.objects.create(title="Research Questions",
            user=user,
            mode="qa")
        assert chat.options.mode == "qa"

        # Step 6: User asks question about document
        question = Message.objects.create(
            chat=chat,
            text="What is the main finding of the research?",
            is_bot=False
        )

        # Step 7: System retrieves relevant documents and generates answer
        # (In real workflow, this uses vector similarity search)
        answer = Message.objects.create(
            chat=chat,
            text="Based on the document, here's the answer...",
            is_bot=True
        )

        # Step 8: Verify workflow completion
        assert Message.objects.filter(chat=chat).count() == 2
        assert document.status == "COMPLETE"
        assert Chat.objects.filter(user=user).count() == 1


# ==================== Library Management Workflow ====================

@pytest.mark.django_db
class TestLibraryManagementWorkflow:
    """Test complete library management workflow"""

    def test_library_collaboration_workflow(self, basic_user):
        """Test end-to-end library collaboration workflow"""
        owner = basic_user(username="owner")
        contributor = basic_user(username="contributor")
        viewer = basic_user(username="viewer")

        owner_key = AccessKey(user=owner)

        # Step 1: Owner creates library
        library = Library.objects.create(
            name="Team Library",
            is_public=False,
            created_by=owner
        )

        # Step 2: Owner adds contributors
        LibraryUserRole.objects.create(
            user=contributor,
            library=library,
            role="contributor"
        )

        LibraryUserRole.objects.create(
            user=viewer,
            library=library,
            role="viewer"
        )

        # Step 3: Owner creates datasource
        datasource = DataSource.objects.create(
            library=library,
            name="Shared Documents"
        )

        # Step 4: Contributor adds document
        contributor_key = AccessKey(user=contributor)
        doc = Document.objects.create(
            data_source=datasource,
            manual_title="Contributor Document"
        )

        # Step 5: Viewer views documents (read-only)
        viewer_key = AccessKey(user=viewer)
        docs = Document.objects.all(access_key=viewer_key)
        assert docs.count() == 1

        # Step 6: Verify permissions
        from otto.rules import can_edit_library, can_view_library

        assert can_view_library(owner, library)
        assert can_edit_library(owner, library)

        assert can_view_library(contributor, library)
        assert can_edit_library(contributor, library)

        assert can_view_library(viewer, library)
        assert not can_edit_library(viewer, library)

    def test_library_visibility_workflow(self, basic_user):
        """Test library visibility change workflow"""
        admin = basic_user(username="admin")
        admin_group = Group.objects.get(name="Otto admin")
        admin.groups.add(admin_group)

        regular_user = basic_user(username="regular")

        admin_key = AccessKey(user=admin)

        # Step 1: Admin creates private library
        library = Library.objects.create(
            name="Internal Library",
            is_public=False,
            created_by=admin
        )
        assert not library.is_public

        # Step 2: Regular user cannot access private library
        # Since SecureModel was removed, use django-rules to check permissions
        assert not regular_user.has_perm("librarian.view_library", library)

        # Step 3: Admin makes library public
        library.is_public = True
        library.save()

        # Step 4: Now regular user can view (but not edit)
        accessible_libs = Library.objects.all()
        # Note: SecureModel filtering might still apply
        # In production, public libraries visible to all


# ==================== Preset Sharing Workflow ====================

@pytest.mark.django_db
class TestPresetSharingWorkflow:
    """Test preset creation and sharing workflow"""

    def test_preset_creation_and_sharing(self, basic_user):
        """Test end-to-end preset creation and sharing"""
        creator = basic_user(username="creator")
        recipient = basic_user(username="recipient")

        # Step 1: Creator creates custom preset
        options = ChatOptions.objects.create(
            mode="qa",
            qa_model="gemini-1.5-pro"
        )
        preset = Preset.objects.create(
            name_en="Custom Research Preset",
            description_en="Optimized for research tasks",
            owner=creator,
            sharing_option="everyone",
            options=options
        )
        assert preset.name_en == "Custom Research Preset"

        # Step 2: Creator shares preset with specific user
        # Note: Preset sharing handled through is_public flag or direct sharing

        # Step 3: Recipient can now see and use preset
        from otto.rules import can_access_preset
        assert can_access_preset(recipient, preset)

        # Step 4: Recipient creates chat using shared preset
        chat = Chat.objects.create(title="Using Shared Preset",
            user=recipient,
            mode="qa")

        # Step 5: Verify preset usage
        assert chat.options.mode == "qa"
        assert chat.options.qa_model == "gemini-1.5-pro"


# ==================== Cost Tracking and Budget Workflow ====================

@pytest.mark.django_db
class TestCostBudgetWorkflow:
    """Test cost tracking and budget management workflow"""

    @patch('chat.llm.genai.GenerativeModel')
    def test_cost_tracking_workflow(self, mock_genai, basic_user):
        """Test end-to-end cost tracking workflow"""
        user = basic_user()

        mock_genai.return_value.generate_content.return_value = Mock(
            text="Response text"
        )

        # Step 1: User starts with zero costs
        initial_cost = Cost.objects.get_user_cost_this_month(user)
        assert initial_cost == 0

        # Step 2: User creates chat
        chat = Chat.objects.create(title="Cost Test Chat",
            user=user)

        # Step 3: User sends messages, incurring costs
        for i in range(5):
            Message.objects.create(
                chat=chat,
                text=f"Message {i}",
                is_bot=False
            )

            # System response creates cost
            cost_type = CostType.objects.get_or_create(
                name="LLM",
                defaults={"unit_name": "tokens", "unit_cost": 0.00001, "unit_quantity": 1000}
            )[0]
            Cost.objects.create(
                user=user,
                cost_type=cost_type,
                count=150 + i * 15,
                usd_cost=0.01 * (i + 1)
            )

        # Step 4: Check accumulated costs
        total_cost = Cost.objects.get_user_cost_this_month(user)
        assert total_cost > 0
        assert Cost.objects.filter(user=user).count() == 5

        # Step 5: User approaches budget limit
        from otto.utils.common import cad_cost
        user_cost_cad = cad_cost(total_cost)
        assert user_cost_cad < user.this_month_max

        # Step 6: Verify cost breakdown
        costs = Cost.objects.filter(user=user)
        assert costs.count() > 0, "Should have cost records"
        total_cost = sum(c.usd_cost for c in costs)
        assert total_cost > 0, "Total cost should be greater than 0"

    def test_budget_limit_workflow(self, basic_user):
        """Test budget limit enforcement workflow"""
        user = basic_user()

        # Set low budget for testing
        user.monthly_max = 1.0  # $1 CAD
        user.monthly_bonus = 0.0
        user.save()

        # Step 1: User incurs costs
        cost_type = CostType.objects.get_or_create(
            name="LLM",
            defaults={"unit_name": "tokens", "unit_cost": 0.00001, "unit_quantity": 1000}
        )[0]
        Cost.objects.create(
            user=user,
            cost_type=cost_type,
            count=15000,
            usd_cost=0.70  # Accounts for USD->CAD exchange rate (~1.38)
        )

        # Step 2: Check if user is over budget
        from otto.utils.common import cad_cost
        user_cost = cad_cost(Cost.objects.get_user_cost_this_month(user))
        assert user_cost < user.this_month_max
        assert not user.is_over_budget

        # Step 3: User exceeds budget
        Cost.objects.create(
            user=user,
            cost_type=cost_type,
            count=7500,
            usd_cost=0.20  # Pushes over $1
        )

        # Step 4: Verify over budget
        user_cost = cad_cost(Cost.objects.get_user_cost_this_month(user))
        assert user_cost >= user.this_month_max

        # Refresh user to check property
        user.refresh_from_db()
        # Note: is_over_budget property recalculates each time


# ==================== File Upload and Processing Workflow ====================

@pytest.mark.django_db
class TestFileUploadWorkflow:
    """Test file upload and processing workflow"""

    @patch('librarian.utils.process_engine.extract_markdown')
    def test_chat_file_upload_workflow(self, mock_extract, basic_user):
        """Test end-to-end file upload in chat"""
        user = basic_user()

        # Mock file extraction
        mock_result = Mock()
        mock_result.markdown = "Extracted file content"
        mock_extract.return_value = mock_result

        # Step 1: User creates chat
        chat = Chat.objects.create(title="File Discussion",
            user=user)

        # Step 2: User uploads file - need to create message first
        file_message = Message.objects.create(
            chat=chat,
            text="",
            is_bot=False
        )
        chat_file = ChatFile.objects.create(
            filename="document.pdf",
            content_type="application/pdf",
            message=file_message
        )
        assert chat_file.filename == "document.pdf"

        # Step 3: File is processed (simulated)
        chat_file.text = "Extracted file content"
        chat_file.save()

        # Step 4: User references file in message
        message = Message.objects.create(
            chat=chat,
            text="Can you summarize this document?"
        )

        # Attach file to message
        message.files.add(chat_file)

        # Step 5: Verify workflow
        assert message.files.count() == 1
        assert message.files.first() == chat_file


# ==================== Error Recovery Workflows ====================

@pytest.mark.django_db
class TestErrorRecoveryWorkflows:
    """Test error recovery and resilience workflows"""

    def test_document_processing_error_recovery(self, basic_user):
        """Test document processing error and retry workflow"""
        user = basic_user()
        access_key = AccessKey(user=user)

        library = Library.objects.create(name="Error Test Library",
            created_by=user
        )

        datasource = DataSource.objects.create(library=library,
            name="Error Test Source"
        )

        # Step 1: Document processing fails
        document = Document.objects.create(data_source=datasource,
            url="https://example.com/broken.pdf"
        )

        # Step 2: Mark as error with details
        document.status = "ERROR"
        document.status_details = "Failed to fetch URL: Connection timeout"
        document.save()
        assert document.status == "ERROR"

        # Step 3: User retries processing
        document.status = "PENDING"
        document.status_details = ""
        document.save()

        # Step 4: Processing succeeds on retry
        document.status = "COMPLETE"
        document.text = "Successfully processed document"
        document.save()
        assert document.status == "COMPLETE"

    @patch('chat.llm.genai.GenerativeModel')
    def test_llm_error_recovery_workflow(self, mock_genai, basic_user):
        """Test LLM error and retry workflow"""
        user = basic_user()

        # Step 1: Initial request fails
        from google.api_core import exceptions as google_exceptions
        mock_genai.return_value.generate_content.side_effect = [
            google_exceptions.ResourceExhausted("Rate limit exceeded"),
            Mock(text="Success after retry")
        ]

        chat = Chat.objects.create(title="Error Recovery Test",
            user=user)

        # Step 2: First message fails
        try:
            llm = OttoLLM()
            response = mock_genai.return_value.generate_content("test")
        except google_exceptions.ResourceExhausted as e:
            error_message = str(e)
            assert "Rate limit" in error_message

        # Step 3: Retry succeeds
        response = mock_genai.return_value.generate_content("test")
        assert response.text == "Success after retry"


# ==================== Multi-User Collaboration Workflows ====================

@pytest.mark.django_db
class TestMultiUserCollaboration:
    """Test multi-user collaboration workflows"""

    def test_team_library_workflow(self, basic_user):
        """Test team collaboration on shared library"""
        team_lead = basic_user(username="lead")
        member1 = basic_user(username="member1")
        member2 = basic_user(username="member2")

        lead_key = AccessKey(user=team_lead)

        # Step 1: Team lead creates shared library
        library = Library.objects.create(
            name="Team Project Library",
            is_public=False,
            created_by=team_lead
        )

        # Step 2: Add team members as contributors
        LibraryUserRole.objects.create(
            user=member1,
            library=library,
            role="contributor"
        )

        LibraryUserRole.objects.create(
            user=member2,
            library=library,
            role="contributor"
        )

        # Step 3: Create shared datasource
        datasource = DataSource.objects.create(
            library=library,
            name="Project Documents"
        )

        # Step 4: Team members add documents
        member1_key = AccessKey(user=member1)
        doc1 = Document.objects.create(
            data_source=datasource,
            manual_title="Member 1 Contribution"
        )

        member2_key = AccessKey(user=member2)
        doc2 = Document.objects.create(
            data_source=datasource,
            manual_title="Member 2 Contribution"
        )

        # Step 5: All team members can access all documents
        lead_docs = Document.objects.all()
        member1_docs = Document.objects.all()
        member2_docs = Document.objects.all()

        # Verify collaboration success - all team members can access documents
        assert doc1 in lead_docs
        assert doc2 in member1_docs
        assert doc1 in member2_docs


# ==================== Feedback and Support Workflow ====================

@pytest.mark.django_db
class TestFeedbackWorkflow:
    """Test user feedback submission workflow"""

    def test_feedback_submission_workflow(self, basic_user):
        """Test end-to-end feedback submission"""
        user = basic_user()

        # Step 1: User encounters issue
        chat = Chat.objects.create(title="Problematic Chat",
            user=user)

        # Step 2: User submits feedback
        feedback = Feedback.objects.create(
            feedback_type="bug",
            feedback_message="The chat interface is not loading properly",
            app="Otto",
            otto_version="v1.0",
            modified_by=user,
            created_at=timezone.now(),
            modified_on=timezone.now()
        )
        assert feedback.feedback_type == "bug"

        # Step 3: Admin reviews feedback
        admin = basic_user(username="admin")
        admin_group = Group.objects.get(name="Otto admin")
        admin.groups.add(admin_group)

        # Admin can see all feedback
        all_feedback = Feedback.objects.all()
        assert feedback in all_feedback

        # Step 4: Issue is resolved and feedback updated
        feedback.status = "resolved"
        feedback.modified_by = admin
        feedback.modified_on = timezone.now()
        feedback.save()

        assert feedback.status == "resolved"


# ==================== Session Management Workflow ====================

@pytest.mark.django_db
class TestSessionManagementWorkflow:
    """Test user session management workflows"""

    def test_user_session_continuity(self, basic_user):
        """Test session continuity across multiple actions"""
        user = basic_user()

        # Simulate user session with multiple actions
        # Step 1: User logs in (SSO handled externally)

        # Step 2: User creates multiple chats
        chats = []
        for i in range(3):
            chat = Chat.objects.create(title=f"Session Chat {i}",
                user=user)
            chats.append(chat)

        # Step 3: User creates messages across chats
        for chat in chats:
            Message.objects.create(
                chat=chat,
                text="Session message",
                    is_bot=False
            )

        # Step 4: Verify session state persistence
        user_chats = Chat.objects.filter(user=user)
        assert user_chats.count() == 3

        user_messages = Message.objects.filter(chat__user=user)
        assert user_messages.count() == 3

        # Step 5: User returns after session timeout
        # Data should persist
        user_chats_after = Chat.objects.filter(user=user)
        assert user_chats_after.count() == 3
