"""Tests for the register GraphQL mutation resolver (rc-common-api).

Strategy
--------
* The resolver is tested at unit level by directly calling ``Mutation.register``.
* ``IsAuthenticated`` and ``get_current_user`` are fully tested in a separate file
  (``test_permissions.py``).  Here we assume the permission guard has already
  populated ``info.context["user_data"]``.
* ``_user_client()`` (the singleton factory) is patched with ``unittest.mock.patch``
  so no real HTTP calls are made.
"""
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from schema.mutations import Mutation


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------

SAMPLE_USER_DATA = {
    "firebase_uid": "uid-123",
    "email": "john@example.com",
    "email_verified": True,
    "provider": "google.com",
    "display_name": "John Doe",
    "photo_url": "https://example.com/photo.jpg",
    "phone": None,
}

SAMPLE_REGISTERED_USER = {
    "user_id": "uuid-abc",
    "email": "john@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "display_name": "John Doe",
    "photo_url": "https://example.com/photo.jpg",
    "role": "BASIC",
    "provider": "google.com",
    "onboarding_step": "PHONE_VERIFICATION",
    "phone_verified": False,
    "profile_completed": False,
}


def _make_info(user_data: dict, tracking_id: str = "track-1") -> MagicMock:
    """Build a minimal Strawberry Info mock with context pre-populated.

    ``get_tracking_id`` reads from ``info.context["request"].state.tracking_id``,
    so we must wire that path on the mock.
    """
    request = MagicMock()
    request.state.tracking_id = tracking_id
    info = MagicMock()
    info.context = {
        "user_data": user_data,
        "request": request,
    }
    return info


def _make_user_client_mock(return_value: dict) -> MagicMock:
    """Return a mock UserServiceClient whose register_user_with_data is an AsyncMock."""
    client_mock = MagicMock()
    client_mock.register_user_with_data = AsyncMock(return_value=return_value)
    return client_mock


# ---------------------------------------------------------------------------
# Tests — resolver happy path
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_register_returns_user_type():
    """register() maps the user-service response into a User Strawberry type."""
    info = _make_info(SAMPLE_USER_DATA)
    client_mock = _make_user_client_mock(SAMPLE_REGISTERED_USER)

    with patch("schema.mutations._user_client", return_value=client_mock):
        result = await Mutation().register(info)

    assert result.user_id == "uuid-abc"
    assert result.email == "john@example.com"
    assert result.first_name == "John"
    assert result.last_name == "Doe"
    assert result.display_name == "John Doe"
    assert result.photo_url == "https://example.com/photo.jpg"
    assert result.role == "BASIC"
    assert result.provider == "google.com"
    assert result.onboarding_step == "PHONE_VERIFICATION"
    assert result.phone_verified is False
    assert result.profile_completed is False


@pytest.mark.asyncio
async def test_register_calls_user_service_with_context_user_data():
    """register() passes info.context['user_data'] to the user-service client."""
    info = _make_info(SAMPLE_USER_DATA, tracking_id="my-tracking-id")
    client_mock = _make_user_client_mock(SAMPLE_REGISTERED_USER)

    with patch("schema.mutations._user_client", return_value=client_mock):
        await Mutation().register(info)

    client_mock.register_user_with_data.assert_awaited_once_with(
        SAMPLE_USER_DATA, "my-tracking-id"
    )


@pytest.mark.asyncio
async def test_register_fallback_user_id_from_context():
    """register() falls back to firebase_uid when user_id is absent in the response."""
    response_without_user_id = {k: v for k, v in SAMPLE_REGISTERED_USER.items() if k != "user_id"}
    info = _make_info(SAMPLE_USER_DATA)
    client_mock = _make_user_client_mock(response_without_user_id)

    with patch("schema.mutations._user_client", return_value=client_mock):
        result = await Mutation().register(info)

    assert result.user_id == SAMPLE_USER_DATA["firebase_uid"]


@pytest.mark.asyncio
async def test_register_defaults_when_fields_missing():
    """register() uses safe defaults for optional fields absent in the response."""
    minimal_response = {
        "email": "jane@example.com",
    }
    info = _make_info({"firebase_uid": "uid-456", "email": "jane@example.com"})
    client_mock = _make_user_client_mock(minimal_response)

    with patch("schema.mutations._user_client", return_value=client_mock):
        result = await Mutation().register(info)

    assert result.email == "jane@example.com"
    assert result.first_name == ""
    assert result.last_name == ""
    assert result.role == "BASIC"
    assert result.provider == "firebase"
    assert result.onboarding_step == "PHONE_VERIFICATION"
    assert result.phone_verified is False
    assert result.profile_completed is False


@pytest.mark.asyncio
async def test_register_with_phone_verified_user():
    """register() correctly reflects phone_verified=True and PROFILE_COMPLETION step."""
    response = {
        **SAMPLE_REGISTERED_USER,
        "phone_verified": True,
        "onboarding_step": "PROFILE_COMPLETION",
    }
    info = _make_info(SAMPLE_USER_DATA)
    client_mock = _make_user_client_mock(response)

    with patch("schema.mutations._user_client", return_value=client_mock):
        result = await Mutation().register(info)

    assert result.phone_verified is True
    assert result.onboarding_step == "PROFILE_COMPLETION"


@pytest.mark.asyncio
async def test_register_propagates_user_service_error():
    """register() propagates exceptions raised by the user-service client."""
    import httpx
    info = _make_info(SAMPLE_USER_DATA)
    client_mock = MagicMock()
    client_mock.register_user_with_data = AsyncMock(
        side_effect=httpx.HTTPStatusError(
            "500",
            request=MagicMock(),
            response=MagicMock(status_code=500),
        )
    )

    with patch("schema.mutations._user_client", return_value=client_mock):
        with pytest.raises(httpx.HTTPStatusError):
            await Mutation().register(info)
