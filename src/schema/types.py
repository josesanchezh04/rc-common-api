"""GraphQL types for API Gateway."""
import strawberry
from typing import Optional


@strawberry.type
class User:
    """User type for GraphQL."""
    user_id: str
    email: str
    first_name: str
    last_name: str
    display_name: Optional[str] = None
    photo_url: Optional[str] = None
    role: str
    provider: str
    onboarding_step: str
    phone_verified: bool
    profile_completed: bool


@strawberry.type
class UpdatePhoneResponse:
    """Response for phone update."""
    success: bool
    phone_verified: bool
    onboarding_step: str


@strawberry.type
class UpgradePremiumResponse:
    """Response for premium upgrade."""
    success: bool
    role: str
    subscription_id: str
    subscription_status: str
    onboarding_step: str


@strawberry.type
class SkipPremiumResponse:
    """Response for skipping premium."""
    success: bool
    role: str
    onboarding_step: str


@strawberry.input
class UpdateProfileInput:
    """Input for profile update."""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    country: str
    phone: Optional[str] = None


@strawberry.input
class UpgradePremiumInput:
    """Input for premium upgrade."""
    payment_method_id: str
    plan: str
