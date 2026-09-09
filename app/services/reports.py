import logging
import math
from dataclasses import dataclass
from typing import NoReturn
from uuid import UUID, uuid4

from fastapi import UploadFile
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.errors import GenerationError, HarborError, ReportNotFoundError
from app.models.report import Report, ReportStatus
from app.schemas.report import Pagination, ReportListResponse, ReportResponse
from app.services.generator import generate_report
from app.services.storage import Storage
from app.services.upload import save_upload, unpack_results

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ReportDeps:
    session: Session
    settings: Settings
    storage: Storage


def to_response(report: Report, base_url: str) -> ReportResponse:
    view_url = None
    if report.status == ReportStatus.READY:
        view_url = f"{base_url.rstrip('/')}/reports/{report.id}/"
    return ReportResponse(
        id=report.id,
        project=report.project,
        name=report.name,
        status=ReportStatus(report.status),
        created_at=report.created_at,
        error_message=report.error_message,
        size_bytes=report.size_bytes,
        view_url=view_url,
        expires_at=None,
    )


async def create_report(
    deps: ReportDeps,
    upload: UploadFile,
    project: str,
    name: str | None,
) -> Report:
    report_id = uuid4()
    deps.storage.ensure_dirs(report_id)
    zip_path = deps.storage.zip_path(report_id)
    try:
        size = await save_upload(upload, zip_path, deps.settings.max_upload_bytes)
        results_root = unpack_results(
            zip_path,
            deps.storage.results_dir(report_id),
            deps.settings,
        )
        report = _new_report(report_id, project, name, size)
        deps.session.add(report)
        deps.session.flush()
        generate_report(
            deps.settings,
            results_root,
            deps.storage.report_dir(report_id),
        )
        report.status = ReportStatus.READY
        deps.storage.write_meta(report)
        deps.session.commit()
        logger.info(
            "report_ready report_id=%s project=%s size_bytes=%s",
            report.id,
            report.project,
            size,
        )
        return report
    except GenerationError as exc:
        _persist_failed(deps, report_id, project, name, exc)
    except HarborError:
        deps.session.rollback()
        deps.storage.delete_report(report_id)
        raise
    except Exception:
        deps.session.rollback()
        deps.storage.delete_report(report_id)
        raise


def get_report(deps: ReportDeps, report_id: UUID) -> Report:
    report = deps.session.get(Report, report_id)
    if report is None:
        raise ReportNotFoundError("Report not found")
    return report


def list_reports(
    deps: ReportDeps,
    page: int,
    page_size: int,
    project: str | None,
) -> ReportListResponse:
    total_stmt = select(func.count()).select_from(Report)
    rows_stmt = select(Report)
    if project:
        total_stmt = total_stmt.where(Report.project == project)
        rows_stmt = rows_stmt.where(Report.project == project)
    total = deps.session.scalar(total_stmt) or 0
    offset = (page - 1) * page_size
    rows = deps.session.scalars(
        rows_stmt.order_by(Report.created_at.desc()).offset(offset).limit(page_size)
    ).all()
    total_pages = math.ceil(total / page_size) if total else 0
    return ReportListResponse(
        data=[to_response(row, deps.settings.public_base_url) for row in rows],
        pagination=Pagination(
            page=page,
            page_size=page_size,
            total=total,
            total_pages=total_pages,
        ),
    )


def delete_report(deps: ReportDeps, report_id: UUID) -> None:
    report = get_report(deps, report_id)
    deps.session.delete(report)
    deps.session.commit()
    deps.storage.delete_report(report_id)
    logger.info("report_deleted report_id=%s", report_id)


def _new_report(
    report_id: UUID,
    project: str,
    name: str | None,
    size: int,
) -> Report:
    return Report(
        id=report_id,
        project=project,
        name=name,
        status=ReportStatus.GENERATING,
        size_bytes=size,
    )


def _persist_failed(
    deps: ReportDeps,
    report_id: UUID,
    project: str,
    name: str | None,
    exc: GenerationError,
) -> NoReturn:
    report = deps.session.get(Report, report_id)
    if report is None:
        zip_path = deps.storage.zip_path(report_id)
        size = zip_path.stat().st_size if zip_path.exists() else 0
        report = _new_report(report_id, project, name, size)
        deps.session.add(report)
    report.status = ReportStatus.FAILED
    report.error_message = exc.message
    deps.storage.write_meta(report)
    deps.session.commit()
    logger.error("report_failed report_id=%s", report_id)
    raise GenerationError(
        exc.message,
        details=exc.details + [{"report_id": str(report_id)}],
    ) from exc
