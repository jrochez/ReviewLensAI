from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import Integer, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Dataset, DatasetTheme, Review, User
from app.db.session import get_db
from app.dependencies import get_current_user

router = APIRouter(prefix="/datasets", tags=["reviews"])


@router.get("/{dataset_id}/reviews")
async def list_reviews(
    dataset_id: str,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    sort: str = Query("date_desc", pattern="^(date_asc|date_desc|stars_asc|stars_desc)$"),
    stars: str | None = Query(None),
    verified: str | None = Query(None, pattern="^(true|false)$"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ds = await db.get(Dataset, dataset_id)
    if not ds:
        raise HTTPException(status_code=404, detail={"error_code": "DATASET_NOT_FOUND", "message": f"No dataset with id {dataset_id}"})

    q = select(Review).where(Review.dataset_id == dataset_id)

    if stars:
        star_list = [int(s.strip()) for s in stars.split(",") if s.strip().isdigit()]
        if star_list:
            q = q.where(Review.star_rating.in_(star_list))

    if verified is not None:
        q = q.where(Review.verified_purchase == (verified == "true"))

    sort_map = {
        "date_asc": Review.review_date.asc(),
        "date_desc": Review.review_date.desc(),
        "stars_asc": Review.star_rating.asc(),
        "stars_desc": Review.star_rating.desc(),
    }
    q = q.order_by(sort_map.get(sort, Review.review_date.desc()))

    count_result = await db.execute(select(func.count()).select_from(q.subquery()))
    total = count_result.scalar() or 0

    offset = (page - 1) * per_page
    paginated = await db.execute(q.offset(offset).limit(per_page))
    reviews = paginated.scalars().all()

    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "reviews": [
            {
                "id": r.id,
                "star_rating": r.star_rating,
                "reviewer_name": r.reviewer_name,
                "review_date": r.review_date,
                "verified_purchase": r.verified_purchase,
                "helpful_votes": r.helpful_votes,
                "review_text": r.review_text,
                "sentiment_label": r.sentiment_label,
            }
            for r in reviews
        ],
    }


@router.get("/{dataset_id}/summary")
async def get_summary(
    dataset_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ds = await db.get(Dataset, dataset_id)
    if not ds:
        raise HTTPException(status_code=404, detail={"error_code": "DATASET_NOT_FOUND", "message": f"No dataset with id {dataset_id}"})

    total_result = await db.execute(
        select(func.count(Review.id)).where(Review.dataset_id == dataset_id)
    )
    total = total_result.scalar() or 0

    verified_result = await db.execute(
        select(func.count(Review.id)).where(
            Review.dataset_id == dataset_id,
            Review.verified_purchase == True,
        )
    )
    verified_count = verified_result.scalar() or 0

    sentiment_counts = {"positive": 0, "neutral": 0, "negative": 0}
    for label in ["positive", "neutral", "negative"]:
        result = await db.execute(
            select(func.count(Review.id)).where(
                Review.dataset_id == dataset_id,
                Review.sentiment_label == label,
            )
        )
        sentiment_counts[label] = result.scalar() or 0

    themes_result = await db.execute(
        select(DatasetTheme.theme, DatasetTheme.frequency)
        .where(DatasetTheme.dataset_id == dataset_id)
        .order_by(DatasetTheme.frequency.desc())
        .limit(30)
    )
    themes = [{"theme": row[0], "frequency": row[1]} for row in themes_result.fetchall()]

    def pct(n: int) -> float:
        return round(n / total * 100, 1) if total > 0 else 0.0

    return {
        "stats": {
            "review_count": total,
            "avg_star_rating": ds.avg_star_rating,
            "review_date_min": ds.review_date_min,
            "review_date_max": ds.review_date_max,
            "verified_count": verified_count,
            "unverified_count": total - verified_count,
        },
        "sentiment": {
            "positive": {"count": sentiment_counts["positive"], "pct": pct(sentiment_counts["positive"])},
            "neutral": {"count": sentiment_counts["neutral"], "pct": pct(sentiment_counts["neutral"])},
            "negative": {"count": sentiment_counts["negative"], "pct": pct(sentiment_counts["negative"])},
        },
        "themes": themes,
    }
