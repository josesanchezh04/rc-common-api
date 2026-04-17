"""Main FastAPI application with GraphQL."""
from fastapi import FastAPI
from strawberry.fastapi import GraphQLRouter
import strawberry
from schema.mutations import Mutation
from schema.queries import Query
from middleware.tracking import RequestTrackingMiddleware
from dotenv import load_dotenv
import os

load_dotenv()

# Create GraphQL schema
schema = strawberry.Schema(query=Query, mutation=Mutation)

# Create GraphQL router
graphql_app = GraphQLRouter(schema)

# Create FastAPI app
app = FastAPI(
    title="BeautyFit API Gateway",
    description="GraphQL API Gateway for BeautyFit microservices",
    version="1.0.0"
)

# Add request tracking middleware
app.add_middleware(RequestTrackingMiddleware)

# Mount GraphQL endpoint
app.include_router(graphql_app, prefix="/graphql")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "BeautyFit API Gateway",
        "version": "1.0.0",
        "graphql": "/graphql"
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("API_GATEWAY_PORT", 4000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
