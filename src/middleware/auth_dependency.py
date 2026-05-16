"""Authentication dependency for GraphQL resolvers."""
from typing import Optional, Dict, Any
from strawberry.types import Info
from clients.auth_client import get_auth_client
from config.settings import get_settings
from beautyfit_logger import get_logger
import httpx

logger = get_logger("AuthDependency")


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
        logger.warning("No Firebase token provided in request")
        raise AuthenticationError("No Firebase token provided")
    
    logger.debug(f"Token received (first 20 chars): {token[:20]}...")
    
    # Validate token with auth-service
    settings = get_settings()
    auth_service_url = settings.ms.auth_service_url
    logger.info(f"Validating token with auth-service at: {auth_service_url}")
    
    auth_client = get_auth_client(auth_service_url)
    
    try:
        user_data = await auth_client.validate_token(token, tracking_id)
        logger.info(f"Token validated successfully for user: {user_data.get('firebase_uid', 'unknown')}")
        
        # Store validated user data in context for use in resolvers
        info.context["user_data"] = user_data
        
    except httpx.HTTPStatusError as e:
        logger.error(f"Auth service HTTP error: {e.response.status_code} - {e.response.text}")
        raise AuthenticationError(f"Token validation failed: HTTP {e.response.status_code}")
    except httpx.HTTPError as e:
        logger.error(f"Auth service connection error: {str(e)}")
        raise AuthenticationError(f"Token validation failed: {str(e)}")
    except ValueError as e:
        logger.warning(f"Invalid token: {str(e)}")
        raise AuthenticationError(str(e))
