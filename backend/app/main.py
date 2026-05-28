# python:3.10-slim-bullseye ships sqlite3 3.34.1; chromadb requires >= 3.35.0.
# Swap in the bundled newer version before any chromadb import occurs.
try:
    import pysqlite3 as _pysqlite3
    import sys as _sys
    _sys.modules["sqlite3"] = _pysqlite3
except ImportError:
    pass

import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime, timedelta

import bcrypt as _bcrypt
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import select

from app.config import settings
from app.db.models import Dataset, User
from app.db.session import AsyncSessionLocal, Base, engine
from app.routers import auth, chat, datasets, reviews, scrape
from app.security import blocklist

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


async def _startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    blocklist.reload()

    async with AsyncSessionLocal() as db:
        # Seed initial admin user if none exists and env vars are set
        admin_email = os.environ.get("INITIAL_ADMIN_EMAIL", "").strip().lower()
        admin_password = os.environ.get("INITIAL_ADMIN_PASSWORD", "").strip()
        if admin_email and admin_password:
            existing = await db.execute(select(User).where(User.email == admin_email))
            if existing.scalar_one_or_none() is None:
                hashed = _bcrypt.hashpw(admin_password.encode(), _bcrypt.gensalt()).decode()
                db.add(User(email=admin_email, hashed_password=hashed))
                await db.commit()
                logger.info("Seeded initial admin user: %s", admin_email)

        # Reset any stuck scraping datasets from a previous crash
        result = await db.execute(select(Dataset).where(Dataset.status == "scraping"))
        stuck = result.scalars().all()
        for ds in stuck:
            ds.status = "error"
            ds.error_message = "Scrape interrupted by server restart."
        if stuck:
            await db.commit()
            logger.info("Reset %d stuck scraping datasets", len(stuck))


@asynccontextmanager
async def lifespan(app: FastAPI):
    await _startup()
    yield


app = FastAPI(title="ReviewLens AI API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8080",
        "http://localhost:3000",
        "http://frontend:3000",
        "https://reviewlens.rochez.net",
        "https://reviewlens-frontend-963929737774.us-central1.run.app",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault("Cache-Control", "no-store")
    return response


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    detail = exc.detail
    if isinstance(detail, dict) and "error_code" in detail:
        content = detail
    else:
        content = {"error_code": "HTTP_ERROR", "message": str(detail)}
    return JSONResponse(status_code=exc.status_code, content=content)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception: %s", exc)
    return JSONResponse(
        status_code=500,
        content={"error_code": "INTERNAL_ERROR", "message": "An unexpected error occurred."},
    )


PREFIX = "/api/v1"
app.include_router(auth.router, prefix=PREFIX)
app.include_router(datasets.router, prefix=PREFIX)
app.include_router(reviews.router, prefix=PREFIX)
app.include_router(chat.router, prefix=PREFIX)
app.include_router(scrape.router, prefix=PREFIX)


@app.get("/health")
async def health():
    return {"status": "ok"}
