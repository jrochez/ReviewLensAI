---
name: project-reviewlens-ai
description: ReviewLens AI project — what was built, tech stack, port config, and current status
metadata:
  type: project
---

ReviewLens AI is a complete internal ORM analyst tool built at `c:\Users\jon\Documents\Dev\ReviewLensAI`. It ingests Amazon product reviews via Bright Data scraping, presents a summary dashboard, and provides a guardrailed GPT-4o chat interface for Q&A over reviews.

**Why:** User requested a full working application from spec files (Requirements.md, DesignSpec.md, Architecture.md) with a QA test suite.

**Status (2026-05-27):** Application fully built and all tests pass — 30 unit, 18 integration (+1 skip), 17 E2E = 65 pass total.

**Stack:**
- Backend: FastAPI + SQLAlchemy 2 async + aiosqlite (SQLite), ChromaDB, OpenAI, Bright Data scraping
- Frontend: Next.js 14 App Router, TanStack Query, Tailwind CSS
- Tests: pytest + Playwright (Chromium)

**Port config (Windows Hyper-V exclusion of 8000–8138):**
- Backend: port 9000 (`uvicorn app.main:app --host 127.0.0.1 --port 9000`)
- Frontend: port 9001 (`npm run dev -- --port 9001`)
- App URL: http://localhost:9001

**Default credentials:** analyst@firm.com / password123 (seeded on startup)

**Mock mode:** Leave BRIGHTDATA_API_KEY and OPENAI_API_KEY empty for local testing with fake data.

**How to apply:** When continuing work on this project, services likely need to be restarted. Check PIDs in `backend_pid.txt` and `frontend_pid.txt`.
