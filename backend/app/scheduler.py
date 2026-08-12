"""
scheduler.py
------------------------------------------------------------------
Background scheduler for Raccoon Hub.

Currently runs one job:
  - refresh_all_products: runs once daily, iterates over every active
    product, live-fetches fresh data from the configured provider,
    and updates price / availability / images in the DB.

Uses APScheduler (AsyncIOScheduler) wired into FastAPI's lifespan so
it starts and stops cleanly with the server process.

Why daily and not more frequent?
  - The mock provider has no rate limit so frequency doesn't matter
    locally, but the real Amazon Creators API is rate-limited.
  - Product prices/availability rarely change more than once per day.
  - Visitors who open a product detail page already get a live refresh
    on that individual product, so the catalogue is always fresh for
    actively viewed items regardless of this schedule.
------------------------------------------------------------------
"""

import logging
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import PriceHistory, Product
from app.providers import get_provider

logger = logging.getLogger("scheduler")

# Single shared scheduler instance — imported by main.py
scheduler = AsyncIOScheduler(timezone="UTC")


def refresh_all_products() -> None:
    """
    Fetch fresh data for every active product from the configured provider.
    Runs synchronously inside APScheduler's thread pool executor.
    """
    db: Session = SessionLocal()
    provider = get_provider()
    updated = 0
    failed = 0

    try:
        products = db.query(Product).filter(Product.is_active.is_(True)).all()
        logger.info("Daily refresh starting — %d active products", len(products))

        for product in products:
            try:
                live = provider.fetch_product(product.asin)
                if not live or not live.fetch_succeeded:
                    failed += 1
                    continue

                old_price = product.price_amount

                # Update cached fields
                if live.title:
                    product.title = live.title
                if live.price_display:
                    product.price_display = live.price_display
                if live.price_amount is not None:
                    product.price_amount = live.price_amount
                if live.availability:
                    product.availability = live.availability
                if live.star_rating is not None:
                    product.star_rating = live.star_rating
                if live.review_count is not None:
                    product.review_count = live.review_count
                if live.image_large_url:
                    product.image_large_url = live.image_large_url
                if live.image_variants:
                    product.image_variants = live.image_variants
                if live.features:
                    product.features = live.features
                product.last_fetched_at = datetime.utcnow()

                # Record price history entry if price changed
                new_price = product.price_amount
                if new_price is not None and new_price != old_price:
                    entry = PriceHistory(
                        product_id=product.id,
                        price_amount=new_price,
                        price_display=product.price_display,
                        recorded_at=datetime.utcnow(),
                    )
                    db.add(entry)

                updated += 1

            except Exception as exc:  # noqa: BLE001
                logger.warning("Failed to refresh ASIN %s: %s", product.asin, exc)
                failed += 1

        db.commit()
        logger.info(
            "Daily refresh complete — %d updated, %d failed", updated, failed
        )

    except Exception as exc:  # noqa: BLE001
        logger.error("Daily refresh job crashed: %s", exc)
        db.rollback()
    finally:
        db.close()


def start_scheduler() -> None:
    """Register all jobs and start the scheduler. Called on app startup."""
    scheduler.add_job(
        refresh_all_products,
        trigger=CronTrigger(hour=3, minute=0, timezone="UTC"),  # 3 AM UTC daily
        id="refresh_all_products",
        name="Daily product refresh",
        replace_existing=True,
        misfire_grace_time=3600,   # allow up to 1 hour late start
    )
    scheduler.start()
    logger.info("Scheduler started — daily product refresh at 03:00 UTC")


def stop_scheduler() -> None:
    """Gracefully shut down. Called on app shutdown."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")
