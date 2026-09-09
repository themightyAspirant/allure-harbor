from uuid import UUID

from fastapi import APIRouter, Request
from fastapi.responses import FileResponse, RedirectResponse

from app.core.errors import ReportNotFoundError
from app.models.report import Report, ReportStatus
from app.services.storage import Storage

router = APIRouter(tags=["report-viewer"])


@router.get("/reports/{report_id}")
def redirect_report(report_id: UUID) -> RedirectResponse:
    return RedirectResponse(url=f"/reports/{report_id}/", status_code=307)


@router.get("/reports/{report_id}/")
def serve_report_index(report_id: UUID, request: Request) -> FileResponse:
    return _file_response(request, report_id, "index.html")


@router.get("/reports/{report_id}/{file_path:path}")
def serve_report_file(
    report_id: UUID,
    file_path: str,
    request: Request,
) -> FileResponse:
    relative = file_path.strip() or "index.html"
    return _file_response(request, report_id, relative)


def _file_response(request: Request, report_id: UUID, relative: str) -> FileResponse:
    storage: Storage = request.app.state.storage
    session = request.app.state.session_factory()
    try:
        report = session.get(Report, report_id)
    finally:
        session.close()
    if report is None or report.status != ReportStatus.READY:
        raise ReportNotFoundError("Report not found")
    report_dir = storage.report_dir(report_id).resolve()
    target = (report_dir / relative).resolve()
    if report_dir not in target.parents and target != report_dir:
        raise ReportNotFoundError("Report not found")
    if target.is_dir():
        target = target / "index.html"
    if not target.is_file():
        raise ReportNotFoundError("Report not found")
    return FileResponse(target)
