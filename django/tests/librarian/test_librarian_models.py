import pytest
from django.contrib.auth import get_user_model
from librarian.models import Library, DataSource
from otto.models import SecurityLabel
from chat.models import Chat, ChatOptions, Preset

User = get_user_model()

@pytest.mark.django_db
def test_create_library():
    """
    Tests the creation of a Library object.
    """
    library = Library.objects.create(name="Test Library")
    assert library.name == "Test Library"

@pytest.mark.django_db
def test_create_data_source():
    """
    Tests the creation of a DataSource object.
    """
    # Use get_or_create to avoid duplicate key errors with fixtures
    SecurityLabel.objects.get_or_create(name="Unclassified", defaults={"acronym_en": "UC"})
    user = User.objects.create_user(upn="testuser@example.com", email="testuser@example.com")
    options = ChatOptions.objects.create()
    Preset.objects.create(name_en="Default", options=options, english_default=True)
    chat = Chat.objects.create(user=user)
    data_source = DataSource.objects.get(chat=chat)
    assert data_source.chat == chat