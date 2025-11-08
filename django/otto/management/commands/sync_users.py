# This command has been deprecated - Entra ID sync is no longer used
from django.core.management.base import BaseCommand
from django_extensions.management.utils import signalcommand


class Command(BaseCommand):
    help = "Deprecated: User sync with Entra ID is no longer supported"

    @signalcommand
    def handle(self, *args, **options):
        self.stdout.write(
            self.style.WARNING(
                "This command has been deprecated. Entra ID sync is no longer used. "
                "Users are managed through standard Django authentication."
            )
        )
