import asyncio
import time
from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ChatLog, Dataset, User
from app.db.session import get_db
from app.dependencies import get_current_user
from app.services import rag

router = APIRouter(prefix="/datasets", tags=["chat"])

_CHAT_RATE_LIMIT = 20   # requests per window per user
_CHAT_RATE_WINDOW = 60  # sliding window in seconds
_chat_timestamps: dict[str, list[float]] = defaultdict(list)
_rate_limit_lock = asyncio.Lock()


async def _check_chat_rate_limit(user_id: str) -> bool:
    now = time.monotonic()
    async with _rate_limit_lock:
        ts = [t for t in _chat_timestamps[user_id] if now - t < _CHAT_RATE_WINDOW]
        if len(ts) >= _CHAT_RATE_LIMIT:
            _chat_timestamps[user_id] = ts
            return False
        ts.append(now)
        _chat_timestamps[user_id] = ts
        return True


class HistoryEntry(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    history: list[HistoryEntry] = []


@router.post("/{dataset_id}/chat")
async def chat(
    dataset_id: str,
    body: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not await _check_chat_rate_limit(current_user.id):
        raise HTTPException(
            status_code=429,
            detail={"error_code": "RATE_LIMIT_EXCEEDED", "message": f"Too many chat requests. Limit is {_CHAT_RATE_LIMIT} per {_CHAT_RATE_WINDOW} seconds."},
        )

    ds = await db.get(Dataset, dataset_id)
    if not ds:
        raise HTTPException(status_code=404, detail={"error_code": "DATASET_NOT_FOUND", "message": f"No dataset with id {dataset_id}"})

    if ds.status != "ready":
        raise HTTPException(
            status_code=400,
            detail={"error_code": "DATASET_NOT_READY", "message": "Dataset is not ready. Please wait for scraping to complete."},
        )

    history_dicts = [{"role": h.role, "content": h.content} for h in body.history]

    try:
        reply, scope_refused = await rag.run_qa(
            dataset_id=dataset_id,
            message=body.message,
            history=history_dicts,
            db=db,
            user_id=current_user.id,
        )
    except HTTPException:
        raise
    except Exception as exc:
        import logging
        logging.getLogger(__name__).error("QA pipeline error: %s", exc)
        raise HTTPException(
            status_code=503,
            detail={"error_code": "LLM_UNAVAILABLE", "message": "The AI service is temporarily unavailable. Please try again."},
        )

    log = ChatLog(
        dataset_id=dataset_id,
        user_id=current_user.id,
        user_message=body.message,
        assistant_reply=reply,
        scope_refused=scope_refused,
        history_length=len(body.history),
    )
    db.add(log)
    await db.commit()

    return {"reply": reply, "scope_refused": scope_refused}
