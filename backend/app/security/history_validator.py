import logging

from fastapi import HTTPException

from app.config import settings
from app.security import blocklist

logger = logging.getLogger(__name__)

_MAX_ENTRY_CHARS = 10_000


def validate_history(history: list[dict]) -> tuple[list[dict], bool]:
    injection_detected = False

    for entry in history:
        role = entry.get("role", "")
        if role not in ("user", "assistant"):
            raise HTTPException(status_code=422, detail={"error_code": "INVALID_HISTORY", "message": f"Invalid role '{role}'. Only 'user' and 'assistant' are allowed."})

    if len(history) > settings.MAX_CHAT_HISTORY_TURNS:
        history = history[-settings.MAX_CHAT_HISTORY_TURNS :]

    clean_history = []
    for entry in history:
        role = entry.get("role")
        content = entry.get("content", "")[:_MAX_ENTRY_CHARS]
        cleaned, detected = blocklist.scan(content)
        if detected:
            injection_detected = True
        if role == "assistant":
            if detected:
                logger.warning("Injection pattern found in assistant history entry — dropping entry")
                continue
            clean_history.append({"role": "assistant", "content": cleaned})
        else:
            if detected:
                logger.warning("Injection pattern found in user history entry — sanitizing")
            clean_history.append({"role": "user", "content": cleaned})

    return clean_history, injection_detected
