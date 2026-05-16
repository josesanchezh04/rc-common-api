"""HTTP client for auth-service communication."""
import uuid
from typing import Optional

import httpx

from clients.gcp_auth import get_oidc_token


class AuthServiceClient:
    """HTTP client for the auth-service."""

    def __init__(self, base_url: str) -> None:
        """Initialise the client.

        Args:
            base_url: Base URL of the auth-service.
        """
        self.base_url = base_url.rstrip("/")
        self.client = httpx.AsyncClient(timeout=5.0)

    async def _get_base_headers(self, tracking_id: Optional[str] = None) -> dict:
        """Build common request headers.

        Args:
            tracking_id: Optional distributed-tracing ID.

        Returns:
            Headers dict, including OIDC ``Authorization`` when in production.
        """
        headers: dict = {}
        headers["X-Tracking-ID"] = tracking_id or str(uuid.uuid4())

        oidc_token = await get_oidc_token(self.base_url)
        if oidc_token:
            headers["Authorization"] = f"Bearer {oidc_token}"
        return headers

    async def validate_token(
        self, firebase_token: str, tracking_id: Optional[str] = None
    ) -> dict:
        """Validate a Firebase ID token against the auth-service.

        Args:
            firebase_token: Firebase ID token.
            tracking_id: Optional tracking ID for distributed tracing.

        Returns:
            ``user_data`` dict from the auth-service response.

        Raises:
            httpx.HTTPStatusError: If the auth-service returns a non-2xx status.
            ValueError: If the token is reported as invalid.
        """
        headers = await self._get_base_headers(tracking_id)

        response = await self.client.post(
            f"{self.base_url}/auth/validate",
            json={"firebase_token": firebase_token},
            headers=headers,
        )
        response.raise_for_status()
        data = response.json()

        if not data.get("valid"):
            raise ValueError("Invalid token")

        return data.get("user_data", {})

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        await self.client.aclose()


# ---------------------------------------------------------------------------
# Singleton helpers
# ---------------------------------------------------------------------------

_auth_client: Optional[AuthServiceClient] = None


def get_auth_client(base_url: str) -> AuthServiceClient:
    """Return the shared :class:`AuthServiceClient` instance (lazy-init).

    Args:
        base_url: Base URL of the auth-service (only used on first call).

    Returns:
        Singleton :class:`AuthServiceClient`.
    """
    global _auth_client
    if _auth_client is None:
        _auth_client = AuthServiceClient(base_url)
    return _auth_client


async def close_auth_client() -> None:
    """Close and discard the singleton client (called during app shutdown)."""
    global _auth_client
    if _auth_client is not None:
        await _auth_client.close()
        _auth_client = None
