"""Tests for UserServiceClient — register_user_with_data method."""
import json
import pytest
import httpx
import respx

from clients.user_client import UserServiceClient


USER_BASE_URL = "http://user-service:8001"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_client() -> UserServiceClient:
    return UserServiceClient(base_url=USER_BASE_URL)


SAMPLE_USER_DATA = {
    "firebase_uid": "uid-123",
    "email": "john@example.com",
    "email_verified": True,
    "provider": "google.com",
    "display_name": "John Doe",
    "photo_url": None,
    "phone": None,
}

SAMPLE_REGISTERED_USER = {
    "user_id": "uuid-abc",
    "email": "john@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "display_name": "John Doe",
    "photo_url": None,
    "role": "BASIC",
    "provider": "google.com",
    "onboarding_step": "PHONE_VERIFICATION",
    "phone_verified": False,
    "profile_completed": False,
}


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@respx.mock
async def test_register_user_with_data_success():
    """register_user_with_data returns the user dict on a 201 response."""
    respx.post(f"{USER_BASE_URL}/users/register-with-data").mock(
        return_value=httpx.Response(201, json=SAMPLE_REGISTERED_USER)
    )

    client = _make_client()
    result = await client.register_user_with_data(SAMPLE_USER_DATA, tracking_id="track-1")

    assert result["email"] == "john@example.com"
    assert result["role"] == "BASIC"
    assert result["onboarding_step"] == "PHONE_VERIFICATION"
    assert result["phone_verified"] is False


@pytest.mark.asyncio
@respx.mock
async def test_register_user_with_data_sends_user_data_as_json():
    """register_user_with_data forwards user_data verbatim as the request body."""
    route = respx.post(f"{USER_BASE_URL}/users/register-with-data").mock(
        return_value=httpx.Response(201, json=SAMPLE_REGISTERED_USER)
    )

    client = _make_client()
    await client.register_user_with_data(SAMPLE_USER_DATA)

    body = json.loads(route.calls.last.request.content)
    assert body["firebase_uid"] == "uid-123"
    assert body["email"] == "john@example.com"


@pytest.mark.asyncio
@respx.mock
async def test_register_user_with_data_forwards_tracking_id():
    """register_user_with_data includes the X-Tracking-ID header when provided."""
    route = respx.post(f"{USER_BASE_URL}/users/register-with-data").mock(
        return_value=httpx.Response(201, json=SAMPLE_REGISTERED_USER)
    )

    client = _make_client()
    await client.register_user_with_data(SAMPLE_USER_DATA, tracking_id="my-trace-id")

    assert route.calls.last.request.headers.get("X-Tracking-ID") == "my-trace-id"


@pytest.mark.asyncio
@respx.mock
async def test_register_user_with_data_raises_on_http_error():
    """register_user_with_data propagates HTTPStatusError for non-2xx responses."""
    respx.post(f"{USER_BASE_URL}/users/register-with-data").mock(
        return_value=httpx.Response(500, json={"detail": "Internal Server Error"})
    )

    client = _make_client()
    with pytest.raises(httpx.HTTPStatusError):
        await client.register_user_with_data(SAMPLE_USER_DATA)


@pytest.mark.asyncio
@respx.mock
async def test_register_user_with_data_raises_on_conflict():
    """register_user_with_data propagates HTTPStatusError on 409 Conflict."""
    respx.post(f"{USER_BASE_URL}/users/register-with-data").mock(
        return_value=httpx.Response(409, json={"detail": "User already exists"})
    )

    client = _make_client()
    with pytest.raises(httpx.HTTPStatusError):
        await client.register_user_with_data(SAMPLE_USER_DATA)
