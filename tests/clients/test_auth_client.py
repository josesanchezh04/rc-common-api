"""Tests for AuthServiceClient — validate_token method."""
import pytest
import httpx
import respx

from clients.auth_client import AuthServiceClient


AUTH_BASE_URL = "http://auth-service:8000"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_client() -> AuthServiceClient:
    return AuthServiceClient(base_url=AUTH_BASE_URL)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@respx.mock
async def test_validate_token_success():
    """validate_token returns user_data dict when the token is valid."""
    user_data = {
        "firebase_uid": "uid-123",
        "email": "john@example.com",
        "email_verified": True,
        "provider": "google.com",
        "display_name": "John Doe",
    }
    respx.post(f"{AUTH_BASE_URL}/auth/validate").mock(
        return_value=httpx.Response(200, json={"valid": True, "user_data": user_data})
    )

    client = _make_client()
    result = await client.validate_token("firebase-token-abc", tracking_id="track-1")

    assert result["firebase_uid"] == "uid-123"
    assert result["email"] == "john@example.com"
    assert result["provider"] == "google.com"


@pytest.mark.asyncio
@respx.mock
async def test_validate_token_sends_correct_payload():
    """validate_token posts the token in the expected JSON body."""
    route = respx.post(f"{AUTH_BASE_URL}/auth/validate").mock(
        return_value=httpx.Response(
            200, json={"valid": True, "user_data": {"firebase_uid": "uid-1", "email": "a@b.com"}}
        )
    )

    client = _make_client()
    await client.validate_token("my-firebase-token")

    sent_payload = route.calls.last.request.content
    import json
    body = json.loads(sent_payload)
    assert body == {"firebase_token": "my-firebase-token"}


@pytest.mark.asyncio
@respx.mock
async def test_validate_token_raises_value_error_when_invalid():
    """validate_token raises ValueError when the auth-service reports the token as invalid."""
    respx.post(f"{AUTH_BASE_URL}/auth/validate").mock(
        return_value=httpx.Response(200, json={"valid": False})
    )

    client = _make_client()
    with pytest.raises(ValueError, match="Invalid token"):
        await client.validate_token("bad-token")


@pytest.mark.asyncio
@respx.mock
async def test_validate_token_raises_on_http_error():
    """validate_token propagates HTTPStatusError for non-2xx responses."""
    respx.post(f"{AUTH_BASE_URL}/auth/validate").mock(
        return_value=httpx.Response(401, json={"detail": "Unauthorized"})
    )

    client = _make_client()
    with pytest.raises(httpx.HTTPStatusError):
        await client.validate_token("expired-token")


@pytest.mark.asyncio
@respx.mock
async def test_validate_token_returns_empty_user_data_when_key_missing():
    """validate_token returns an empty dict if user_data key is absent (graceful fallback)."""
    respx.post(f"{AUTH_BASE_URL}/auth/validate").mock(
        return_value=httpx.Response(200, json={"valid": True})
    )

    client = _make_client()
    result = await client.validate_token("token-without-user-data")
    assert result == {}
