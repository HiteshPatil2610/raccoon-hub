"""
providers/__init__.py
------------------------------------------------------------------
Factory returning the active product-data provider, chosen by
DATA_PROVIDER in .env. Every other module (routers/admin.py,
routers/public.py) should import get_provider() from here rather
than instantiating a provider directly - this is the single switch
point for going from mock data to the real Creators API.
------------------------------------------------------------------
"""

from functools import lru_cache

from app.config import settings
from app.providers.base import ProductData, ProductDataProvider  # noqa: F401 (re-exported)
from app.providers.creators_api_provider import CreatorsAPIProvider
from app.providers.mock_provider import MockProductProvider


@lru_cache
def get_provider() -> ProductDataProvider:
    if settings.DATA_PROVIDER == "creators_api":
        return CreatorsAPIProvider()
    return MockProductProvider()