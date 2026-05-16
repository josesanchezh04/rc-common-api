"""Tests for IsAuthenticated permission + get_current_user dependency."""
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
import httpx

from middleware.auth_dependency import AuthenticationError, get_current_user
from middleware.permissions import IsAuthenticated


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_info(token: str = "valid-token", tracking_id: str = "track-1") -> MagicMock:
    request = MagicMock()
    request.headers = {"Authorization": f"Bearer {token}"}
    request.state.tracking_id = tracking_id
    info = MagicMock()
    info.context = {"request": request}
    return info


# ---------------------------------------------------------------------------
# get_current_user tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_current_user_success_stores_user_data_in_context():
    """get_current_user stores validated user_data in info.context on success."""
    user_data = {"firebase_uid": "uid-1", "email": "a@b.com"}
    auth_client_mock = MagicMock()
    auth_client_mock.validate_token = AsyncMock(return_value=user_data)

    info = _make_info("good-token")

    with patch("middleware.auth_dependency.get_auth_client", return_value=auth_client_mock):
        await get_current_user(info)

    assert info.context["user_data"] == user_data
    auth_client_mock.validate_token.assert_awaited_once_with("good-token", "track-1")


@pytest.mark.asyncio
async def test_get_current_user_raises_when_no_token():
    """get_current_user raises AuthenticationError when Authorization header is absent."""
    request = MagicMock()
    request.headers = {}
    request.state.tracking_id = None
    info = MagicMock()
    info.context = {"request": request}

    with pytest.raises(AuthenticationError, match="No Firebase token provided"):
        await get_current_user(info)


@pytest.mark.asyncio
async def test_get_current_user_raises_when_bearer_prefix_missing():
    """get_current_user raises AuthenticationError when token lacks the Bearer prefix."""
    request = MagicMock()
    request.headers = {"Authorization": "token-without-bearer"}
    request.state.tracking_id = None
    info = MagicMock()
    info.context = {"request": request}

    with pytest.raises(AuthenticationError, match="No Firebase token provided"):
        await get_current_user(info)


@pytest.mark.asyncio
async def test_get_current_user_raises_on_http_error():
    """get_current_user wraps httpx.HTTPError in AuthenticationError."""
    auth_client_mock = MagicMock()
    auth_client_mock.validate_token = AsyncMock(
        side_effect=httpx.ConnectError("Connection refused")
    )

    info = _make_info("some-token")
    with patch("middleware.auth_dependency.get_auth_client", return_value=auth_client_mock):
        with pytest.raises(AuthenticationError, match="Token validation failed"):
            await get_current_user(info)


@pytest.mark.asyncio
async def test_get_current_user_raises_on_invalid_token_value_error():
    """get_current_user wraps ValueError (invalid token) in AuthenticationError."""
    auth_client_mock = MagicMock()
    auth_client_mock.validate_token = AsyncMock(side_effect=ValueError("Invalid token"))

    info = _make_info("bad-token")
    with patch("middleware.auth_dependency.get_auth_client", return_value=auth_client_mock):
        with pytest.raises(AuthenticationError, match="Invalid token"):
            await get_current_user(info)


# ---------------------------------------------------------------------------
# IsAuthenticated tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_is_authenticated_returns_true_for_valid_token():
    """IsAuthenticated.has_permission returns True when the token is valid."""
    user_data = {"firebase_uid": "uid-1", "email": "a@b.com"}
    auth_client_mock = MagicMock()
    auth_client_mock.validate_token = AsyncMock(return_value=user_data)

    info = _make_info("valid-token")

    with patch("middleware.auth_dependency.get_auth_client", return_value=auth_client_mock):
        result = await IsAuthenticated().has_permission(source=None, info=info)

    assert result is True


@pytest.mark.asyncio
async def test_is_authenticated_returns_false_for_missing_token():
    """IsAuthenticated.has_permission returns False when no token is present."""
    request = MagicMock()
    request.headers = {}
    request.state.tracking_id = None
    info = MagicMock()
    info.context = {"request": request}

    result = await IsAuthenticated().has_permission(source=None, info=info)

    assert result is False


@pytest.mark.asyncio
async def test_is_authenticated_returns_false_for_invalid_token():
    """IsAuthenticated.has_permission returns False when the token is invalid."""
    auth_client_mock = MagicMock()
    auth_client_mock.validate_token = AsyncMock(side_effect=ValueError("Invalid token"))

    info = _make_info("expired-token")

    with patch("middleware.auth_dependency.get_auth_client", return_value=auth_client_mock):
        result = await IsAuthenticated().has_permission(source=None, info=info)

    assert result is False
