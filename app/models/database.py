from collections.abc import Generator

from fastapi import Request
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.core.config import Settings
from app.models.report import Base


def create_engine_from_settings(settings: Settings) -> Engine:
    return create_engine(
        settings.database_url,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )


def init_db(settings: Settings) -> Engine:
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    (settings.data_dir / "reports").mkdir(parents=True, exist_ok=True)
    engine = create_engine_from_settings(settings)
    Base.metadata.create_all(engine)
    return engine


def get_session(request: Request) -> Generator[Session, None, None]:
    session: Session = request.app.state.session_factory()
    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_settings(request: Request) -> Settings:
    settings = request.app.state.settings
    if not isinstance(settings, Settings):
        raise TypeError("application settings are not configured")
    return settings
