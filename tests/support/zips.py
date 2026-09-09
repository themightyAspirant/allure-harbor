from io import BytesIO
from pathlib import Path
from zipfile import ZipFile, ZipInfo

SAMPLE_RESULT = (
    b'{"uuid":"aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",'
    b'"name":"sample test","status":"passed","stage":"finished"}'
)


def build_results_zip(
    nested: bool = True,
    extra: dict[str, bytes] | None = None,
) -> bytes:
    buffer = BytesIO()
    with ZipFile(buffer, "w") as archive:
        name = (
            "allure-results/aaaaaaaa-result.json"
            if nested
            else "aaaaaaaa-result.json"
        )
        archive.writestr(name, SAMPLE_RESULT)
        if extra:
            for path, payload in extra.items():
                archive.writestr(path, payload)
    return buffer.getvalue()


def write_results_zip(path: Path, nested: bool = True) -> Path:
    path.write_bytes(build_results_zip(nested=nested))
    return path


def build_zip_with_member(name: str, payload: bytes = b"x") -> bytes:
    buffer = BytesIO()
    with ZipFile(buffer, "w") as archive:
        archive.writestr(ZipInfo(name), payload)
    return buffer.getvalue()
