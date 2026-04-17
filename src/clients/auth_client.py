"""HTTP client for auth-service communication."""
import httpx
from typing import Optional
from src.clients.gcp_auth import get_oidc_token


class AuthServiceClient:
    """Client for auth-service."""
    
    def __init__(self, base_url: str):
        """Initialize auth client."""
        self.base_url = base_url.rstrip("/")
        self.client = httpx.AsyncClient(timeout=5.0)

    async def _get_base_headers(self, tracking_id: str = None) -> dict:
        """Get base headers including GCP OIDC token."""
        headers = {}
        if tracking_id:
            headers["X-Tracking-ID"] = tracking_id
        
        oidc_token = await get_oidc_token(self.base_url)
        if oidc_token:
            headers["Authorization"] = f"Bearer {oidc_token}"
        return headers
    
    async def validate_token(self, firebase_token: str, tracking_id: str = None) -> dict:
        """
        Validate Firebase token.
        
        Args:
            firebase_token: Firebase ID token
            tracking_id: Optional tracking ID for distributed tracing
            
        Returns:
            dict with user_data from Firebase
            
        Raises:
            httpx.HTTPError: If validation fails
        """
        headers = await self._get_base_headers(tracking_id)
        
        response = await self.client.post(
            f"{self.base_url}/auth/validate",
            json={"firebase_token": firebase_token},
            headers=headers
        )
        response.raise_for_status()
        data = response.json()
        
        if not data.get("valid"):
            raise ValueError("Invalid token")
        
        return data.get("user_data", {})
    
    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()


# Singleton
_auth_client: Optional[AuthServiceClient] = None

def get_auth_client(base_url: str) -> AuthServiceClient:
    """Get auth client instance."""
    global _auth_client
    if _auth_client is None:
        _auth_client = AuthServiceClient(base_url)
    return _auth_client
