"""
providers/mock_provider.py
------------------------------------------------------------------
Deterministic fake product data generator. Lets you build and test
the entire pipeline - admin preview/confirm, tag extraction, public
listing, product detail page - without any Amazon API access at all.

Set DATA_PROVIDER=mock in .env (the default) to use this. Switch to
DATA_PROVIDER=creators_api once real credentials are issued - no
other code changes needed anywhere else in the app.
------------------------------------------------------------------
"""

import hashlib
import random
from typing import Optional

from app.providers.base import ProductData, ProductDataProvider

_SAMPLE_TITLES = [
    "Wireless Gaming Mouse, 16000 DPI, RGB Lighting, Ergonomic Grip",
    "Mechanical Keyboard, Hot-Swappable Switches, 104 Keys, RGB Backlit",
    "Over-Ear Wireless Headphones, 40H Battery, Active Noise Cancelling",
    "27-inch Gaming Monitor, 165Hz, 1ms Response Time, IPS Panel",
    "USB Condenser Microphone, Cardioid Pattern, Plug and Play",
    "1080p HD Webcam with Built-in Microphone, Auto Light Correction",
    "10000mAh Power Bank, 22.5W Fast Charging, Dual USB Output",
    "Bluetooth 5.3 Portable Speaker, 12W Output, IPX7 Waterproof",
]

_SAMPLE_FEATURES = [
    "Adjustable weight tuning system",
    "Wireless charging compatible",
    "Customizable RGB lighting zones",
    "Ergonomic design for extended use",
    "Durable braided cable",
    "Plug-and-play, no drivers required",
    "Compact and portable design",
    "Long battery life on a single charge",
]


class MockProductProvider(ProductDataProvider):
    """Generates realistic-looking but entirely fake product data."""

    def fetch_product(self, asin: str) -> Optional[ProductData]:
        if not asin:
            return None

        # Deterministic per-ASIN pseudo-randomness, so re-fetching the same
        # ASIN gives consistent results while testing the admin panel.
        seed = int(hashlib.sha256(asin.encode()).hexdigest(), 16) % (2**32)
        rng = random.Random(seed)

        title = rng.choice(_SAMPLE_TITLES)
        price_amount = round(rng.uniform(299, 24999), 2)
        features = rng.sample(_SAMPLE_FEATURES, k=rng.randint(3, 5))

        return ProductData(
            asin=asin,
            title=f"{title} [MOCK DATA - {asin}]",
            price_display=f"\u20b9{price_amount:,.2f}",
            price_amount=price_amount,
            currency="INR",
            availability="In Stock",
            star_rating=None,
            review_count=None,
            image_large_url=f"https://placehold.co/500x500?text={asin}",
            image_variants=[
                f"https://placehold.co/500x500?text={asin}-2",
                f"https://placehold.co/500x500?text={asin}-3",
            ],
            features=features,
            fetch_succeeded=True,
        )