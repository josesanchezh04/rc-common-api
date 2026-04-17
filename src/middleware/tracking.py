"""Request tracking middleware for distributed tracing."""
import uuid
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable
from shared.logger.logger import set_tracking_id


class RequestTrackingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add tracking ID to all requests.
    
    Features:
    - Generates unique tracking ID for each request
    - Adds tracking ID to response headers
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and add tracking ID.
        
        The tracking_id is stored in request.state and will be automatically
        available in GraphQL context via info.context["request"].state.tracking_id
        
        It is also injected into the logger context, so all logs in this request
        will automatically include the tracking_id.
        
        Args:
            request: Incoming request
            call_next: Next middleware/handler
            
        Returns:
            Response with tracking headers
        """
        # Generate tracking ID
        tracking_id = str(uuid.uuid4())
        
        # Store tracking ID in request state for access in resolvers
        # This will be accessible in GraphQL via info.context["request"].state.tracking_id
        request.state.tracking_id = tracking_id
        
        # Inject tracking_id into logger context for automatic inclusion in all logs
        set_tracking_id(tracking_id)
        
        response = await call_next(request)
            
        # Add tracking headers to response
        response.headers["X-Tracking-ID"] = tracking_id
            
        return response


def get_tracking_id(info) -> str:
    """
    Get tracking ID from GraphQL Info context.
    
    Args:
        info: Strawberry Info object with request in context
        
    Returns:
        Tracking ID string
    """
    request = info.context.get("request")
    if request:
        return getattr(request.state, "tracking_id", "unknown")
    return "unknown"
