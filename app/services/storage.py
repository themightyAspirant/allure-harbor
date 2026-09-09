import json
from pathlib import Path
from uuid import UUID

from app.models.report import Report

_REPORTS_DIR = "reports"
_UPLOAD_ZIP = "upload.zip"
_RESULTS_DIR = "results"
_REPORT_DIR = "report"
_META_FILE = "meta.json"


class Storage:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.reports_root = root / _REPORTS_DIR

    def report_root(self, report_id: UUID) -> Path:
        return self.reports_root / str(report_id)

    def zip_path(self, report_id: UUID) -> Path:
        return self.report_root(report_id) / _UPLOAD_ZIP

    def results_dir(self, report_id: UUID) -> Path:
        return self.report_root(report_id) / _RESULTS_DIR

    def report_dir(self, report_id: UUID) -> Path:
        return self.report_root(report_id) / _REPORT_DIR

    def meta_path(self, report_id: UUID) -> Path:
        return self.report_root(report_id) / _META_FILE

    def ensure_dirs(self, report_id: UUID) -> None:
        root = self.report_root(report_id)
        root.mkdir(parents=True, exist_ok=True)
        self.results_dir(report_id).mkdir(parents=True, exist_ok=True)
        self.report_dir(report_id).mkdir(parents=True, exist_ok=True)

    def delete_report(self, report_id: UUID) -> None:
        root = self.report_root(report_id)
        if root.exists():
            _rmtree(root)

    def write_meta(self, report: Report) -> None:
        payload = {
            "id": str(report.id),
            "project": report.project,
            "name": report.name,
            "status": report.status,
            "created_at": report.created_at.isoformat(),
            "error_message": report.error_message,
            "size_bytes": report.size_bytes,
        }
        self.meta_path(report.id).write_text(
            json.dumps(payload, indent=2),
            encoding="utf-8",
        )


def _rmtree(path: Path) -> None:
    import shutil

    shutil.rmtree(path)
