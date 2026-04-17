"""GraphQL queries for API Gateway."""
import strawberry
from strawberry.types import Info
from schema.types import User


@strawberry.type
class Query:
    """GraphQL queries."""
    
    @strawberry.field
    async def me(self, info: Info) -> User:
        """Get current authenticated user."""
        # TODO: Implement get current user
        # This would fetch user from context after auth middleware
        user_id = info.context.get("user_id")
        
        # Placeholder
        return User(
            user_id=user_id or "unknown",
            email="user@example.com",
            first_name="John",
            last_name="Doe",
            role="BASIC",
            provider="firebase",
            onboarding_step="COMPLETED",
            phone_verified=False,
            profile_completed=False
        )
