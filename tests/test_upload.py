from fastapi.testclient import TestClient

from tests.support.zips import build_results_zip, build_zip_with_member


def test_corrupt_zip_returns_400_and_cleans_disk(
    client: TestClient,
    settings,
) -> None:
    files = {"file": ("results.zip", b"not-a-zip-file", "application/zip")}
    response = client.post("/api/v1/reports", files=files)
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_ZIP"
    reports_root = settings.data_dir / "reports"
    leftovers = list(reports_root.iterdir()) if reports_root.exists() else []
    assert leftovers == []


def test_missing_results_returns_422(
    client: TestClient,
    settings,
) -> None:
    files = {
        "file": (
            "results.zip",
            build_zip_with_member("notes.txt", b"hi"),
            "application/zip",
        )
    }
    response = client.post("/api/v1/reports", files=files)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "MISSING_RESULTS"
    leftovers = list((settings.data_dir / "reports").iterdir())
    assert leftovers == []


def test_zip_slip_upload_is_rejected(
    client: TestClient,
    settings,
) -> None:
    files = {
        "file": (
            "results.zip",
            build_zip_with_member("../evil.txt", b"hacked"),
            "application/zip",
        )
    }
    response = client.post("/api/v1/reports", files=files)
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "ZIP_SLIP"
    assert not (settings.data_dir.parent / "evil.txt").exists()


def test_content_length_limit(client: TestClient) -> None:
    files = {"file": ("results.zip", build_results_zip(), "application/zip")}
    headers = {"content-length": str(10 * 1024 * 1024)}
    response = client.post("/api/v1/reports", files=files, headers=headers)
    assert response.status_code == 413
    assert response.json()["error"]["code"] == "PAYLOAD_TOO_LARGE"


def test_empty_upload_rejected(client: TestClient) -> None:
    files = {"file": ("results.zip", b"", "application/zip")}
    response = client.post("/api/v1/reports", files=files)
    assert response.status_code == 400


def test_wrong_content_type_rejected(client: TestClient) -> None:
    files = {"file": ("results.zip", build_results_zip(), "application/json")}
    response = client.post("/api/v1/reports", files=files)
    assert response.status_code == 400


def test_report_path_redirects(client: TestClient) -> None:
    files = {"file": ("results.zip", build_results_zip(), "application/zip")}
    created = client.post("/api/v1/reports", files=files)
    report_id = created.json()["id"]
    response = client.get(f"/reports/{report_id}", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"].endswith(f"/reports/{report_id}/")


def test_static_unknown_report_is_not_found(client: TestClient) -> None:
    response = client.get("/reports/11111111-1111-1111-1111-111111111111/")
    assert response.status_code == 404
