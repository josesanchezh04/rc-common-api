"""Authentication dependency for GraphQL resolvers."""
from typing import Optional, Dict, Any
from strawberry.types import Info
from clients.auth_client import get_auth_client
from config.settings import get_settings
import httpx


class AuthenticationError(Exception):
    """Authentication error."""
    pass


async def get_current_user(info: Info):
    """
    Dependency to extract and validate Firebase token.
    
    Extracts token from:
    1. HTTP headers (Authorization: Bearer <token>)
    
    Args:
        info: Strawberry Info object with context
        
    Returns:
        dict with validated user data from Firebase
        
    Raises:
        AuthenticationError: If token is missing or invalid
    """
    # Extract tracking ID for propagation
    request = info.context.get("request")
    tracking_id = getattr(request.state, "tracking_id", None) if request else None
    
    # Try to get token from different sources
    token = None
    
    # 1. Try from HTTP Authorization header
    if not token and request:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]  # Remove "Bearer " prefix    
    
    if not token:
        raise AuthenticationError("No Firebase token provided")
    
    # Validate token with auth-service
    settings = get_settings()
    auth_client = get_auth_client(settings.ms.auth_service_url)
    
    try:
        user_data = await auth_client.validate_token(token, tracking_id)
        
        # Store validated user data in context for use in resolvers
        info.context["user_data"] = user_data
        
    except httpx.HTTPError as e:
        raise AuthenticationError(f"Token validation failed: {str(e)}")
    except ValueError as e:
        raise AuthenticationError(str(e))
