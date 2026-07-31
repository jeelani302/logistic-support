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


def test_demo_logs_are_synthetic_and_available():
    response = client.get("/demo-logs")
    assert response.status_code == 200
    assert len(response.json()["logs"]) >= 5
    assert all("raw_text" in item for item in response.json()["logs"])


def test_generate_demo_log_does_not_call_llm():
    response = client.post("/demo-logs/generate")
    assert response.status_code == 200
    assert {"id", "label", "raw_text"} <= response.json().keys()


def test_webhook_requires_configured_secret(monkeypatch):
    monkeypatch.setenv("WEBHOOK_SECRET", "test-secret")
    response = client.post(
        "/webhooks/ticket",
        json={"raw_text": "Package PKG-1 failed at the Delhi sorting hub."},
    )
    assert response.status_code == 401


def test_webhook_flattens_ticket_and_returns_analysis(monkeypatch):
    expected = {
        "tracking_id": "PKG-1",
        "location": "Delhi",
        "issue_type": "Scan failure",
        "incident_summary": "The package scan failed.",
        "observed_facts": ["The package is at the Delhi hub."],
        "hypotheses": [],
        "missing_evidence": ["Scanner logs"],
        "recommended_actions": ["Inspect scanner logs."],
        "prevention_measures": ["Alert on repeated scan failures."],
        "draft_support_response": "We are investigating a processing delay.",
        "overall_confidence": "medium",
    }
    monkeypatch.setenv("WEBHOOK_SECRET", "test-secret")
    monkeypatch.setattr("app.main.analyze_ticket", lambda raw_text: expected)
    response = client.post(
        "/webhooks/ticket",
        headers={"X-Webhook-Secret": "test-secret"},
        json={
            "source": "zendesk",
            "event_id": "evt-1",
            "ticket": {
                "id": "123",
                "subject": "Scan failed",
                "description": "Package PKG-1 failed at the Delhi sorting hub.",
            },
        },
    )
    assert response.status_code == 200
    assert response.json()["observed_facts"] == expected["observed_facts"]


def test_invalid_provider_output_does_not_leak_details(monkeypatch):
    monkeypatch.setattr(
        "app.main.analyze_ticket",
        lambda raw_text: (_ for _ in ()).throw(ValueError("sensitive raw output")),
    )
    response = client.post(
        "/analyze-ticket",
        json={"raw_text": "Package PKG-1 failed at the Delhi sorting hub."},
    )
    assert response.status_code == 502
    assert "sensitive raw output" not in response.json()["detail"]
