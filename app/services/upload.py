from pathlib import Path
from zipfile import ZipFile, ZipInfo

from fastapi import UploadFile

from app.core.config import Settings
from app.core.errors import (
    InvalidZipError,
    MissingResultsError,
    PayloadTooLargeError,
    ZipBombError,
    ZipSlipError,
)

ZIP_MAGIC = b"PK\x03\x04"
RESULT_SUFFIXES = ("-result.json", "-result.xml")
CHUNK_SIZE = 1024 * 1024
ALLOWED_TYPES = {
    "application/zip",
    "application/x-zip-compressed",
    "application/x-zip",
    "application/octet-stream",
}


def validate_filename(filename: str | None) -> None:
    if filename and not filename.lower().endswith(".zip"):
        raise InvalidZipError("Uploaded file must be a ZIP archive")


def validate_content_type(content_type: str | None) -> None:
    if not content_type:
        return
    mime = content_type.split(";")[0].strip().lower()
    if mime not in ALLOWED_TYPES:
        raise InvalidZipError("Uploaded file must be a ZIP archive")


def validate_zip_magic(zip_path: Path) -> None:
    with zip_path.open("rb") as handle:
        header = handle.read(4)
    if header != ZIP_MAGIC:
        raise InvalidZipError("Uploaded file is not a valid ZIP archive")


def is_safe_member(name: str, dest: Path) -> bool:
    if not name or name.startswith("/") or name.startswith("\\"):
        return False
    normalized = name.replace("\\", "/")
    if normalized.startswith("/") or normalized.startswith("../"):
        return False
    parts = Path(normalized).parts
    if any(part == ".." for part in parts):
        return False
    if len(name) >= 2 and name[1] == ":":
        return False
    target = (dest / normalized).resolve()
    dest_resolved = dest.resolve()
    return target == dest_resolved or dest_resolved in target.parents


async def save_upload(upload: UploadFile, dest: Path, max_bytes: int) -> int:
    validate_filename(upload.filename)
    validate_content_type(upload.content_type)
    size = 0
    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open("wb") as handle:
        while True:
            chunk = await upload.read(CHUNK_SIZE)
            if not chunk:
                break
            size += len(chunk)
            if size > max_bytes:
                raise PayloadTooLargeError(
                    "Upload exceeds the maximum allowed size",
                    details=[{"limit_bytes": str(max_bytes)}],
                )
            handle.write(chunk)
    if size == 0:
        raise InvalidZipError("Uploaded file is empty")
    return size


def extract_zip(zip_path: Path, dest: Path, settings: Settings) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    with ZipFile(zip_path) as archive:
        members = archive.infolist()
        _assert_zip_limits(members, settings)
        for info in members:
            _extract_member(archive, info, dest)


def find_results_root(extracted: Path) -> Path:
    result_files = [
        path
        for path in extracted.rglob("*")
        if path.is_file() and path.name.endswith(RESULT_SUFFIXES)
    ]
    if not result_files:
        raise MissingResultsError(
            "ZIP must contain at least one Allure result file",
            details=[{"hint": "expected *-result.json or *-result.xml"}],
        )
    parents = {path.parent for path in result_files}
    for parent in parents:
        if parent.name == "allure-results":
            return parent
    return next(iter(parents))


def unpack_results(zip_path: Path, dest: Path, settings: Settings) -> Path:
    validate_zip_magic(zip_path)
    extract_zip(zip_path, dest, settings)
    return find_results_root(dest)


def _assert_zip_limits(members: list[ZipInfo], settings: Settings) -> None:
    if len(members) > settings.max_zip_files:
        raise ZipBombError(
            "ZIP contains too many entries",
            details=[{"limit": str(settings.max_zip_files)}],
        )
    total = 0
    for info in members:
        total += info.file_size
        if total > settings.max_uncompressed_bytes:
            raise ZipBombError(
                "ZIP uncompressed size exceeds the limit",
                details=[{"limit_bytes": str(settings.max_uncompressed_bytes)}],
            )


def _extract_member(archive: ZipFile, info: ZipInfo, dest: Path) -> None:
    if not is_safe_member(info.filename, dest):
        raise ZipSlipError("ZIP contains an unsafe path")
    target = (dest / info.filename.replace("\\", "/")).resolve()
    if info.is_dir() or info.filename.endswith("/"):
        target.mkdir(parents=True, exist_ok=True)
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    with archive.open(info) as source, target.open("wb") as output:
        while True:
            chunk = source.read(CHUNK_SIZE)
            if not chunk:
                break
            output.write(chunk)
