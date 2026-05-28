import asyncio
import logging
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.models import Dataset, DatasetTheme, Review, ScrapeUsage
from app.db.session import AsyncSessionLocal
from app.security import blocklist
from app.services.scraper import RawReview, get_scraper

logger = logging.getLogger(__name__)

SCRAPE_TIMEOUT_SECONDS = 600  # 10 minutes


def _sentiment(star_rating: int) -> str:
    if star_rating >= 4:
        return "positive"
    if star_rating == 3:
        return "neutral"
    return "negative"


def _sanitize(text: str) -> tuple[str, bool]:
    truncated = text[: 2000]
    cleaned, detected = blocklist.scan(truncated)
    return cleaned, detected


async def check_budgets(db: AsyncSession, user_id: str) -> tuple[bool, datetime | None]:
    """Return (is_ok, next_available_at). next_available_at is set when budget exceeded."""
    window_start = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=24)

    # Global budget
    global_sum_result = await db.execute(
        select(func.sum(ScrapeUsage.reviews_fetched)).where(ScrapeUsage.fetched_at >= window_start)
    )
    global_used = global_sum_result.scalar() or 0
    if global_used >= settings.BRIGHTDATA_DAILY_REVIEW_LIMIT:
        oldest = await db.execute(
            select(func.min(ScrapeUsage.fetched_at)).where(ScrapeUsage.fetched_at >= window_start)
        )
        oldest_at = oldest.scalar()
        next_at = oldest_at + timedelta(hours=24) if oldest_at else datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(hours=24)
        return False, next_at

    # Per-user budget
    user_sum_result = await db.execute(
        select(func.sum(ScrapeUsage.reviews_fetched)).where(
            ScrapeUsage.fetched_at >= window_start,
            ScrapeUsage.user_id == user_id,
        )
    )
    user_used = user_sum_result.scalar() or 0
    if user_used >= settings.BRIGHTDATA_PER_USER_DAILY_LIMIT:
        oldest = await db.execute(
            select(func.min(ScrapeUsage.fetched_at)).where(
                ScrapeUsage.fetched_at >= window_start,
                ScrapeUsage.user_id == user_id,
            )
        )
        oldest_at = oldest.scalar()
        next_at = oldest_at + timedelta(hours=24) if oldest_at else datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(hours=24)
        return False, next_at

    return True, None


async def run_scrape_job(dataset_id: str, user_id: str):
    """Background task: scrape → sanitize → upsert → embed → themes → ready."""
    scraper = get_scraper()

    async with AsyncSessionLocal() as db:
        try:
            dataset = await db.get(Dataset, dataset_id)
            if not dataset:
                logger.error("Dataset %s not found for scrape job", dataset_id)
                return

            dataset.status = "scraping"
            await db.commit()

            # Submit job
            try:
                job_id = await asyncio.to_thread(scraper.submit_job, dataset.asin)
            except Exception as exc:
                logger.error("Failed to submit scrape job: %s", exc)
                dataset.status = "error"
                dataset.error_message = f"Failed to submit job: {exc}"
                await db.commit()
                return

            dataset.scrape_job_id = job_id
            await db.commit()

            # Poll with timeout
            deadline = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(seconds=SCRAPE_TIMEOUT_SECONDS)
            from app.services.scraper import JobStatus
            while True:
                if datetime.now(timezone.utc).replace(tzinfo=None) > deadline:
                    dataset.status = "error"
                    dataset.error_message = "Scrape job timed out after 10 minutes."
                    await db.commit()
                    return

                try:
                    status = await asyncio.to_thread(scraper.poll_job, job_id)
                except Exception as exc:
                    logger.warning("Poll error: %s", exc)
                    await asyncio.sleep(10)
                    continue

                if status == JobStatus.complete:
                    break
                if status == JobStatus.error:
                    dataset.status = "error"
                    dataset.error_message = "Bright Data returned an error status."
                    await db.commit()
                    return

                await asyncio.sleep(10)

            # Fetch results
            try:
                raw_reviews: list[RawReview] = await asyncio.to_thread(scraper.fetch_results, job_id)
            except Exception as exc:
                dataset.status = "error"
                dataset.error_message = f"Failed to fetch results: {exc}"
                await db.commit()
                return

            raw_reviews = raw_reviews[: settings.BRIGHTDATA_MAX_REVIEWS_PER_ASIN]

            # Upsert reviews
            total_sanitized_detected = False
            for raw in raw_reviews:
                clean_text, detected = _sanitize(raw.review_text)
                if detected:
                    total_sanitized_detected = True

                existing = await db.execute(
                    select(Review).where(
                        Review.dataset_id == dataset_id,
                        Review.external_review_id == raw.external_review_id,
                    )
                )
                existing_review = existing.scalar_one_or_none()

                if existing_review:
                    existing_review.review_text = clean_text
                    existing_review.star_rating = raw.star_rating
                    existing_review.reviewer_name = raw.reviewer_name
                    existing_review.review_date = raw.review_date
                    existing_review.verified_purchase = raw.verified_purchase
                    existing_review.helpful_votes = raw.helpful_votes
                    existing_review.sentiment_label = _sentiment(raw.star_rating)
                else:
                    new_review = Review(
                        id=str(uuid4()),
                        dataset_id=dataset_id,
                        external_review_id=raw.external_review_id,
                        review_text=clean_text,
                        star_rating=raw.star_rating,
                        reviewer_name=raw.reviewer_name,
                        review_date=raw.review_date,
                        verified_purchase=raw.verified_purchase,
                        helpful_votes=raw.helpful_votes,
                        sentiment_label=_sentiment(raw.star_rating),
                    )
                    db.add(new_review)

            await db.commit()

            # Record usage
            usage = ScrapeUsage(
                id=str(uuid4()),
                dataset_id=dataset_id,
                user_id=user_id,
                reviews_fetched=len(raw_reviews),
                fetched_at=datetime.now(timezone.utc).replace(tzinfo=None),
            )
            db.add(usage)
            await db.commit()

            # Update dataset stats
            stats_result = await db.execute(
                select(
                    func.count(Review.id),
                    func.avg(Review.star_rating),
                    func.min(Review.review_date),
                    func.max(Review.review_date),
                ).where(Review.dataset_id == dataset_id)
            )
            count, avg_rating, date_min, date_max = stats_result.one()

            dataset.review_count = count
            dataset.avg_star_rating = round(float(avg_rating), 1) if avg_rating else None
            dataset.review_date_min = date_min
            dataset.review_date_max = date_max
            dataset.last_scraped_at = datetime.now(timezone.utc).replace(tzinfo=None)

            # Try to set product name from first review's context (mock sets asin-based)
            if not dataset.product_name:
                dataset.product_name = f"Product {dataset.asin}"
                dataset.product_url = f"https://www.amazon.com/dp/{dataset.asin}"

            await db.commit()

            # Theme extraction
            try:
                from app.services.themes import extract_themes
                all_texts_result = await db.execute(
                    select(Review.review_text).where(Review.dataset_id == dataset_id)
                )
                texts = [row[0] for row in all_texts_result.fetchall()]
                theme_pairs = await asyncio.to_thread(extract_themes, texts)

                existing_themes = await db.execute(
                    select(DatasetTheme).where(DatasetTheme.dataset_id == dataset_id)
                )
                for t in existing_themes.scalars().all():
                    await db.delete(t)

                for theme_text, freq in theme_pairs:
                    db.add(DatasetTheme(
                        id=str(uuid4()),
                        dataset_id=dataset_id,
                        theme=theme_text,
                        frequency=freq,
                    ))
                await db.commit()
            except Exception as exc:
                logger.warning("Theme extraction failed: %s", exc)

            # Embeddings / ChromaDB
            try:
                from app.services.rag import index_dataset
                await index_dataset(dataset_id, db)
            except Exception as exc:
                logger.warning("Embedding/indexing failed: %s", exc)

            dataset.status = "ready"
            await db.commit()
            logger.info("Dataset %s scrape complete: %d reviews", dataset_id, len(raw_reviews))

        except Exception as exc:
            logger.exception("Unhandled error in scrape job for dataset %s: %s", dataset_id, exc)
            try:
                dataset = await db.get(Dataset, dataset_id)
                if dataset:
                    dataset.status = "error"
                    dataset.error_message = "An unexpected error occurred during scraping."
                    await db.commit()
            except Exception:
                pass
