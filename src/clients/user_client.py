"""HTTP client for user-service communication."""
from typing import Optional

import httpx

from clients.gcp_auth import get_oidc_token


class UserServiceClient:
    """HTTP client for the user-service."""

    def __init__(self, base_url: str) -> None:
        """Initialise the client.

        Args:
            base_url: Base URL of the user-service.
        """
        self.base_url = base_url.rstrip("/")
        self.client = httpx.AsyncClient(timeout=10.0)

    async def _get_base_headers(self, tracking_id: Optional[str] = None) -> dict:
        """Build common request headers.

        Args:
            tracking_id: Optional distributed-tracing ID.

        Returns:
            Headers dict, including OIDC ``Authorization`` when in production.
        """
        headers: dict = {}
        if tracking_id:
            headers["X-Tracking-ID"] = tracking_id

        oidc_token = await get_oidc_token(self.base_url)
        if oidc_token:
            headers["Authorization"] = f"Bearer {oidc_token}"
        return headers

    async def get_user(self, user_id: str, tracking_id: Optional[str] = None) -> dict:
        """Fetch a user by their Firebase UID.

        Args:
            user_id: Firebase UID of the user.
            tracking_id: Optional tracking ID for distributed tracing.

        Returns:
            dict with user profile fields.

        Raises:
            httpx.HTTPStatusError: If the user-service returns a non-2xx status.
        """
        headers = await self._get_base_headers(tracking_id)
        headers["X-User-ID"] = user_id

        response = await self.client.get(
            f"{self.base_url}/users/me",
            headers=headers,
        )
        response.raise_for_status()
        return response.json()

    async def register_user_with_data(
        self, user_data: dict, tracking_id: Optional[str] = None
    ) -> dict:
        """Register a user using already-validated Firebase data.

        Avoids redundant token validation by receiving ``user_data`` directly
        from the auth-service instead of re-sending the raw Firebase token.

        Args:
            user_data: Validated user data from the auth-service.
            tracking_id: Optional tracking ID for distributed tracing.

        Returns:
            dict with the registered user's profile fields.

        Raises:
            httpx.HTTPStatusError: If the user-service returns a non-2xx status.
        """
        headers = await self._get_base_headers(tracking_id)

        response = await self.client.post(
            f"{self.base_url}/users/register-with-data",
            json=user_data,
            headers=headers,
        )
        response.raise_for_status()
        return response.json()

    async def update_phone(
        self, user_id: str, phone: str, phone_verified: bool,
        tracking_id: Optional[str] = None
    ) -> dict:
        """Update the phone number for a user.

        Args:
            user_id: Firebase UID of the user.
            phone: New phone number.
            phone_verified: Whether the phone has been verified.
            tracking_id: Optional tracking ID for distributed tracing.

        Returns:
            dict with updated phone fields.

        Raises:
            httpx.HTTPStatusError: If the user-service returns a non-2xx status.
        """
        headers = await self._get_base_headers(tracking_id)
        headers["X-User-ID"] = user_id

        response = await self.client.post(
            f"{self.base_url}/users/update-phone",
            json={"phone": phone, "phone_verified": phone_verified},
            headers=headers,
        )
        response.raise_for_status()
        return response.json()

    async def update_profile(
        self, user_id: str, profile_data: dict,
        tracking_id: Optional[str] = None
    ) -> dict:
        """Update a user's profile.

        Args:
            user_id: Firebase UID of the user.
            profile_data: Fields to update.
            tracking_id: Optional tracking ID for distributed tracing.

        Returns:
            dict with the full updated user profile.

        Raises:
            httpx.HTTPStatusError: If the user-service returns a non-2xx status.
        """
        headers = await self._get_base_headers(tracking_id)
        headers["X-User-ID"] = user_id

        response = await self.client.patch(
            f"{self.base_url}/users/profile",
            json=profile_data,
            headers=headers,
        )
        response.raise_for_status()
        return response.json()

    async def upgrade_to_premium(
        self, user_id: str, payment_data: dict,
        tracking_id: Optional[str] = None
    ) -> dict:
        """Upgrade a user to a premium plan.

        Args:
            user_id: Firebase UID of the user.
            payment_data: Payment method and plan information.
            tracking_id: Optional tracking ID for distributed tracing.

        Returns:
            dict with subscription and role fields.

        Raises:
            httpx.HTTPStatusError: If the user-service returns a non-2xx status.
        """
        headers = await self._get_base_headers(tracking_id)
        headers["X-User-ID"] = user_id

        response = await self.client.post(
            f"{self.base_url}/users/upgrade-premium",
            json=payment_data,
            headers=headers,
        )
        response.raise_for_status()
        return response.json()

    async def skip_premium(
        self, user_id: str, tracking_id: Optional[str] = None
    ) -> dict:
        """Skip the premium upgrade step during onboarding.

        Args:
            user_id: Firebase UID of the user.
            tracking_id: Optional tracking ID for distributed tracing.

        Returns:
            dict with updated role and onboarding_step.

        Raises:
            httpx.HTTPStatusError: If the user-service returns a non-2xx status.
        """
        headers = await self._get_base_headers(tracking_id)
        headers["X-User-ID"] = user_id

        response = await self.client.post(
            f"{self.base_url}/users/skip-premium",
            headers=headers,
        )
        response.raise_for_status()
        return response.json()

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        await self.client.aclose()


# ---------------------------------------------------------------------------
# Singleton helpers
# ---------------------------------------------------------------------------

_user_client: Optional[UserServiceClient] = None


def get_user_client(base_url: str) -> UserServiceClient:
    """Return the shared :class:`UserServiceClient` instance (lazy-init).

    Args:
        base_url: Base URL of the user-service (only used on first call).

    Returns:
        Singleton :class:`UserServiceClient`.
    """
    global _user_client
    if _user_client is None:
        _user_client = UserServiceClient(base_url)
    return _user_client


async def close_user_client() -> None:
    """Close and discard the singleton client (called during app shutdown)."""
    global _user_client
    if _user_client is not None:
        await _user_client.close()
        _user_client = None
