
from fastapi.testclient import TestClient

import main

client = TestClient(main.app)


def mock_ai_review(monkeypatch):
    """Prevent tests from waiting for the local Ollama model."""
    monkeypatch.setattr(
        main,
        "explain_findings",
        lambda code, findings: {
            "summary": "Potential security issues detected.",
            "explanations": [],
        },
    )


def test_home():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["status"] == "running"


def test_health():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_review_detects_security_issues(monkeypatch):
    mock_ai_review(monkeypatch)

    code = """
import subprocess

def run(user_input):
    subprocess.call("echo " + user_input, shell=True)
    return eval(user_input)
"""

    response = client.post("/review", json={"code": code})

    assert response.status_code == 200

    result = response.json()
    assert result["issue_count"] >= 2

    rule_ids = {
        finding["rule_id"]
        for finding in result["findings"]
    }

    assert "B602" in rule_ids
    assert "B307" in rule_ids


def test_review_rejects_empty_code():
    response = client.post("/review", json={"code": "   "})

    assert response.status_code == 400
    assert response.json()["detail"] == "Code cannot be empty."


def test_review_rejects_oversized_code():
    code = "a" * 100_001

    response = client.post("/review", json={"code": code})

    assert response.status_code == 413
    assert response.json()["detail"] == "Code exceeds the 100 KB limit."


def test_review_includes_ai_explanations(monkeypatch):
    mock_ai_review(monkeypatch)

    response = client.post(
        "/review",
        json={
            "code": (
                "def calculate(user_input):\n"
                "    return eval(user_input)\n"
            )
        },
    )

    assert response.status_code == 200

    data = response.json()
    assert "ai_review" in data
    assert data["ai_review"]["summary"] == (
        "Potential security issues detected."
    )
    assert data["ai_review"]["explanations"] == []
