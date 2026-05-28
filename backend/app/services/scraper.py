from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

import httpx

from app.config import settings


class JobStatus(str, Enum):
    pending = "pending"
    running = "running"
    complete = "complete"
    error = "error"


@dataclass
class RawReview:
    external_review_id: str
    review_text: str
    star_rating: int
    reviewer_name: str | None = None
    review_date: str | None = None
    verified_purchase: bool = False
    helpful_votes: int = 0


class ScraperProvider(ABC):
    @abstractmethod
    def submit_job(self, asin: str) -> str: ...

    @abstractmethod
    def poll_job(self, job_id: str) -> JobStatus: ...

    @abstractmethod
    def fetch_results(self, job_id: str) -> list[RawReview]: ...


class BrightDataAdapter(ScraperProvider):
    BASE_URL = "https://api.brightdata.com/datasets/v3"

    def __init__(self):
        self.api_key = settings.BRIGHTDATA_API_KEY
        self.dataset_id = settings.BRIGHTDATA_DATASET_ID
        self.headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

    def submit_job(self, asin: str) -> str:
        url = f"{self.BASE_URL}/trigger?dataset_id={self.dataset_id}&include_errors=true"
        payload = [{"url": f"https://www.amazon.com/dp/{asin}"}]
        with httpx.Client(timeout=30) as client:
            resp = client.post(url, json=payload, headers=self.headers)
            resp.raise_for_status()
            data = resp.json()
            return data.get("snapshot_id") or data.get("id") or str(data)

    def poll_job(self, job_id: str) -> JobStatus:
        url = f"{self.BASE_URL}/progress/{job_id}"
        with httpx.Client(timeout=30) as client:
            resp = client.get(url, headers=self.headers)
            resp.raise_for_status()
            data = resp.json()
            status = data.get("status", "").lower()
            if status in ("ready", "complete", "success"):
                return JobStatus.complete
            if status in ("failed", "error"):
                return JobStatus.error
            if status in ("running", "collecting"):
                return JobStatus.running
            return JobStatus.pending

    def fetch_results(self, job_id: str) -> list[RawReview]:
        url = f"{self.BASE_URL}/snapshot/{job_id}?format=json"
        with httpx.Client(timeout=120) as client:
            resp = client.get(url, headers=self.headers)
            resp.raise_for_status()
            raw = resp.json()

        reviews = []
        max_reviews = settings.BRIGHTDATA_MAX_REVIEWS_PER_ASIN
        for item in raw[:max_reviews]:
            review_id = str(item.get("id") or item.get("review_id") or item.get("_id") or "")
            text = item.get("review_text") or item.get("body") or item.get("review_body") or item.get("text") or ""
            title = item.get("title") or item.get("review_title") or ""
            if title:
                text = f"{title}\n{text}"
            rating_raw = item.get("rating") or item.get("star_rating") or 0
            try:
                rating = int(float(str(rating_raw)))
            except (ValueError, TypeError):
                rating = 3
            rating = max(1, min(5, rating))

            date_raw = item.get("review_posted_date") or item.get("date") or item.get("review_date") or item.get("published_date")
            if date_raw and isinstance(date_raw, str):
                try:
                    date_str = datetime.strptime(date_raw, "%B %d, %Y").date().isoformat()
                except ValueError:
                    date_str = None
            else:
                date_str = None

            verified = bool(item.get("is_verified") or item.get("verified_purchase") or item.get("verified"))
            helpful = int(item.get("helpful_votes") or item.get("helpful") or 0)
            reviewer = item.get("author_name") or item.get("name") or item.get("author") or item.get("reviewer_name")

            reviews.append(RawReview(
                external_review_id=review_id or str(hash(text[:50])),
                review_text=text,
                star_rating=rating,
                reviewer_name=reviewer,
                review_date=date_str,
                verified_purchase=verified,
                helpful_votes=helpful,
            ))

        return reviews


class MockScraperAdapter(ScraperProvider):
    """Used when BRIGHTDATA_API_KEY is not set. Returns fake reviews for local dev/testing."""

    def submit_job(self, asin: str) -> str:
        return f"mock-job-{asin}"

    def poll_job(self, job_id: str) -> JobStatus:
        return JobStatus.complete

    def fetch_results(self, job_id: str) -> list[RawReview]:
        asin = job_id.replace("mock-job-", "")
        return [
            RawReview("mock-1", f"Great product! I love the {asin}. The quality is excellent and it works perfectly. Battery life is amazing and setup was a breeze.", 5, "Happy Customer", "2025-01-15", True, 12),
            RawReview("mock-2", "Decent product but the battery life could be better. After 3 months of use it doesn't last as long. Customer service was responsive though.", 3, "Average Joe", "2025-02-20", True, 5),
            RawReview("mock-3", "Terrible experience. The product stopped working after 2 weeks. Very disappointed. Build quality is poor and connectivity issues are constant.", 1, "Disappointed Dan", "2025-03-10", False, 23),
            RawReview("mock-4", "Really happy with this purchase. Sound quality is superb. Easy to set up and connects seamlessly. Would highly recommend to anyone looking for a reliable product.", 5, "Tech Reviewer", "2025-04-01", True, 8),
            RawReview("mock-5", "Good value for money. Does what it says on the tin. Nothing special but gets the job done reliably. Build quality seems solid enough for everyday use.", 4, "Practical Pete", "2025-05-12", True, 3),
        ]


def get_scraper() -> ScraperProvider:
    if settings.BRIGHTDATA_API_KEY:
        return BrightDataAdapter()
    return MockScraperAdapter()
