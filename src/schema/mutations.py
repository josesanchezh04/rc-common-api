"""GraphQL mutations for API Gateway."""
import strawberry
from strawberry.types import Info
from schema.types import (
    User,
    UpdatePhoneResponse,
    UpdateProfileInput,
    UpgradePremiumInput,
    UpgradePremiumResponse,
    SkipPremiumResponse
)
from clients.user_client import get_user_client
from config.settings import get_settings
from middleware.auth_dependency import get_current_user
from middleware.permissions import IsAuthenticated
from middleware.tracking import get_tracking_id
from shared.logger.logger import get_logger


@strawberry.type
class Mutation:
    """GraphQL mutations."""
    
    @strawberry.mutation(permission_classes=[IsAuthenticated])
    async def register(
        self,
        info: Info
    ) -> User:
        """
        Register user with Firebase token.
        
        Authentication is handled by IsAuthenticated permission guard.
        The guard validates the token and stores user_data in context.
        
        Args:
            info: GraphQL info object
            
        Returns:
            User object with registration data
        """
        # Get logger - tracking_id is automatically injected by middleware
        logger = get_logger("Mutation.register")
        
        logger.info("Obtaining user data")
        # Extract user_data from context (set by IsAuthenticated guard)
        user_data = info.context["user_data"]

        if user_data and not user_data.get("phoneNumber"):
            return User(
                email=user_data["email"],
                first_name=user_data["first_name"],
                last_name=user_data["last_name"],
                display_name=user_data.get("display_name"),
                profile_completed=False
            )
        
        # Extract tracking_id from context (set by RequestTrackingMiddleware)
        tracking_id = get_tracking_id(info)
        
        # Get settings and user client
        settings = get_settings()
        user_client = get_user_client(settings.ms.user_service_url)
        
        # Register user with validated data
        logger.info("Registering user")
        registered_user = await user_client.register_user_with_data(user_data, tracking_id)
        
        # Return user
        return User(
            email=registered_user["email"],
            first_name=registered_user["first_name"],
            last_name=registered_user["last_name"],
            display_name=registered_user.get("display_name"),
            profile_completed=registered_user["profile_completed"]
        )
    
    @strawberry.mutation(permission_classes=[IsAuthenticated])
    async def update_phone(
        self,
        phone: str,
        phone_verified: bool,
        info: Info
    ) -> UpdatePhoneResponse:
        """Update user phone number. Authentication handled by IsAuthenticated guard."""
        # Extract user_data from context (set by IsAuthenticated guard)
        user_data = info.context["user_data"]
        user_id = user_data.get("firebase_uid")
        
        settings = get_settings()
        user_client = get_user_client(settings.ms.user_service_url)
        
        result = await user_client.update_phone(user_id, phone, phone_verified)
        
        return UpdatePhoneResponse(
            success=result["success"],
            phone_verified=result["phone_verified"],
            onboarding_step=result["onboarding_step"]
        )
    
    @strawberry.mutation(permission_classes=[IsAuthenticated])
    async def update_profile(
        self,
        input: UpdateProfileInput,
        info: Info
    ) -> User:
        """Update user profile. Authentication handled by IsAuthenticated guard."""
        # Extract user_data from context (set by IsAuthenticated guard)
        user_data = info.context["user_data"]
        user_id = user_data.get("firebase_uid")
        
        settings = get_settings()
        user_client = get_user_client(settings.ms.user_service_url)
        
        profile_data = {
            "first_name": input.first_name,
            "last_name": input.last_name,
            "country": input.country,
            "phone": input.phone
        }
        
        result = await user_client.update_profile(user_id, profile_data)
        
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
            profile_completed=result["profile_completed"]
        )
    
    @strawberry.mutation(permission_classes=[IsAuthenticated])
    async def upgrade_to_premium(
        self,
        input: UpgradePremiumInput,
        info: Info
    ) -> UpgradePremiumResponse:
        """Upgrade user to premium. Authentication handled by IsAuthenticated guard."""
        # Extract user_data from context (set by IsAuthenticated guard)
        user_data = info.context["user_data"]
        user_id = user_data.get("firebase_uid")
        
        settings = get_settings()
        user_client = get_user_client(settings.ms.user_service_url)
        
        payment_data = {
            "payment_method_id": input.payment_method_id,
            "plan": input.plan
        }
        
        result = await user_client.upgrade_to_premium(user_id, payment_data)
        
        return UpgradePremiumResponse(
            success=result["success"],
            role=result["role"],
            subscription_id=result["subscription_id"],
            subscription_status=result["subscription_status"],
            onboarding_step=result["onboarding_step"]
        )
    
    @strawberry.mutation(permission_classes=[IsAuthenticated])
    async def skip_premium(
        self,
        info: Info
    ) -> SkipPremiumResponse:
        """Skip premium upgrade. Authentication handled by IsAuthenticated guard."""
        # Extract user_data from context (set by IsAuthenticated guard)
        user_data = info.context["user_data"]
        user_id = user_data.get("firebase_uid")
        
        settings = get_settings()
        user_client = get_user_client(settings.ms.user_service_url)
        
        result = await user_client.skip_premium(user_id)
        
        return SkipPremiumResponse(
            success=result["success"],
            role=result["role"],
            onboarding_step=result["onboarding_step"]
        )
