import re
import unicodedata
from pathlib import Path

from app.config import settings

_DEFAULT_PATTERNS = [
    "IGNORE PREVIOUS", "IGNORE ALL PREVIOUS", "SYSTEM:", "SYSTEM INSTRUCTION",
    "ADMIN:", "ADMIN OVERRIDE", "OVERRIDE:", "NEW INSTRUCTIONS:", "FORGET EVERYTHING",
    "[SYSTEM", "---SYSTEM", "<system>", "</system>", "<instruction>", "</instruction>",
    "SYSTEM ADMIN MESSAGE", "DISREGARD PRIOR", "DISREGARD PREVIOUS",
    "JAILBREAK", "UNRESTRICTED MODE", "DEVELOPER MODE", "DAN MODE", "SUDO MODE",
    "ACT AS", "PRETEND YOU ARE", "YOU ARE NOW", "FROM NOW ON", "IGNORE YOUR",
    "DO ANYTHING NOW", "BYPASS", "PROMPT INJECTION", "ESCAPE YOUR",
    "BREAK CHARACTER", "END SYSTEM PROMPT", "END OF PROMPT",
]

_patterns: list[str] = []


def _load() -> list[str]:
    path = Path(settings.INJECTION_BLOCKLIST_PATH)
    if path.exists():
        lines = [ln.strip() for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]
        return lines if lines else _DEFAULT_PATTERNS
    return _DEFAULT_PATTERNS


def reload():
    global _patterns
    _patterns = _load()


reload()


def _normalize(text: str) -> str:
    """NFC-normalize and collapse whitespace to resist Unicode homoglyph bypasses."""
    return " ".join(unicodedata.normalize("NFC", text).split())


def scan(text: str) -> tuple[str, bool]:
    matched = False
    result = _normalize(text)
    for pattern in _patterns:
        escaped = re.escape(pattern)
        new, n = re.subn(escaped, "[REMOVED]", result, flags=re.IGNORECASE)
        if n > 0:
            matched = True
            result = new
    return result, matched
