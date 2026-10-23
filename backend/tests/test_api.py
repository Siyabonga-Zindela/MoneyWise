from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.routes import analysis
from backend.app.services.ai_analysis.baseline import analyze_text as analyze_baseline


client = TestClient(app)


def test_analysis_endpoint_returns_assessment(monkeypatch):
    async def fake_analyze_text(text):
        return analyze_baseline(text)

    monkeypatch.setattr(analysis, "analyze_text", fake_analyze_text)

    response = client.post(
        "/api/v1/analysis",
        json={"text": "Send your OTP now to stop your account being closed."},
    )

    assert response.status_code == 200
    result = response.json()
    assert result["category"] == "high"
    assert result["indicators"][0]["code"] == "credential_request"
    assert result["source"] == "deterministic_rules"


def test_analysis_endpoint_rejects_invalid_input():
    response = client.post("/api/v1/analysis", json={"text": "  "})

    assert response.status_code == 422


def test_analysis_endpoint_rejects_oversized_input():
    response = client.post("/api/v1/analysis", json={"text": "x" * 5001})

    assert response.status_code == 422
