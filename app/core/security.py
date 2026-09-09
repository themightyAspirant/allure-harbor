from fastapi import Request

from app.core.config import Settings
from app.core.errors import PayloadTooLargeError


def enforce_content_length(request: Request) -> None:
    settings = request.app.state.settings
    if not isinstance(settings, Settings):
        raise TypeError("application settings are not configured")
    raw = request.headers.get("content-length")
    if raw is None:
        return
    try:
        length = int(raw)
    except ValueError:
        return
    if length > settings.max_upload_bytes:
        raise PayloadTooLargeError(
            "Upload exceeds the maximum allowed size",
            details=[{"limit_bytes": str(settings.max_upload_bytes)}],
        )
