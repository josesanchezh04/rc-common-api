"""GraphQL queries for API Gateway."""
import strawberry
from strawberry.types import Info

from clients.user_client import get_user_client
from config.settings import get_settings
from middleware.permissions import IsAuthenticated
from middleware.tracking import get_tracking_id
from schema.types import User
from beautyfit_logger import get_logger


@strawberry.type
class Query:
    """GraphQL queries."""

    @strawberry.field(permission_classes=[IsAuthenticated])
    async def me(self, info: Info) -> User:
        """Return the profile of the currently authenticated user.

        Authentication is handled by :class:`IsAuthenticated`; ``user_data``
        is available in the context once the guard succeeds.

        Args:
            info: Strawberry Info object with request context.

        Returns:
            :class:`User` populated from the user-service.
        """
        logger = get_logger("Query.me")

        user_data = info.context["user_data"]
        user_id: str = user_data.get("firebase_uid", "")
        tracking_id = get_tracking_id(info)

        logger.info(f"Fetching profile for user_id={user_id}")

        settings = get_settings()
        user_client = get_user_client(settings.ms.user_service_url)
        result = await user_client.get_user(user_id, tracking_id)

        return User(
            user_id=result["user_id"],
            email=result.get("email", ""),
            first_name=result["first_name"],
            last_name=result["last_name"],
            display_name=result.get("display_name"),
            photo_url=result.get("photo_url"),
            role=result.get("role", "BASIC"),
            provider=result.get("provider", "firebase"),
            onboarding_step=result.get("onboarding_step", ""),
            phone_verified=result.get("phone_verified", False),
            profile_completed=result.get("profile_completed", False),
        )

