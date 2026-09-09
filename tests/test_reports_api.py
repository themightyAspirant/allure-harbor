from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app
from app.services.generator import generate_report
from tests.support.zips import build_results_zip


def test_generate_writes_index(tmp_path: Path, fake_allure: Path) -> None:
    results = tmp_path / "results"
    results.mkdir()
    (results / "aaaaaaaa-result.json").write_text("{}", encoding="utf-8")
    report_dir = tmp_path / "report"
    settings = Settings(
        data_dir=tmp_path / "data",
        allure_bin=str(fake_allure),
    )
    generate_report(settings, results, report_dir)
    assert (report_dir / "index.html").is_file()


def test_upload_generates_and_serves(client: TestClient) -> None:
    files = {"file": ("results.zip", build_results_zip(), "application/zip")}
    data = {"project": "Checkout Suite", "name": "nightly"}
    response = client.post("/api/v1/reports", files=files, data=data)
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "ready"
    assert body["project"] == "checkout-suite"
    assert body["name"] == "nightly"
    assert body["view_url"].endswith(f"/reports/{body['id']}/")
    assert body["expires_at"] is None
    page = client.get(body["view_url"].replace("http://testserver", ""))
    assert page.status_code == 200
    asset = client.get(f"/reports/{body['id']}/app.js")
    assert asset.status_code == 200


def test_list_get_and_delete(client: TestClient) -> None:
    files = {"file": ("results.zip", build_results_zip(), "application/zip")}
    created = client.post("/api/v1/reports", files=files)
    report_id = created.json()["id"]
    listed = client.get("/api/v1/reports")
    assert listed.status_code == 200
    assert listed.json()["pagination"]["total"] == 1
    fetched = client.get(f"/api/v1/reports/{report_id}")
    assert fetched.status_code == 200
    assert fetched.json()["id"] == report_id
    deleted = client.delete(f"/api/v1/reports/{report_id}")
    assert deleted.status_code == 204
    missing = client.get(f"/api/v1/reports/{report_id}")
    assert missing.status_code == 404


def test_unknown_report_is_not_found(client: TestClient) -> None:
    response = client.get(f"/api/v1/reports/{uuid4()}")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "REPORT_NOT_FOUND"


def test_generation_failure_persists_failed_status(
    tmp_path: Path,
    failing_allure: Path,
) -> None:
    settings = Settings(
        data_dir=tmp_path / "data",
        allure_bin=str(failing_allure),
        public_base_url="http://testserver",
    )
    with TestClient(create_app(settings)) as client:
        files = {"file": ("results.zip", build_results_zip(), "application/zip")}
        response = client.post("/api/v1/reports", files=files)
        assert response.status_code == 502
        report_id = response.json()["error"]["details"][1]["report_id"]
        fetched = client.get(f"/api/v1/reports/{report_id}")
        assert fetched.status_code == 200
        assert fetched.json()["status"] == "failed"


def test_filter_by_project(client: TestClient) -> None:
    files = {"file": ("results.zip", build_results_zip(), "application/zip")}
    client.post("/api/v1/reports", files=files, data={"project": "alpha"})
    listed = client.get("/api/v1/reports", params={"project": "beta"})
    assert listed.json()["pagination"]["total"] == 0
    listed = client.get("/api/v1/reports", params={"project": "alpha"})
    assert listed.json()["pagination"]["total"] == 1
