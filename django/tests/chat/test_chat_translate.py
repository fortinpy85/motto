import os
import tempfile
from decimal import Decimal
from unittest import mock

from django.urls import reverse

import pytest
import pytest_asyncio

from chat._views.load_test import exhaust_streaming_response
from chat.models import Chat, Message
from chat.tasks import translate_file

pytest_plugins = ("pytest_asyncio",)


@pytest.mark.django_db
def test_translate_file(all_apps_user):
    """Test translate_file function with Gemini-based translation."""
    # Create a temporary file with content
    with tempfile.NamedTemporaryFile(
        delete=False, mode="w", suffix=".txt", encoding="utf-8"
    ) as temp_file:
        temp_file.write("Hello, this is a test file.")
        file_path = temp_file.name

    try:
        # Create a user and message for the test
        user = all_apps_user()
        chat = Chat.objects.create(user=user)
        in_message = Message.objects.create(chat=chat, text="Translate this")
        out_message = Message.objects.create(chat=chat, text="")

        # Mock OttoLLM
        mock_llm = mock.MagicMock()
        mock_llm.complete.return_value = "Bonjour, ceci est un fichier de test."
        mock_llm.create_costs.return_value = None

        # Mock contextvars to return the message ID
        get_contextvars = mock.MagicMock()
        get_contextvars.return_value = {"message_id": out_message.id}

        with (
            mock.patch("chat.tasks.OttoLLM", return_value=mock_llm),
            mock.patch("chat.tasks.get_contextvars", get_contextvars),
        ):
            translate_file(file_path, "fr")

        # Verify that a ChatFile was created
        from chat.models import ChatFile
        chat_files = ChatFile.objects.filter(message=out_message)
        assert chat_files.count() == 1
        assert "FR" in chat_files.first().filename

    finally:
        # Clean up the temporary file
        if os.path.exists(file_path):
            os.remove(file_path)


@pytest.mark.django_db(transaction=True)
def test_translate_text_with_gemini(client, all_apps_user):
    """Test Gemini text translation through the translate_response function."""

    user = all_apps_user()
    client.force_login(user)

    # Create a chat using the route to create it with appropriate options
    response = client.get(reverse("chat:translate"), follow=True)
    chat = Chat.objects.filter(user=user).order_by("-created_at").first()
    chat.options.translate_model = "gemini-1.5-flash"
    chat.options.save()

    # Test chat_response with Translate mode
    message = Message.objects.create(chat=chat, text="Hello", mode="translate")
    message = Message.objects.create(
        chat=chat, mode="translate", is_bot=True, parent=message
    )
    response = client.get(reverse("chat:chat_response", args=[message.id]))
    assert response.status_code == 200
    content, _ = exhaust_streaming_response(response)
    assert (
        "Bonjour" in content
        or "Salut" in content
        or "Coucou" in content
        or "Allo" in content
    )


# Azure translation test removed - Azure Cognitive Services no longer supported
# All translation now uses Google Gemini models
