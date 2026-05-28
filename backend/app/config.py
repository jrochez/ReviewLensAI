from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    BRIGHTDATA_API_KEY: str = ""
    BRIGHTDATA_DATASET_ID: str = ""
    BRIGHTDATA_MAX_REVIEWS_PER_ASIN: int = 10000
    BRIGHTDATA_DAILY_REVIEW_LIMIT: int = 10000
    BRIGHTDATA_PER_USER_DAILY_LIMIT: int = 5000

    OPENAI_API_KEY: str = ""

    SECRET_KEY: str = ""
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/reviewlens.db"

    RAG_TOP_K: int = 20
    CHROMA_PERSIST_DIR: str = "./data/chromadb"

    INJECTION_BLOCKLIST_PATH: str = "./config/injection_blocklist.txt"
    MAX_CHAT_MESSAGE_LENGTH: int = 1000
    MAX_CHAT_HISTORY_TURNS: int = 10
    SYSTEM_REMINDER_INTERVAL_TURNS: int = 5

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()

_INSECURE_SECRET_KEYS = {
    "",
    "dev-secret-change-in-production",
    "change-me-to-a-random-secret-in-production",
}
if settings.SECRET_KEY in _INSECURE_SECRET_KEYS:
    raise RuntimeError(
        "SECRET_KEY is not set or is still an insecure placeholder. "
        "Generate a unique secret and set SECRET_KEY in your .env file."
    )
