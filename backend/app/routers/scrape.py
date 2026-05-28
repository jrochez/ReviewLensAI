from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.models import ScrapeUsage, User
from app.db.session import get_db
from app.dependencies import get_current_user

router = APIRouter(prefix="/scrape", tags=["scrape"])


@router.get("/rate-limit")
async def get_rate_limit(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    window_start = datetime.utcnow() - timedelta(hours=24)

    total_result = await db.execute(
        select(func.sum(ScrapeUsage.reviews_fetched)).where(ScrapeUsage.fetched_at >= window_start)
    )
    total_fetched = total_result.scalar() or 0

    suspended = total_fetched >= settings.BRIGHTDATA_DAILY_REVIEW_LIMIT
    next_available = None

    if suspended:
        oldest_result = await db.execute(
            select(func.min(ScrapeUsage.fetched_at)).where(ScrapeUsage.fetched_at >= window_start)
        )
        oldest_at = oldest_result.scalar()
        if oldest_at:
            next_available = (oldest_at + timedelta(hours=24)).isoformat() + "Z"

    return {
        "daily_limit": settings.BRIGHTDATA_DAILY_REVIEW_LIMIT,
        "reviews_fetched_today": total_fetched,
        "suspended": suspended,
        "next_scrape_available_at": next_available,
    }
