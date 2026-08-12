"""
providers/creators_api_provider.py
------------------------------------------------------------------
Amazon Creators API client — the replacement for the retired PA-API 5.0.

╔══════════════════════════════════════════════════════════════════╗
║  STATUS: WRITTEN FROM DOCS — NOT YET VERIFIED AGAINST LIVE API  ║
╚══════════════════════════════════════════════════════════════════╝

This provider was written from Amazon's published Creators API migration
documentation before live credentials were issued. It has NOT been tested
against a real API response. Treat it as a well-researched starting point.

HOW TO VERIFY WHEN CREDENTIALS ARRIVE
--------------------------------------
1. Set in backend/.env:
       DATA_PROVIDER=creators_api
       CREATORS_API_CLIENT_ID=<your-client-id>
       CREATORS_API_CLIENT_SECRET=<your-client-secret>
       AMAZON_ASSOCIATE_TAG=<your-tag-21>

2. Enable debug logging by setting DEBUG_CREATORS_API=true in .env.
   This logs the full raw JSON response for every API call so you can
   inspect actual field names/paths vs. what's assumed below.

3. Start the backend and run a preview in the admin panel with a
   known Amazon.in ASIN. Check the console output for the raw response.

4. Compare actual response fields against _parse_item() below.
   Common things that may differ:
   - "itemsResult" → might be "ItemsResult" (PascalCase in some docs)
   - "offersV2"    → might be "offers" or "Offers"
   - "listings"    → might be "Listings"
   - Price field:  "displayAmount" / "amount" / "value" — varies by version
   - Availability: "message" / "type" / "availability" — varies by version

KNOWN FROM OFFICIAL DOCUMENTATION (confirmed)
----------------------------------------------
- Auth endpoint: https://api.amazon.com/auth/o2/token
- Grant type:    client_credentials
- Scope:         creatorsapi::catalog
- Catalog host:  https://creatorsapi.amazon  (single global host)
- Endpoint path: /catalog/v1/getItems
- Request body fields (lowerCamelCase):
    itemIds, partnerTag, partnerType, marketplace, resources
- partnerType value: "Associates"
- marketplace value: "www.amazon.in" for India
- x-marketplace header: same value as marketplace in body

ASSUMED / UNVERIFIED (may need adjustment)
-------------------------------------------
- Exact shape of itemsResult.items[*]
- Price field path: offersV2.listings[0].price.displayAmount / .amount
- Availability field path: offersV2.listings[0].availability.message
- Image field paths: images.primary.large.url / images.variants[*].large.url
- Features field: itemInfo.features.displayValues (list of strings)
------------------------------------------------------------------
"""

import logging
import os
import time
from typing import Optional

import requests

from app.config import settings
from app.providers.base import ProductData, ProductDataProvider

logger = logging.getLogger("creators_api_provider")

# Enable by setting DEBUG_CREATORS_API=true in .env
# Logs full raw JSON responses — never enable in production.
_DEBUG = os.getenv("DEBUG_CREATORS_API", "false").lower() == "true"

TOKEN_URL = "https://api.amazon.com/auth/o2/token"
CATALOG_HOST = "https://creatorsapi.amazon"
GET_ITEMS_PATH = "/catalog/v1/getItems"
OAUTH_SCOPE = "creatorsapi::catalog"


class CreatorsAPIProvider(ProductDataProvider):
    def __init__(self):
        if not settings.CREATORS_API_CLIENT_ID or not settings.CREATORS_API_CLIENT_SECRET:
            raise RuntimeError(
                "DATA_PROVIDER=creators_api but CREATORS_API_CLIENT_ID or "
                "CREATORS_API_CLIENT_SECRET are not set in .env"
            )
        self._token: Optional[str] = None
        self._token_expires_at: float = 0.0

    # ------------------------------------------------------------------
    # OAuth token management
    # ------------------------------------------------------------------
    def _get_access_token(self) -> Optional[str]:
        """Return a cached token or fetch a new one. Returns None on failure."""
        if self._token and time.time() < self._token_expires_at - 30:
            return self._token

        logger.debug("Fetching new Creators API access token")
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
            if _DEBUG:
                logger.debug("Token response status=%s body=%s", resp.status_code, resp.text[:500])
            resp.raise_for_status()
            data = resp.json()
            self._token = data["access_token"]
            self._token_expires_at = time.time() + data.get("expires_in", 3600)
            logger.debug("Access token obtained, expires in %ss", data.get("expires_in"))
            return self._token
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to obtain Creators API access token: %s", exc)
            return None

    # ------------------------------------------------------------------
    # Product fetch
    # ------------------------------------------------------------------
    def fetch_product(self, asin: str) -> Optional[ProductData]:
        token = self._get_access_token()
        if not token:
            return None

        payload = {
            "itemIds": [asin],
            "partnerTag": settings.AMAZON_ASSOCIATE_TAG,
            "partnerType": "Associates",
            "marketplace": settings.CREATORS_API_MARKETPLACE,
            # VERIFY: check these resource strings match your API version's accepted values
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
            # VERIFY: some docs show "x-amz-marketplace" instead of "x-marketplace"
            "x-marketplace": settings.CREATORS_API_MARKETPLACE,
        }

        logger.debug("Creators API getItems request for ASIN=%s", asin)
        try:
            resp = requests.post(
                f"{CATALOG_HOST}{GET_ITEMS_PATH}",
                json=payload,
                headers=headers,
                timeout=10,
            )
            if _DEBUG:
                logger.debug(
                    "getItems response status=%s body=%s",
                    resp.status_code,
                    resp.text[:2000],  # cap at 2KB to avoid flooding logs
                )
            resp.raise_for_status()
            body = resp.json()
        except Exception as exc:  # noqa: BLE001
            logger.error("Creators API request failed for ASIN %s: %s", asin, exc)
            return None

        # VERIFY: top-level key — might be "ItemsResult" (PascalCase) in some versions
        items = (body.get("itemsResult") or body.get("ItemsResult") or {}).get("items") or []
        if not items:
            logger.warning(
                "No item returned for ASIN %s. Full response keys: %s",
                asin,
                list(body.keys()),
            )
            return None

        return self._parse_item(items[0])

    # ------------------------------------------------------------------
    # Response parsing
    # ------------------------------------------------------------------
    def _parse_item(self, item: dict) -> ProductData:
        """
        Parse a single item from the Creators API response into ProductData.

        ALL field paths below are ASSUMED from documentation and may need
        adjustment once verified against a real response. Enable
        DEBUG_CREATORS_API=true to log the raw response and compare.
        """
        asin = item.get("asin", "UNKNOWN")
        data = ProductData(asin=asin)

        # ---- Title ----
        # VERIFY: path itemInfo.title.displayValue
        try:
            data.title = item["itemInfo"]["title"]["displayValue"]
        except (KeyError, TypeError):
            logger.debug("ASIN %s: could not parse title from %s", asin, list(item.keys()))

        # ---- Features ----
        # VERIFY: path itemInfo.features.displayValues (list of strings)
        try:
            data.features = item["itemInfo"]["features"]["displayValues"]
            if not isinstance(data.features, list):
                data.features = []
        except (KeyError, TypeError):
            data.features = []

        # ---- Price ----
        # VERIFY: offersV2.listings[0].price.displayAmount / .amount / .currency
        try:
            listing = item["offersV2"]["listings"][0]
            data.price_display = listing["price"]["displayAmount"]
            data.price_amount = float(listing["price"]["amount"])
            data.currency = listing["price"].get("currency", "INR")
        except (KeyError, TypeError, IndexError, ValueError):
            logger.debug("ASIN %s: could not parse price", asin)

        # ---- Availability ----
        # VERIFY: offersV2.listings[0].availability.message
        try:
            data.availability = item["offersV2"]["listings"][0]["availability"]["message"]
        except (KeyError, TypeError, IndexError):
            # Fallback heuristic: if we got a price, assume in stock
            data.availability = "unknown" if data.price_display else "Out of Stock"

        # ---- Main image ----
        # VERIFY: images.primary.large.url
        try:
            data.image_large_url = item["images"]["primary"]["large"]["url"]
        except (KeyError, TypeError):
            logger.debug("ASIN %s: could not parse primary image", asin)

        # ---- Variant images ----
        # VERIFY: images.variants[*].large.url
        try:
            data.image_variants = [
                v["large"]["url"]
                for v in item.get("images", {}).get("variants", [])
                if v.get("large") and v["large"].get("url")
            ]
        except (KeyError, TypeError):
            data.image_variants = []

        data.fetch_succeeded = True
        logger.debug(
            "ASIN %s parsed: title=%r price=%s avail=%s",
            asin,
            data.title,
            data.price_display,
            data.availability,
        )
        return data
