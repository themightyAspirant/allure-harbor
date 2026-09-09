from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.core.errors import GenerationError
from app.services.generator import (
    generate_report,
    read_allure_version,
    resolve_allure_bin,
)


def test_missing_allure_binary(tmp_path: Path) -> None:
    settings = Settings(
        data_dir=tmp_path,
        allure_bin="allure-binary-does-not-exist",
    )
    with pytest.raises(GenerationError, match="not installed"):
        generate_report(settings, tmp_path / "results", tmp_path / "report")


def test_allure_nonzero_exit(tmp_path: Path, failing_allure: Path) -> None:
    settings = Settings(
        data_dir=tmp_path,
        allure_bin=str(failing_allure),
    )
    with pytest.raises(GenerationError, match="generation failed"):
        generate_report(settings, tmp_path / "results", tmp_path / "report")


def test_version_when_cli_missing(tmp_path: Path) -> None:
    settings = Settings(
        data_dir=tmp_path,
        allure_bin="allure-binary-does-not-exist",
    )
    assert read_allure_version(settings) is None


def test_unknown_route_uses_error_envelope(client: TestClient) -> None:
    response = client.get("/nope")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


def test_invalid_uuid_is_validation_error(client: TestClient) -> None:
    response = client.get("/api/v1/reports/not-a-uuid")
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_resolves_allure_name_from_path(
    tmp_path: Path,
    fake_allure: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PATH", str(fake_allure.parent))
    assert Path(resolve_allure_bin("allure")).name.lower().startswith("allure")
    settings = Settings(data_dir=tmp_path / "data", allure_bin="allure")
    results = tmp_path / "results"
    results.mkdir()
    (results / "aaaaaaaa-result.json").write_text("{}", encoding="utf-8")
    report_dir = tmp_path / "report"
    generate_report(settings, results, report_dir)
    assert (report_dir / "index.html").is_file()
