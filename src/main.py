"""Main FastAPI application with GraphQL."""
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import strawberry
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from strawberry.fastapi import GraphQLRouter

from clients.auth_client import close_auth_client
from clients.user_client import close_user_client
from config.settings import get_settings
from middleware.tracking import RequestTrackingMiddleware
from schema.mutations import Mutation
from schema.queries import Query
from beautyfit_logger import configure_logger, get_logger

load_dotenv()

configure_logger(service_name="rc-api")
logger = get_logger("ServiceStartup")


# ---------------------------------------------------------------------------
# Lifespan — startup / shutdown
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application lifespan events.

    On startup: logs the environment and port.
    On shutdown: gracefully closes all HTTP clients.
    """
    settings = get_settings()
    logger.info(f"Starting API Gateway [env={settings.env}, port={settings.api_gateway_port}]")
    yield
    logger.info("Shutting down — closing HTTP clients")
    await close_auth_client()
    await close_user_client()


# ---------------------------------------------------------------------------
# GraphQL schema
# ---------------------------------------------------------------------------

schema = strawberry.Schema(query=Query, mutation=Mutation)
graphql_app = GraphQLRouter(schema)

# ---------------------------------------------------------------------------
# FastAPI application
# ---------------------------------------------------------------------------

app = FastAPI(
    title="BeautyFit API Gateway",
    description="GraphQL API Gateway for BeautyFit microservices",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(RequestTrackingMiddleware)
app.include_router(graphql_app, prefix="/graphql")


# ---------------------------------------------------------------------------
# Custom exception handlers
# ---------------------------------------------------------------------------

@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Return a structured 500 response instead of leaking a stack trace."""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


# ---------------------------------------------------------------------------
# REST endpoints
# ---------------------------------------------------------------------------

@app.get("/")
async def root() -> dict:
    """Service discovery endpoint."""
    return {
        "service": "BeautyFit API Gateway",
        "version": "1.0.0",
        "graphql": "/graphql",
    }


@app.get("/health")
async def health() -> dict:
    """Liveness probe for Cloud Run / load balancers."""
    return {"status": "healthy"}


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run("main:app", host="0.0.0.0", port=settings.api_gateway_port, reload=True)

