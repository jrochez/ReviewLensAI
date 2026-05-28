from datetime import datetime, timezone
from uuid import uuid4


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


def _uuid() -> str:
    return str(uuid4())


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=_utcnow)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    sessions: Mapped[list["Session"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    datasets: Mapped[list["Dataset"]] = relationship(back_populates="creator")
    scrape_usages: Mapped[list["ScrapeUsage"]] = relationship(back_populates="user")


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=_utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    user: Mapped["User"] = relationship(back_populates="sessions")


class Dataset(Base):
    __tablename__ = "datasets"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    asin: Mapped[str] = mapped_column(String, nullable=False)
    product_name: Mapped[str | None] = mapped_column(String, nullable=True)
    product_url: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=False, default="pending")
    scrape_job_id: Mapped[str | None] = mapped_column(String, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    review_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    avg_star_rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    review_date_min: Mapped[str | None] = mapped_column(String, nullable=True)
    review_date_max: Mapped[str | None] = mapped_column(String, nullable=True)
    created_by: Mapped[str] = mapped_column(String, ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=_utcnow)
    last_scraped_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    creator: Mapped["User"] = relationship(back_populates="datasets")
    reviews: Mapped[list["Review"]] = relationship(back_populates="dataset", cascade="all, delete-orphan")
    themes: Mapped[list["DatasetTheme"]] = relationship(back_populates="dataset", cascade="all, delete-orphan")
    scrape_usages: Mapped[list["ScrapeUsage"]] = relationship(back_populates="dataset", cascade="all, delete-orphan")
    chat_logs: Mapped[list["ChatLog"]] = relationship(back_populates="dataset", cascade="all, delete-orphan")


class Review(Base):
    __tablename__ = "reviews"
    __table_args__ = (UniqueConstraint("dataset_id", "external_review_id", name="uq_review_per_dataset"),)

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    dataset_id: Mapped[str] = mapped_column(String, ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False)
    external_review_id: Mapped[str] = mapped_column(String, nullable=False)
    review_text: Mapped[str] = mapped_column(Text, nullable=False)
    star_rating: Mapped[int] = mapped_column(Integer, nullable=False)
    reviewer_name: Mapped[str | None] = mapped_column(String, nullable=True)
    review_date: Mapped[str | None] = mapped_column(String, nullable=True)
    verified_purchase: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    helpful_votes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    sentiment_label: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=_utcnow)

    dataset: Mapped["Dataset"] = relationship(back_populates="reviews")


class DatasetTheme(Base):
    __tablename__ = "dataset_themes"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    dataset_id: Mapped[str] = mapped_column(String, ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False)
    theme: Mapped[str] = mapped_column(String, nullable=False)
    frequency: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=_utcnow)

    dataset: Mapped["Dataset"] = relationship(back_populates="themes")


class ScrapeUsage(Base):
    __tablename__ = "scrape_usage"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    dataset_id: Mapped[str] = mapped_column(String, ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), nullable=False)
    reviews_fetched: Mapped[int] = mapped_column(Integer, nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=_utcnow)

    dataset: Mapped["Dataset"] = relationship(back_populates="scrape_usages")
    user: Mapped["User"] = relationship(back_populates="scrape_usages")


class ChatLog(Base):
    """Audit log for every Ask Questions (Chat) interaction per dataset."""

    __tablename__ = "chat_logs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    dataset_id: Mapped[str] = mapped_column(String, ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), nullable=False)
    user_message: Mapped[str] = mapped_column(Text, nullable=False)
    assistant_reply: Mapped[str] = mapped_column(Text, nullable=False)
    scope_refused: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    history_length: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=_utcnow)

    dataset: Mapped["Dataset"] = relationship(back_populates="chat_logs")
    user: Mapped["User"] = relationship()
