from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root_returns_welcome_message():
    response = client.get("/")
    assert response.status_code == 200
    assert "Welcome" in response.json()["message"]


def test_health_check_is_ok():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_services_health_has_expected_fields():
    response = client.get("/api/health/services")
    assert response.status_code == 200
    data = response.json()
    assert "postgres" in data
    assert "redis" in data