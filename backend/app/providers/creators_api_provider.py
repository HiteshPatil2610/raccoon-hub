"""
providers/creators_api_provider.py
------------------------------------------------------------------
Amazon Creators API client - the replacement for the now-retired
PA-API 5.0.

*** IMPORTANT - UNVERIFIED ***
This is written from Amazon's published Creators API migration
documentation. It has NOT been tested against a live response,
because Creators API credentials have not yet been issued for this
Associates account. Treat this as a strong, well-researched starting
point - not a guarantee. Once real CREATORS_API_CLIENT_ID /
CREATORS_API_CLIENT_SECRET are available, expect to spend a short
debugging pass here matching exact field names/paths against real
response payloads (Amazon's docs for this API were incomplete/newly
published at the time this was written).

Known from documentation:
  - Auth: OAuth 2.0 client-credentials flow via Login-With-Amazon,
    exchanged for a short-lived bearer access token.
  - Host: creatorsapi.amazon (single global host - no per-region host,
    unlike the old PA-API).
  - Region/marketplace is selected via request body + x-marketplace
    header, not via host/region like the old SDK.
  - Field names are lowerCamelCase (itemIds, partnerTag), not
    PascalCase like the old PA-API.
------------------------------------------------------------------
"""

import logging
import time
from typing import Optional

import requests

from app.config import settings
from app.providers.base import ProductData, ProductDataProvider

logger = logging.getLogger("creators_api_provider")

# NOTE: verify this against the exact token URL shown on your Creators API
# credential page in Associates Central - LWA token endpoints have varied
# by credential version (v2.x vs v3.x) in Amazon's own documentation.
TOKEN_URL = "https://api.amazon.com/auth/o2/token"
CATALOG_HOST = "https://creatorsapi.amazon"
GET_ITEMS_PATH = "/catalog/v1/getItems"

# NOTE: verify this scope string against your credential page too.
OAUTH_SCOPE = "creatorsapi::catalog"


class CreatorsAPIProvider(ProductDataProvider):
    def __init__(self):
        if not settings.CREATORS_API_CLIENT_ID or not settings.CREATORS_API_CLIENT_SECRET:
            raise RuntimeError(
                "DATA_PROVIDER=creators_api but CREATORS_API_CLIENT_ID/"
                "CREATORS_API_CLIENT_SECRET are not set in .env"
            )
        self._token: Optional[str] = None
        self._token_expires_at: float = 0.0

    def _get_access_token(self) -> Optional[str]:
        if self._token and time.time() < self._token_expires_at - 30:
            return self._token

        try:
            resp = requests.post(
                TOKEN_URL,
                data={
                    "grant_type": "client_credentials",
                    "client_id": settings.CREATORS_API_CLIENT_ID,
                    "client_secret": settings.CREATORS_API_CLIENT_SECRET,
                    "scope": OAUTH_SCOPE,
                },
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()
            self._token = data["access_token"]
            self._token_expires_at = time.time() + data.get("expires_in", 3600)
            return self._token
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to obtain Creators API access token: %s", exc)
            return None

    def fetch_product(self, asin: str) -> Optional[ProductData]:
        token = self._get_access_token()
        if not token:
            return None

        payload = {
            "itemIds": [asin],
            "partnerTag": settings.AMAZON_ASSOCIATE_TAG,
            "partnerType": "Associates",
            "marketplace": settings.CREATORS_API_MARKETPLACE,
            "resources": [
                "itemInfo.title",
                "itemInfo.features",
                "offersV2.listings.price",
                "offersV2.listings.availability",
                "images.primary.large",
                "images.variants.large",
            ],
        }
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "x-marketplace": settings.CREATORS_API_MARKETPLACE,
        }

        try:
            resp = requests.post(
                f"{CATALOG_HOST}{GET_ITEMS_PATH}",
                json=payload,
                headers=headers,
                timeout=10,
            )
            resp.raise_for_status()
            body = resp.json()
        except Exception as exc:  # noqa: BLE001
            logger.error("Creators API request failed for ASIN %s: %s", asin, exc)
            return None

        items = (body.get("itemsResult") or {}).get("items") or []
        if not items:
            logger.warning("No item returned for ASIN %s", asin)
            return None

        return self._parse_item(items[0])

    def _parse_item(self, item: dict) -> ProductData:
        asin = item.get("asin", "UNKNOWN")
        data = ProductData(asin=asin)

        try:
            data.title = item["itemInfo"]["title"]["displayValue"]
        except (KeyError, TypeError):
            pass

        try:
            data.features = item["itemInfo"]["features"]["displayValues"]
        except (KeyError, TypeError):
            data.features = []

        try:
            listing = item["offersV2"]["listings"][0]
            data.price_display = listing["price"]["displayAmount"]
            data.price_amount = float(listing["price"]["amount"])
            data.currency = listing["price"]["currency"]
        except (KeyError, TypeError, IndexError, ValueError):
            pass

        try:
            data.availability = item["offersV2"]["listings"][0]["availability"]["message"]
        except (KeyError, TypeError, IndexError):
            data.availability = "out_of_stock" if data.price_display is None else "unknown"

        try:
            data.image_large_url = item["images"]["primary"]["large"]["url"]
        except (KeyError, TypeError):
            pass

        try:
            data.image_variants = [
                v["large"]["url"]
                for v in item.get("images", {}).get("variants", [])
                if v.get("large")
            ]
        except (KeyError, TypeError):
            data.image_variants = []

        data.fetch_succeeded = True
        return data