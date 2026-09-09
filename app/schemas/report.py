from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.report import ReportStatus


class ReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project: str
    name: str | None
    status: ReportStatus
    created_at: datetime
    error_message: str | None
    size_bytes: int
    view_url: str | None
    expires_at: datetime | None = None


class Pagination(BaseModel):
    page: int
    page_size: int
    total: int
    total_pages: int


class ReportListResponse(BaseModel):
    data: list[ReportResponse]
    pagination: Pagination


class ErrorBody(BaseModel):
    code: str
    message: str
    details: list[dict[str, str]] = Field(default_factory=list)


class ErrorResponse(BaseModel):
    error: ErrorBody
