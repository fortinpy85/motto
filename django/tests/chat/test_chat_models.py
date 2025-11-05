
import pytest
from django.contrib.auth import get_user_model
from chat.models import Chat, ChatOptions, Preset
from librarian.models import DataSource, Library
from otto.models import SecurityLabel

User = get_user_model()

@pytest.mark.django_db
def test_create_chat():
    """
    Tests the creation of a Chat object.
    """
    user = User.objects.create_user(upn="testuser@example.com", email="testuser@example.com")
    chat = Chat.objects.create(user=user)
    assert chat.user == user
    assert chat.title == ""
    assert chat.pinned is False
    assert ChatOptions.objects.filter(chat=chat).exists()
    assert DataSource.objects.filter(chat=chat).exists()

@pytest.mark.django_db
def test_chat_str():
    """
    Tests the __str__ method of the Chat model.
    """
    user = User.objects.create_user(upn="testuser@example.com", email="testuser@example.com")
    chat = Chat.objects.create(user=user, title="Test Chat")
    assert str(chat) == f"Chat {chat.id}: Test Chat"

@pytest.mark.django_db
def test_chat_delete():
    """
    Tests the delete method of the Chat model.
    """
    user = User.objects.create_user(upn="testuser@example.com", email="testuser@example.com")
    chat = Chat.objects.create(user=user)
    data_source = DataSource.objects.get(chat=chat)
    chat.delete()
    assert not Chat.objects.filter(pk=chat.pk).exists()
    assert not DataSource.objects.filter(pk=data_source.pk).exists()

@pytest.mark.django_db
def test_chat_manager_create_with_mode():
    """
    Tests the create method of the ChatManager with a specific mode.
    """
    user = User.objects.create_user(upn="testuser@example.com", email="testuser@example.com")
    chat = Chat.objects.create(user=user, mode="qa")
    assert chat.options.mode == "qa"

@pytest.mark.django_db
def test_preset_creation_from_yaml(mocker):
    """
    Tests the create_from_yaml method of the PresetManager.
    """
    # Mock dependencies
    mocker.patch("chat.models.get_request", return_value=None)
    mocker.patch("os.path.exists", return_value=True)
    mocker.patch("builtins.open", mocker.mock_open(read_data=""))
    mocker.patch("librarian.utils.process_engine.generate_hash", return_value="dummy_hash")

    # Ensure no existing default libraries before creating a new one
    Library.objects.filter(is_default_library=True).delete()
    # Create a default library
    Library.objects.create(name="Default", is_default_library=True, is_public=True)

    # Clear fixture presets loaded during setup to ensure test isolation
    Preset.objects.all().delete()

    # Sample YAML data
    yaml_data = {
        "preset1": {
            "name_en": "Test Preset 1",
            "description_en": "Description 1",
            "options": {
                "chat_model": "test_model_1"
            }
        },
        "preset2": {
            "name_en": "Test Preset 2",
            "description_en": "Description 2",
            "based_on": "preset1",
            "options": {
                "chat_model": "test_model_2"
            }
        }
    }

    Preset.objects.create_from_yaml(yaml_data)

    assert Preset.objects.count() == 2
    preset1 = Preset.objects.get(name_en="Test Preset 1")
    preset2 = Preset.objects.get(name_en="Test Preset 2")

    assert preset1.options.chat_model == "test_model_1"
    assert preset2.options.chat_model == "test_model_2"
    assert preset1.sharing_option == "everyone"
    assert preset2.sharing_option == "everyone"
