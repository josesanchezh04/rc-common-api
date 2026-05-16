"""Shared pytest fixtures for rc-common-api tests."""
import os
import pytest

# ---------------------------------------------------------------------------
# Inject required environment variables before any app import
# ---------------------------------------------------------------------------

os.environ.setdefault("ENV", "development")
os.environ.setdefault("API_GATEWAY_PORT", "4000")
os.environ.setdefault("MS__AUTH_SERVICE_URL", "http://auth-service:8000")
os.environ.setdefault("MS__USER_SERVICE_URL", "http://user-service:8001")
