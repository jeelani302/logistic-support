from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_home_serves_interface():
    response = client.get("/")
    assert response.status_code == 200
    assert "Logistics RCA Agent" in response.text


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_ticket_validation_rejects_short_input():
    response = client.post("/analyze-ticket", json={"raw_text": "short"})
    assert response.status_code == 422
