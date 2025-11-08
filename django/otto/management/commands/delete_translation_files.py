from django.conf import settings
from django.core.management.base import BaseCommand

from django_extensions.management.utils import signalcommand
from structlog import get_logger

logger = get_logger(__name__)


class Command(BaseCommand):
    help = "Deprecated: Azure translation files cleanup is no longer needed"

    @signalcommand
    def handle(self, *args, **options):
        logger.warning(
            "This command has been deprecated. Azure translation services are no longer used. "
            "Translation is now handled by Google Gemini."
        )
