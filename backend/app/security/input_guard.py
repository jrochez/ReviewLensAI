from app.config import settings
from app.security import blocklist


def validate_message(text: str) -> tuple[str, bool]:
    truncated = text[: settings.MAX_CHAT_MESSAGE_LENGTH]
    cleaned, detected = blocklist.scan(truncated)
    return cleaned, detected
