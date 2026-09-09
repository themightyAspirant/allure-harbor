from fastapi import APIRouter, Request

from app.core.config import Settings
from app.services.generator import read_allure_version

router = APIRouter(tags=["health"])


@router.get("/health")
def health(request: Request) -> dict[str, str | None]:
    settings: Settings = request.app.state.settings
    return {
        "status": "ok",
        "allure_version": read_allure_version(settings),
    }
