# Generated migration to migrate Azure translation to Gemini
from django.db import migrations


def migrate_azure_to_gemini(apps, schema_editor):
    """
    Migrate existing ChatOptions from Azure translation models to Gemini.
    Maps:
    - "azure" -> "gemini-1.5-flash"
    - "azure_custom" -> "gemini-1.5-flash"
    - Leaves GPT models unchanged
    """
    ChatOptions = apps.get_model("chat", "ChatOptions")

    # Update all Azure translation model references to Gemini
    azure_options = ChatOptions.objects.filter(translate_model__in=["azure", "azure_custom"])
    azure_options.update(translate_model="gemini-1.5-flash")

    print(f"Migrated {azure_options.count()} ChatOptions from Azure to Gemini translation")


def reverse_migrate(apps, schema_editor):
    """
    Reverse migration - convert Gemini back to Azure (for rollback)
    Note: This is a best-effort reverse; we default to "azure" for simplicity
    """
    ChatOptions = apps.get_model("chat", "ChatOptions")

    gemini_options = ChatOptions.objects.filter(translate_model__startswith="gemini")
    gemini_options.update(translate_model="azure")

    print(f"Rolled back {gemini_options.count()} ChatOptions from Gemini to Azure translation")


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0025_alter_chatoptions_chat_reasoning_effort_and_more'),
    ]

    operations = [
        migrations.RunPython(migrate_azure_to_gemini, reverse_migrate),
    ]
