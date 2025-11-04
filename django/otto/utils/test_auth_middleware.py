# TEMPORARY: Auto-login middleware for local testing
# WARNING: Remove this file and middleware configuration before production deployment!

from django.contrib.auth import get_user_model, login
from django.utils.deprecation import MiddlewareMixin
from structlog import get_logger

logger = get_logger(__name__)
User = get_user_model()


class AutoLoginMiddleware(MiddlewareMixin):
    """
    Automatically log in the test user for local testing purposes.

    WARNING: This is ONLY for local testing and must be removed before production!
    """

    def process_request(self, request):
        if not request.user.is_authenticated:
            try:
                # Get or create test user
                test_user, created = User.objects.get_or_create(
                    upn="testuser",
                    defaults={
                        "email": "test@example.com",
                        "first_name": "Test",
                        "last_name": "User",
                        "is_active": True,
                        "is_staff": False,
                        "homepage_tour_completed": True,
                        "ai_assistant_tour_completed": True,
                        "laws_search_tour_completed": True,
                    },
                )

                # Log in the test user
                login(request, test_user, backend="django.contrib.auth.backends.ModelBackend")

                if created:
                    logger.info("Created and logged in test user", user=test_user.upn)
                else:
                    logger.info("Auto-logged in test user", user=test_user.upn)

            except Exception as e:
                logger.error("Failed to auto-login test user", error=str(e))

        return None
