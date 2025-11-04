import pytest
from django.contrib.auth import get_user_model
from otto.models import SecurityLabel

User = get_user_model()

@pytest.mark.django_db
def test_create_user():
    """
    Tests the creation of a User object.
    """
    user = User.objects.create_user(upn="testuser@example.com", email="testuser@example.com")
    assert user.upn == "testuser@example.com"
    assert user.email == "testuser@example.com"
    assert user.username == "testuser"

@pytest.mark.django_db
def test_create_security_label():
    """
    Tests the creation of a SecurityLabel object.
    """
    label = SecurityLabel.objects.create(name="Unclassified", acronym_en="UC")
    assert label.name == "Unclassified"
    assert label.acronym_en == "UC"