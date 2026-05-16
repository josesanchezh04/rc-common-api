"""GCP Authentication utilities for Service-to-Service internal networking."""
import httpx
from typing import Optional

from beautyfit_logger import get_logger
from config.settings import get_settings

logger = get_logger("GCPAuth")

# Google Cloud Metadata Server URL
# See: https://cloud.google.com/run/docs/authenticating/service-to-service
METADATA_SERVER_URL = (
    "http://metadata.google.internal/computeMetadata/v1"
    "/instance/service-accounts/default/identity"
)


async def get_oidc_token(audience: str) -> Optional[str]:
    """Fetch an OIDC identity token from the GCP Metadata server.

    Works automatically when running inside Cloud Run or other GCP compute
    instances. Returns ``None`` outside of production so local development is
    unaffected.

    Args:
        audience: URL of the receiving internal service
            (e.g. ``https://user-service-xyz.run.app``).

    Returns:
        The OIDC token string, or ``None`` if not in production or on error.
    """
    settings = get_settings()

    if settings.env != "production":
        logger.debug(f"Bypassing OIDC token fetch in '{settings.env}' environment.")
        return None

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                METADATA_SERVER_URL,
                params={"audience": audience},
                headers={"Metadata-Flavor": "Google"}
            )
            response.raise_for_status()
            token = response.text
            logger.debug(f"Successfully fetched OIDC token for audience: {audience}")
            return token
    except httpx.HTTPStatusError as err:
        logger.warning(
            f"Failed to fetch OIDC token (HTTP {err.response.status_code}). "
            f"Proceeding without authentication. Audience: {audience}"
        )
        return None
    except httpx.HTTPError as err:
        logger.warning(
            f"Failed to fetch OIDC token: {err}. "
            f"Proceeding without authentication. Audience: {audience}"
        )
        return None
