"""
Tests for chat forms helper functions.

This module tests the helper functions used in chat/forms.py, particularly
the extract_context_params() function which handles autocomplete context
parameter extraction.
"""

import pytest
from django.test import RequestFactory
from chat.forms import extract_context_params


class MockContextArg:
    """
    Mock the ContextArg structure from django-htmx-autocomplete.

    The autocomplete library passes context as:
    ContextArg(request=Django_Request, client_kwargs=GET_params_dict)
    """

    def __init__(self, request, client_kwargs):
        self.request = request
        self.client_kwargs = client_kwargs


class TestExtractContextParams:
    """Test the extract_context_params helper function"""

    def test_none_context(self):
        """Should return None request and empty dict for None context"""
        request, params = extract_context_params(None)
        assert request is None
        assert params == {}

    def test_contextarg_structure(self):
        """Should extract from ContextArg object correctly"""
        factory = RequestFactory()
        django_request = factory.get("/", {"library_id": "123"})
        context = MockContextArg(
            request=django_request, client_kwargs={"library_id": "123", "chat_id": "456"}
        )

        request, params = extract_context_params(context)
        assert request == django_request
        assert params == {"library_id": "123", "chat_id": "456"}

    def test_legacy_request_structure(self):
        """Should handle direct Django request object (backward compatibility)"""
        factory = RequestFactory()
        django_request = factory.get("/", {"library_id": "789"})

        request, params = extract_context_params(django_request)
        assert request == django_request
        # Convert QueryDict to regular dict for comparison
        assert dict(params) == {"library_id": "789"}

    def test_missing_attributes(self):
        """Should handle objects without expected attributes gracefully"""

        class BadContext:
            pass

        bad_context = BadContext()
        request, params = extract_context_params(bad_context)
        assert request == bad_context
        assert params == {}

    def test_contextarg_with_empty_kwargs(self):
        """Should handle ContextArg with empty client_kwargs"""
        factory = RequestFactory()
        django_request = factory.get("/")
        context = MockContextArg(request=django_request, client_kwargs={})

        request, params = extract_context_params(context)
        assert request == django_request
        assert params == {}

    def test_contextarg_with_multiple_params(self):
        """Should extract multiple parameters from ContextArg"""
        factory = RequestFactory()
        django_request = factory.get("/")
        context = MockContextArg(
            request=django_request,
            client_kwargs={
                "library_id": "100",
                "chat_id": "200",
                "search": "test query",
                "name": "qa_documents",
            },
        )

        request, params = extract_context_params(context)
        assert request == django_request
        assert params["library_id"] == "100"
        assert params["chat_id"] == "200"
        assert params["search"] == "test query"
        assert params["name"] == "qa_documents"

    def test_request_with_multiple_get_params(self):
        """Should handle Django request with multiple GET parameters"""
        factory = RequestFactory()
        django_request = factory.get(
            "/", {"library_id": "999", "filter": "active", "page": "2"}
        )

        request, params = extract_context_params(django_request)
        assert request == django_request
        params_dict = dict(params)
        assert params_dict["library_id"] == "999"
        assert params_dict["filter"] == "active"
        assert params_dict["page"] == "2"
