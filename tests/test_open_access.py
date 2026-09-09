from fastapi.testclient import TestClient

from tests.support.zips import build_results_zip


def test_list_reports_is_open(client: TestClient) -> None:
    response = client.get("/api/v1/reports")
    assert response.status_code == 200
    assert response.json()["data"] == []


def test_upload_and_view_without_credentials(client: TestClient) -> None:
    files = {"file": ("results.zip", build_results_zip(), "application/zip")}
    created = client.post("/api/v1/reports", files=files)
    assert created.status_code == 201
    report_id = created.json()["id"]
    response = client.get(f"/reports/{report_id}/")
    assert response.status_code == 200
    assert b"fake-allure" in response.content
