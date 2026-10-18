
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_home():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["message"] == "Welcome to ReviewPilot AI!"


def test_health():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_review_detects_security_issues():
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

    rule_ids = {finding["rule_id"] for finding in result["findings"]}
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

