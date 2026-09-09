from fastapi.testclient import TestClient


def test_health_is_public(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["allure_version"] == "2.32.0-fake"
