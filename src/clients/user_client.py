"""HTTP client for user-service communication."""
import httpx
from typing import Optional
from src.clients.gcp_auth import get_oidc_token


class UserServiceClient:
    """Client for user-service."""
    
    def __init__(self, base_url: str):
        """Initialize user client."""
        self.base_url = base_url.rstrip("/")
        self.client = httpx.AsyncClient(timeout=10.0)

    async def _get_base_headers(self, tracking_id: str = None) -> dict:
        """Get base headers including GCP OIDC token."""
        headers = {}
        if tracking_id:
            headers["X-Tracking-ID"] = tracking_id
        
        oidc_token = await get_oidc_token(self.base_url)
        if oidc_token:
            headers["Authorization"] = f"Bearer {oidc_token}"
        return headers
    
    async def register_user(self, firebase_token: str, tracking_id: str = None) -> dict:
        """
        Register user.
        
        Args:
            firebase_token: Firebase ID token
            tracking_id: Optional tracking ID for distributed tracing
            
        Returns:
            dict with user data
            
        Raises:
            httpx.HTTPError: If registration fails
        """
        headers = await self._get_base_headers(tracking_id)
        
        response = await self.client.post(
            f"{self.base_url}/users/register",
            json={"firebase_token": firebase_token},
            headers=headers
        )
        response.raise_for_status()
        return response.json()
    
    async def register_user_with_data(self, user_data: dict, tracking_id: str = None) -> dict:
        """
        Register user with validated Firebase data.
        
        This method receives already-validated user data from auth-service
        instead of a Firebase token, avoiding redundant validation.
        
        Args:
            user_data: Validated user data from Firebase
            tracking_id: Optional tracking ID for distributed tracing
            
        Returns:
            dict with registered user data
            
        Raises:
            httpx.HTTPError: If registration fails
        """
        headers = await self._get_base_headers(tracking_id)
        
        response = await self.client.post(
            f"{self.base_url}/users/register-with-data",
            json=user_data,
            headers=headers
        )
        response.raise_for_status()
        return response.json()
    
    async def update_phone(self, user_id: str, phone: str, phone_verified: bool) -> dict:
        """Update user phone."""
        headers = await self._get_base_headers()
        headers["X-User-ID"] = user_id
        response = await self.client.post(
            f"{self.base_url}/users/update-phone",
            json={
                "phone": phone,
                "phone_verified": phone_verified
            },
            headers=headers
        )
        response.raise_for_status()
        return response.json()
    
    async def update_profile(self, user_id: str, profile_data: dict) -> dict:
        """Update user profile."""
        headers = await self._get_base_headers()
        headers["X-User-ID"] = user_id
        response = await self.client.patch(
            f"{self.base_url}/users/profile",
            json=profile_data,
            headers=headers
        )
        response.raise_for_status()
        return response.json()
    
    async def upgrade_to_premium(self, user_id: str, payment_data: dict) -> dict:
        """Upgrade user to premium."""
        headers = await self._get_base_headers()
        headers["X-User-ID"] = user_id
        response = await self.client.post(
            f"{self.base_url}/users/upgrade-premium",
            json=payment_data,
            headers=headers
        )
        response.raise_for_status()
        return response.json()
    
    async def skip_premium(self, user_id: str) -> dict:
        """Skip premium upgrade."""
        headers = await self._get_base_headers()
        headers["X-User-ID"] = user_id
        response = await self.client.post(
            f"{self.base_url}/users/skip-premium",
            headers=headers
        )
        response.raise_for_status()
        return response.json()
    
    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()


# Singleton
_user_client: Optional[UserServiceClient] = None

def get_user_client(base_url: str) -> UserServiceClient:
    """Get user client instance."""
    global _user_client
    if _user_client is None:
        _user_client = UserServiceClient(base_url)
    return _user_client
