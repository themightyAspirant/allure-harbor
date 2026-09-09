from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Query, Response, UploadFile

from app.api.deps import get_report_deps
from app.core.sanitize import sanitize_name, sanitize_project
from app.core.security import enforce_content_length
from app.schemas.report import ReportListResponse, ReportResponse
from app.services.reports import (
    ReportDeps,
    create_report,
    delete_report,
    get_report,
    list_reports,
    to_response,
)

router = APIRouter(prefix="/api/v1", tags=["reports"])

UploadParts = tuple[UploadFile, str, str | None]


async def parse_upload(
    file: UploadFile = File(...),
    project: str | None = Form(default=None),
    name: str | None = Form(default=None),
) -> UploadParts:
    return file, sanitize_project(project), sanitize_name(name)


@router.post(
    "/reports",
    status_code=201,
    dependencies=[Depends(enforce_content_length)],
)
async def upload_report(
    deps: Annotated[ReportDeps, Depends(get_report_deps)],
    upload: Annotated[UploadParts, Depends(parse_upload)],
) -> ReportResponse:
    file, project, name = upload
    report = await create_report(deps, file, project, name)
    return to_response(report, deps.settings.public_base_url)


@router.get("/reports")
def list_report_records(
    deps: Annotated[ReportDeps, Depends(get_report_deps)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    project: str | None = Query(default=None),
) -> ReportListResponse:
    project_filter = sanitize_project(project) if project else None
    return list_reports(deps, page, page_size, project_filter)


@router.get("/reports/{report_id}")
def get_report_record(
    report_id: UUID,
    deps: Annotated[ReportDeps, Depends(get_report_deps)],
) -> ReportResponse:
    report = get_report(deps, report_id)
    return to_response(report, deps.settings.public_base_url)


@router.delete("/reports/{report_id}", status_code=204)
def delete_report_record(
    report_id: UUID,
    deps: Annotated[ReportDeps, Depends(get_report_deps)],
) -> Response:
    delete_report(deps, report_id)
    return Response(status_code=204)
