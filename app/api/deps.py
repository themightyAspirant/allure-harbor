from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.database import get_session
from app.services.reports import ReportDeps
from app.services.storage import Storage


def get_report_deps(
    request: Request,
    session: Session = Depends(get_session),
) -> ReportDeps:
    settings: Settings = request.app.state.settings
    storage: Storage = request.app.state.storage
    return ReportDeps(session=session, settings=settings, storage=storage)
