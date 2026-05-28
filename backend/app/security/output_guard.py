import logging
import re

logger = logging.getLogger(__name__)

_DISCLOSURE_PATTERNS = [
    r"my instructions are",
    r"my system prompt",
    r"STRICT RULES",
    r"RULE \d",
    r"Identity Lock",
    r"Framing Immunity",
    r"Authority Immunity",
    r"Session Persistence",
    r"Encoding Immunity",
]

_INJECTION_ARTIFACTS = [
    r"\[SYSTEM",
    r"ADMIN OVERRIDE",
    r"SYSTEM ADMIN MESSAGE",
]


def filter_output(text: str) -> str:
    for pat in _DISCLOSURE_PATTERNS:
        if re.search(pat, text, re.IGNORECASE):
            logger.warning("Output disclosure pattern detected: %s", pat)
            return "I cannot share my configuration."

    for pat in _INJECTION_ARTIFACTS:
        if re.search(pat, text, re.IGNORECASE):
            logger.error("Injection artifact detected in LLM output: %s", pat)
            raise ValueError("Injection artifact detected in LLM response")

    return text
