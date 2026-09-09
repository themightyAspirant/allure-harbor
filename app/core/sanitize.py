import re

_PROJECT_RE = re.compile(r"[^a-z0-9-]+")
_HYPHEN_RE = re.compile(r"-{2,}")
_MAX_PROJECT_LEN = 64
_MAX_NAME_LEN = 255


def sanitize_project(value: str | None) -> str:
    raw = (value or "default").strip().lower()
    cleaned = _PROJECT_RE.sub("-", raw)
    cleaned = _HYPHEN_RE.sub("-", cleaned).strip("-")
    cleaned = cleaned[:_MAX_PROJECT_LEN]
    return cleaned or "default"


def sanitize_name(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    if not cleaned:
        return None
    return cleaned[:_MAX_NAME_LEN]
