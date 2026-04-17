"""Permission classes for GraphQL resolvers (similar to NestJS guards)."""
from typing import Any
import strawberry
from strawberry.types import Info
from strawberry.permission import BasePermission
from middleware.auth_dependency import get_current_user, AuthenticationError


class IsAuthenticated(BasePermission):
    """
    Permission class to validate authentication.
    
    Similar to NestJS guards, this validates the token before the resolver executes.
    If validation succeeds, user_data is stored in the context for use in resolvers.
    """
    
    message = "User is not authenticated"
    
    async def has_permission(self, source: Any, info: Info, **kwargs) -> bool:
        """
        Validate if user is authenticated.
        
        This will be called before the resolver executes.
        If successful, user_data is stored in info.context["user_data"].
        
        Args:
            source: The source object (parent resolver result)
            info: Strawberry Info object with context
            **kwargs: Additional arguments
            
        Returns:
            True if authenticated, False otherwise
        """
        try:
            # Validate token and get user data
            # get_current_user already stores user_data in context
            await get_current_user(info)
            return True
        except AuthenticationError:
            return False
