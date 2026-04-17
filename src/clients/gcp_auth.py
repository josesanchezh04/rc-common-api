"""GCP Authentication utilities for Service-to-Service internal networking."""
import os
import httpx
from typing import Optional
from loguru import logger

# Google Cloud Metadata Server URL
# See: https://cloud.google.com/run/docs/authenticating/service-to-service
METADATA_SERVER_URL = "http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/identity"

async def get_oidc_token(audience: str) -> Optional[str]:
    """
    Asynchronously fetches an Identity (OIDC) token from the GCP Metadata server.
    This works automatically when running inside Cloud Run or other GCP compute instances.
    
    Args:
        audience: The URL of the receiving internal service (e.g., https://user-service-xyz.run.app)
        
    Returns:
        The OIDC token as a string, or None if not running in GCP or an error occurs.
    """
    # Bypass in local development
    if os.getenv("ENV", "development").lower() != "production":
        logger.debug(f"Bypassing OIDC token fetch in {os.getenv('ENV')} environment.")
        return None

    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            response = await client.get(
                METADATA_SERVER_URL,
                params={"audience": audience},
                headers={"Metadata-Flavor": "Google"}
            )
            response.raise_for_status()
            return response.text
    except httpx.HTTPError as err:
        logger.error(f"Failed to fetch OIDC token from Metadata server: {err}")
        return None
