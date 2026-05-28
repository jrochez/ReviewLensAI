import asyncio
import csv
import io
import json as json_lib
import logging
import re
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Dataset, DatasetTheme, Review, ScrapeUsage, User
from app.db.session import AsyncSessionLocal, get_db
from app.dependencies import get_current_user
from app.services.ingest import check_budgets, run_scrape_job

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/datasets", tags=["datasets"])

MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB


def _create_logged_task(coro) -> asyncio.Task:
    task = asyncio.create_task(coro)
    def _on_done(t: asyncio.Task):
        if not t.cancelled() and (exc := t.exception()):
            logger.error("Background task %s raised: %s", t.get_name(), exc, exc_info=exc)
    task.add_done_callback(_on_done)
    return task

AMAZON_URL_PATTERN = re.compile(
    r"(?:https?://)?(?:www\.)?amazon\.[a-z.]+/(?:[^/]+/)?dp/([A-Z0-9]{10})", re.IGNORECASE
)
BARE_ASIN_PATTERN = re.compile(r"^[A-Z0-9]{10}$")
_SAFE_URL_PATTERN = re.compile(r'^https?://', re.IGNORECASE)


def extract_asin(input_str: str) -> str:
    """Extract a 10-char ASIN from a URL or bare ASIN string. SSRF-safe (regex only)."""
    stripped = input_str.strip()

    m = AMAZON_URL_PATTERN.search(stripped)
    if m:
        return m.group(1).upper()

    if BARE_ASIN_PATTERN.match(stripped):
        return stripped

    raise HTTPException(
        status_code=422,
        detail={"error_code": "INVALID_ASIN", "message": "Invalid Amazon URL or ASIN. Provide a 10-character ASIN or a valid Amazon product URL."},
    )


class CreateDatasetRequest(BaseModel):
    input: str


UPLOAD_REQUIRED_FIELDS = {"review_id", "review_text", "rating"}


def _upload_sentiment(star_rating: int) -> str:
    if star_rating >= 4:
        return "positive"
    if star_rating <= 2:
        return "negative"
    return "neutral"


def _parse_bool_field(val) -> bool:
    if isinstance(val, bool):
        return val
    return str(val).strip().upper() in ("TRUE", "1", "YES")


def _verify_file_content(filename: str, content: bytes) -> None:
    """Reject binary files and ensure the declared format matches actual content."""
    if b'\x00' in content[:512]:
        raise HTTPException(
            status_code=422,
            detail={"error_code": "INVALID_FILE_TYPE", "message": "File appears to be binary; only text CSV or JSON files are accepted."},
        )
    if filename.endswith(".json"):
        first_byte = content.lstrip()[:1]
        if first_byte != b'[':
            raise HTTPException(
                status_code=422,
                detail={"error_code": "INVALID_FILE_TYPE", "message": "JSON file must contain a top-level array of review objects."},
            )
    elif filename.endswith(".csv"):
        try:
            content[:512].decode("utf-8")
        except UnicodeDecodeError:
            raise HTTPException(
                status_code=422,
                detail={"error_code": "INVALID_FILE_TYPE", "message": "CSV file must be valid UTF-8 encoded text."},
            )


def _sanitize_product_url(url: str, asin: str) -> str:
    """Accept only http/https URLs; fall back to the canonical Amazon URL."""
    stripped = url.strip()
    if stripped and _SAFE_URL_PATTERN.match(stripped):
        return stripped
    return f"https://www.amazon.com/dp/{asin}"


def _parse_csv_rows(content: bytes) -> list[dict]:
    text = content.decode("utf-8-sig")
    return list(csv.DictReader(io.StringIO(text)))


def _parse_json_rows(content: bytes) -> list[dict]:
    data = json_lib.loads(content.decode("utf-8"))
    if not isinstance(data, list):
        raise ValueError("JSON must be an array of objects")
    rows = []
    for item in data:
        row = dict(item)
        if "input" in row and isinstance(row["input"], dict):
            row.setdefault("input_url", row["input"].get("url", ""))
        rows.append(row)
    return rows


async def _run_post_upload_tasks(dataset_id: str) -> None:
    async with AsyncSessionLocal() as db:
        try:
            from app.services.themes import extract_themes
            texts_result = await db.execute(
                select(Review.review_text).where(Review.dataset_id == dataset_id)
            )
            texts = [r[0] for r in texts_result.fetchall()]
            theme_pairs = await asyncio.to_thread(extract_themes, texts)
            for theme_text, freq in theme_pairs:
                db.add(DatasetTheme(
                    id=str(uuid4()),
                    dataset_id=dataset_id,
                    theme=theme_text,
                    frequency=freq,
                ))
            await db.commit()
        except Exception as exc:
            logger.warning("Upload themes failed for %s: %s", dataset_id, exc)
        try:
            from app.services.rag import index_dataset
            await index_dataset(dataset_id, db)
        except Exception as exc:
            logger.warning("Upload embeddings failed for %s: %s", dataset_id, exc)


def _dataset_to_dict(ds: Dataset, creator_email: str | None = None) -> dict:
    return {
        "id": ds.id,
        "asin": ds.asin,
        "product_name": ds.product_name,
        "product_url": ds.product_url,
        "status": ds.status,
        "review_count": ds.review_count,
        "avg_star_rating": ds.avg_star_rating,
        "review_date_min": ds.review_date_min,
        "review_date_max": ds.review_date_max,
        "error_message": ds.error_message,
        "created_at": ds.created_at.isoformat() + "Z" if ds.created_at else None,
        "last_scraped_at": ds.last_scraped_at.isoformat() + "Z" if ds.last_scraped_at else None,
        "created_by": creator_email,
    }


@router.get("")
async def list_datasets(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Dataset).order_by(Dataset.created_at.desc()))
    datasets = result.scalars().all()
    out = []
    for ds in datasets:
        creator = await db.get(User, ds.created_by)
        out.append(_dataset_to_dict(ds, creator.email if creator else None))
    return {"datasets": out}


@router.post("", status_code=201)
async def create_dataset(
    body: CreateDatasetRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    asin = extract_asin(body.input)

    scraping_check = await db.execute(select(Dataset).where(Dataset.status == "scraping"))
    if scraping_check.scalar_one_or_none():
        raise HTTPException(
            status_code=409,
            detail={"error_code": "SCRAPE_IN_PROGRESS", "message": "A scrape job is already running. Please wait for it to complete before starting another."},
        )

    budget_ok, next_at = await check_budgets(db, current_user.id)
    if not budget_ok:
        raise HTTPException(
            status_code=429,
            detail={
                "error_code": "DAILY_LIMIT_EXCEEDED",
                "message": "Daily review budget exhausted.",
                "next_scrape_available_at": next_at.isoformat() + "Z" if next_at else None,
            },
        )

    ds = Dataset(
        id=str(uuid4()),
        asin=asin,
        status="pending",
        created_by=current_user.id,
    )
    db.add(ds)
    await db.commit()
    await db.refresh(ds)

    _create_logged_task(run_scrape_job(ds.id, current_user.id))

    return {"id": ds.id, "asin": ds.asin, "status": ds.status}


@router.post("/upload", status_code=201)
async def upload_dataset(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    filename = (file.filename or "").lower()
    content = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail={"error_code": "FILE_TOO_LARGE", "message": "File exceeds the 10 MB upload limit."},
        )

    if not content:
        raise HTTPException(status_code=422, detail={"error_code": "EMPTY_FILE", "message": "Uploaded file is empty."})

    _verify_file_content(filename, content)

    try:
        if filename.endswith(".csv"):
            rows = _parse_csv_rows(content)
        elif filename.endswith(".json"):
            rows = _parse_json_rows(content)
        else:
            raise HTTPException(
                status_code=422,
                detail={"error_code": "INVALID_FILE_TYPE", "message": "File must be a .csv or .json file."},
            )
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("File parse failed for upload: %s", exc)
        raise HTTPException(
            status_code=422,
            detail={"error_code": "PARSE_ERROR", "message": "Failed to parse file. Ensure it is a valid CSV or JSON."},
        )

    if not rows:
        raise HTTPException(status_code=422, detail={"error_code": "EMPTY_FILE", "message": "File contains no reviews."})

    first = rows[0]
    missing = UPLOAD_REQUIRED_FIELDS - {k for k, v in first.items() if str(v).strip()}
    if missing:
        raise HTTPException(
            status_code=422,
            detail={"error_code": "MISSING_FIELDS", "message": f"Missing required fields: {', '.join(sorted(missing))}"},
        )

    asin = str(first.get("asin", "")).strip().upper()
    if not asin or not BARE_ASIN_PATTERN.match(asin):
        url = str(first.get("url", "") or first.get("input_url", ""))
        m = AMAZON_URL_PATTERN.search(url)
        if m:
            asin = m.group(1).upper()
        else:
            raise HTTPException(
                status_code=422,
                detail={"error_code": "MISSING_ASIN", "message": "Cannot determine ASIN. Ensure 'asin' column or a valid Amazon 'url' is present."},
            )

    product_name = str(first.get("product_name", "")).strip() or f"Product {asin}"
    product_url = _sanitize_product_url(str(first.get("url", "")), asin)

    ds = Dataset(
        id=str(uuid4()),
        asin=asin,
        product_name=product_name,
        product_url=product_url,
        status="pending",
        created_by=current_user.id,
    )
    db.add(ds)
    await db.commit()
    await db.refresh(ds)

    seen_ids: set[str] = set()
    inserted = 0
    for row in rows:
        review_id = str(row.get("review_id", "")).strip()
        review_text = str(row.get("review_text", "")).strip()
        try:
            star_rating = int(round(float(str(row.get("rating", 0) or 0))))
        except (ValueError, TypeError):
            continue
        if not review_id or review_id in seen_ids or not review_text or not (1 <= star_rating <= 5):
            continue
        seen_ids.add(review_id)
        try:
            helpful = int(float(str(row.get("helpful_count", 0) or 0)))
        except (ValueError, TypeError):
            helpful = 0
        db.add(Review(
            id=str(uuid4()),
            dataset_id=ds.id,
            external_review_id=review_id,
            review_text=review_text,
            star_rating=star_rating,
            reviewer_name=str(row.get("author_name", "")).strip() or None,
            review_date=str(row.get("review_posted_date", "")).strip() or None,
            verified_purchase=_parse_bool_field(row.get("is_verified", False)),
            helpful_votes=helpful,
            sentiment_label=_upload_sentiment(star_rating),
        ))
        inserted += 1

    if inserted == 0:
        await db.delete(ds)
        await db.commit()
        raise HTTPException(
            status_code=422,
            detail={"error_code": "NO_VALID_REVIEWS", "message": "No valid reviews found. Ensure review_id, review_text, and rating (1–5) are populated."},
        )

    await db.commit()

    stats_result = await db.execute(
        select(
            func.count(Review.id),
            func.avg(Review.star_rating),
            func.min(Review.review_date),
            func.max(Review.review_date),
        ).where(Review.dataset_id == ds.id)
    )
    count, avg_rating, date_min, date_max = stats_result.one()
    ds.review_count = count
    ds.avg_star_rating = round(float(avg_rating), 2) if avg_rating else None
    ds.review_date_min = date_min
    ds.review_date_max = date_max
    ds.last_scraped_at = datetime.now(timezone.utc).replace(tzinfo=None)
    ds.status = "ready"
    await db.commit()

    _create_logged_task(_run_post_upload_tasks(ds.id))

    return {"id": ds.id, "status": ds.status}


@router.get("/{dataset_id}")
async def get_dataset(
    dataset_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ds = await db.get(Dataset, dataset_id)
    if not ds:
        raise HTTPException(status_code=404, detail={"error_code": "DATASET_NOT_FOUND", "message": f"No dataset with id {dataset_id}"})
    creator = await db.get(User, ds.created_by)
    return _dataset_to_dict(ds, creator.email if creator else None)


@router.post("/{dataset_id}/rescrape", status_code=202)
async def rescrape_dataset(
    dataset_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ds = await db.get(Dataset, dataset_id)
    if not ds:
        raise HTTPException(status_code=404, detail={"error_code": "DATASET_NOT_FOUND", "message": f"No dataset with id {dataset_id}"})

    scraping_check = await db.execute(
        select(Dataset).where(Dataset.status == "scraping", Dataset.id != dataset_id)
    )
    if scraping_check.scalar_one_or_none():
        raise HTTPException(
            status_code=409,
            detail={"error_code": "SCRAPE_IN_PROGRESS", "message": "A scrape job is already running. Please wait for it to complete before starting another."},
        )

    budget_ok, next_at = await check_budgets(db, current_user.id)
    if not budget_ok:
        raise HTTPException(
            status_code=429,
            detail={
                "error_code": "DAILY_LIMIT_EXCEEDED",
                "message": "Daily review budget exhausted.",
                "next_scrape_available_at": next_at.isoformat() + "Z" if next_at else None,
            },
        )

    ds.status = "pending"
    ds.error_message = None
    await db.commit()

    _create_logged_task(run_scrape_job(ds.id, current_user.id))

    return {"status": "pending"}


@router.delete("/{dataset_id}", status_code=204)
async def delete_dataset(
    dataset_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ds = await db.get(Dataset, dataset_id)
    if not ds:
        raise HTTPException(status_code=404, detail={"error_code": "DATASET_NOT_FOUND", "message": f"No dataset with id {dataset_id}"})
    if ds.status == "scraping":
        raise HTTPException(
            status_code=409,
            detail={"error_code": "SCRAPE_IN_PROGRESS", "message": "Cannot delete a dataset while scraping is in progress."},
        )
    await db.delete(ds)
    await db.commit()
