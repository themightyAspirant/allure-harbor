import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import sessionmaker

from app import __version__
from app.api.errors import register_error_handlers
from app.api.health import router as health_router
from app.api.routes import router as reports_router
from app.api.static import router as static_router
from app.core.config import Settings
from app.models.database import init_db
from app.services.storage import Storage


def load_settings() -> Settings:
    return Settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = app.state.settings
    if not isinstance(settings, Settings):
        raise TypeError("application settings are not configured")
    engine = init_db(settings)
    app.state.engine = engine
    app.state.session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    app.state.storage = Storage(settings.data_dir)
    yield
    engine.dispose()


def create_app(settings: Settings | None = None) -> FastAPI:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    resolved = settings or load_settings()
    app = FastAPI(
        title="Allure Harbor",
        version=__version__,
        description="Upload Allure results and share generated HTML reports.",
        lifespan=lifespan,
    )
    app.state.settings = resolved
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    register_error_handlers(app)
    app.include_router(health_router)
    app.include_router(reports_router)
    app.include_router(static_router)
    return app
