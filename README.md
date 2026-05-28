# ReviewLens AI

An AI-powered Amazon product review analysis platform. Paste a product ASIN, scrape its reviews, then explore them through a RAG-based chat interface — ask natural-language questions and get answers grounded in real customer feedback.

Works fully in **mock mode** with no API keys required (synthetic data is used instead of live scraping and real AI responses).

---

## Features

- **Review ingestion** — Scrape Amazon reviews by ASIN via Bright Data (or mock data for local dev)
- **Review explorer** — Paginated, filterable review table with star ratings and sentiment labels
- **Dataset summary** — Stats, average rating, sentiment breakdown, and TF-IDF theme extraction
- **RAG chat** — Ask questions about a product's reviews; GPT-4o answers using the top-K retrieved reviews as context
- **Auth** — JWT bearer token auth with session persistence
- **Rate limiting** — Per-user daily scrape budget enforced server-side
- **Prompt injection defense** — Input guard + blocklist + scope classifier on every chat message

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI (Python 3.12) + SQLAlchemy 2 async |
| Database | SQLite via aiosqlite (swap to PostgreSQL for production) |
| Vector store | ChromaDB embedded |
| AI / RAG | OpenAI GPT-4o + text-embedding-3-small |
| Scraping | Bright Data v3 API + MockScraperAdapter |
| Frontend | Next.js 15 (App Router) + TanStack Query + Tailwind CSS |
| Migrations | Alembic (async) |
| Tests | pytest + Playwright |

---

## Deploy from GitHub (Docker Compose)

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running
- Git

### Steps

```bash
# 1. Clone the repository
git clone https://github.com/jrochez/ReviewLensAI.git
cd ReviewLensAI

# 2. Create your environment file
cp .env.example .env
```

Open `.env` and fill in your API keys. Both are optional — leave them empty to run in mock mode:

```env
BRIGHTDATA_API_KEY=        # leave empty → mock scraper (synthetic reviews)
OPENAI_API_KEY=            # leave empty → mock AI responses
```

```bash
# 3. Build and start
docker-compose up --build
```

| Service | URL |
|---------|-----|
| Frontend | http://localhost:9001 |
| Backend API | http://localhost:9000 |
| API docs | http://localhost:9000/docs |

**Default login:** `analyst@firm.com` / `password123`

To stop: `docker-compose down`  
To stop and remove data volumes: `docker-compose down -v`

---

## Local Development (No Docker)

**Prerequisites:** Python 3.12+, Node.js 18+

```bash
# 1. Clone and enter project
git clone https://github.com/jrochez/ReviewLensAI.git
cd ReviewLensAI

# 2. Create env file
cp .env.example .env

# 3. Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 9000 --reload

# 4. Frontend (new terminal)
cd frontend
npm install
npm run dev -- --port 9001
```

Open **http://localhost:9001**.

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite+aiosqlite:///data/reviewlens.db` | DB connection string |
| `BRIGHTDATA_API_KEY` | _(empty)_ | Enables real scraping; mock mode when empty |
| `OPENAI_API_KEY` | _(empty)_ | Enables real RAG/chat; mock mode when empty |
| `CHROMA_PERSIST_DIR` | `data/chroma` | ChromaDB storage path |
| `RAG_TOP_K` | `20` | Reviews retrieved per chat query |
| `INJECTION_BLOCKLIST_PATH` | `config/injection_blocklist.txt` | Prompt injection patterns file |
| `MAX_CHAT_MESSAGE_LENGTH` | `2000` | Input character limit |
| `MAX_CHAT_HISTORY_TURNS` | `20` | Chat history window |
| `BRIGHTDATA_PER_USER_DAILY_LIMIT` | `500` | Max reviews scraped per user/day |

---

## API Reference

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/auth/login` | Login → bearer token |
| `POST` | `/api/v1/auth/logout` | Invalidate token |
| `GET` | `/api/v1/datasets` | List datasets |
| `POST` | `/api/v1/datasets` | Create dataset (triggers scrape) |
| `GET` | `/api/v1/datasets/{id}` | Get dataset |
| `POST` | `/api/v1/datasets/{id}/rescrape` | Trigger re-scrape |
| `DELETE` | `/api/v1/datasets/{id}` | Delete dataset |
| `GET` | `/api/v1/datasets/{id}/reviews` | Paginated, filterable reviews |
| `GET` | `/api/v1/datasets/{id}/summary` | Stats, sentiment, themes |
| `POST` | `/api/v1/datasets/{id}/chat` | RAG Q&A |
| `GET` | `/api/v1/scrape/rate-limit` | Daily scrape budget status |
| `GET` | `/health` | Health check |

Interactive docs available at **http://localhost:9000/docs** when running.
