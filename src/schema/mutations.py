"""GraphQL mutations for API Gateway."""
import strawberry
from strawberry.types import Info

from clients.user_client import UserServiceClient, get_user_client
from config.settings import get_settings
from middleware.permissions import IsAuthenticated
from middleware.tracking import get_tracking_id
from schema.types import (
    SkipPremiumResponse,
    UpdatePhoneResponse,
    UpdateProfileInput,
    UpgradePremiumInput,
    UpgradePremiumResponse,
    User,
)
from beautyfit_logger import get_logger, set_tracking_id

# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _user_client() -> UserServiceClient:
    """Return the singleton :class:`UserServiceClient` using current settings."""
    return get_user_client(get_settings().ms.user_service_url)


# ---------------------------------------------------------------------------
# Mutations
# ---------------------------------------------------------------------------

@strawberry.type
class Mutation:
    """GraphQL mutations."""

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    async def register(self, info: Info) -> User:
        """Register the authenticated user.

        Authentication is handled by :class:`IsAuthenticated`; the guard
        validates the Firebase token and stores ``user_data`` in context.

        If the user has no phone number (first registration), returns a partial
        :class:`User` without calling the user-service so onboarding can
        proceed.

        Args:
            info: Strawberry Info object with request context.

        Returns:
            :class:`User` with registration data.
        """
        tracking_id = get_tracking_id(info)
        # set_tracking_id(tracking_id or "")
        logger = get_logger("Mutation.register")
        logger.info("Obtaining user data from context")

        user_data = info.context["user_data"]

        
        logger.info("Registering user with user-service")
        registered_user = await _user_client().register_user_with_data(user_data, tracking_id)

        return User(
            user_id=registered_user.get("user_id", user_data.get("firebase_uid", "")),
            email=registered_user["email"],
            first_name=registered_user.get("first_name") or "",
            last_name=registered_user.get("last_name") or "",
            display_name=registered_user.get("display_name"),
            photo_url=registered_user.get("photo_url"),
            role=registered_user.get("role", "BASIC"),
            provider=registered_user.get("provider", "firebase"),
            onboarding_step=registered_user.get("onboarding_step", "PHONE_VERIFICATION"),
            phone_verified=registered_user.get("phone_verified", False),
            profile_completed=registered_user.get("profile_completed", False),
        )

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    async def update_phone(
        self,
        phone: str,
        phone_verified: bool,
        info: Info,
    ) -> UpdatePhoneResponse:
        """Update the authenticated user's phone number.

        Args:
            phone: New phone number.
            phone_verified: Whether the number has been verified.
            info: Strawberry Info object with request context.

        Returns:
            :class:`UpdatePhoneResponse` with the updated state.
        """
        user_id: str = info.context["user_data"].get("firebase_uid", "")
        tracking_id = get_tracking_id(info)
        result = await _user_client().update_phone(user_id, phone, phone_verified, tracking_id)

        return UpdatePhoneResponse(
            success=result["success"],
            phone_verified=result["phone_verified"],
            onboarding_step=result["onboarding_step"],
        )

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    async def update_profile(self, input: UpdateProfileInput, info: Info) -> User:
        """Update the authenticated user's profile.

        Args:
            input: Profile fields to update.
            info: Strawberry Info object with request context.

        Returns:
            :class:`User` with the full updated profile.
        """
        user_id: str = info.context["user_data"].get("firebase_uid", "")

        profile_data = {
            "first_name": input.first_name,
            "last_name": input.last_name,
            "country": input.country,
            "phone": input.phone,
        }

        tracking_id = get_tracking_id(info)
        result = await _user_client().update_profile(user_id, profile_data, tracking_id)

        return User(
            user_id=result["user_id"],
            email=result.get("email", ""),
            first_name=result["first_name"],
            last_name=result["last_name"],
            display_name=result.get("display_name"),
            photo_url=result.get("photo_url"),
            role=result.get("role", "BASIC"),
            provider=result.get("provider", "firebase"),
            onboarding_step=result["onboarding_step"],
            phone_verified=result.get("phone_verified", False),
            profile_completed=result["profile_completed"],
        )

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    async def upgrade_to_premium(
        self, input: UpgradePremiumInput, info: Info
    ) -> UpgradePremiumResponse:
        """Upgrade the authenticated user to a premium plan.

        Args:
            input: Payment method and plan information.
            info: Strawberry Info object with request context.

        Returns:
            :class:`UpgradePremiumResponse` with subscription details.
        """
        user_id: str = info.context["user_data"].get("firebase_uid", "")

        payment_data = {
            "payment_method_id": input.payment_method_id,
            "plan": input.plan,
        }

        tracking_id = get_tracking_id(info)
        result = await _user_client().upgrade_to_premium(user_id, payment_data, tracking_id)

        return UpgradePremiumResponse(
            success=result["success"],
            role=result["role"],
            subscription_id=result["subscription_id"],
            subscription_status=result["subscription_status"],
            onboarding_step=result["onboarding_step"],
        )

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    async def skip_premium(self, info: Info) -> SkipPremiumResponse:
        """Skip the premium upgrade step during onboarding.

        Args:
            info: Strawberry Info object with request context.

        Returns:
            :class:`SkipPremiumResponse` with updated role and onboarding step.
        """
        user_id: str = info.context["user_data"].get("firebase_uid", "")
        tracking_id = get_tracking_id(info)
        result = await _user_client().skip_premium(user_id, tracking_id)

        return SkipPremiumResponse(
            success=result["success"],
            role=result["role"],
            onboarding_step=result["onboarding_step"],
        )

