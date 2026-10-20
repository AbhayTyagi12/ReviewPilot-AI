from fastapi.testclient import TestClient
import json
import main
client = TestClient(main.app)

from app import ai_reviewer


SAMPLE_FINDINGS = [
    {
        "tool": "bandit",
        "rule_id": "B307",
        "severity": "medium",
        "message": "Use of possibly insecure function: eval",
        "file": "review_input.py",
        "line": 2,
        "confidence": "high",
        "description": "Use of eval() may allow arbitrary code execution.",
        "suggestion": "Avoid eval() on untrusted input.",
    }
]


def test_ai_timeout_returns_fallback(monkeypatch):
    """A timeout should return a fallback instead of crashing."""

    def fake_urlopen(request, timeout):
        raise TimeoutError("simulated timeout")

    monkeypatch.setattr(
        ai_reviewer.urllib.request,
        "urlopen",
        fake_urlopen,
    )

    result = ai_reviewer.explain_findings(
        "def calculate(value):\n    return eval(value)\n",
        SAMPLE_FINDINGS,
    )

    assert result["summary"] == (
        "AI explanations are temporarily unavailable."
    )
    assert result["explanations"] == []


def test_invalid_ai_json_returns_fallback(monkeypatch):
    """Malformed model JSON should be handled gracefully."""

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            return False

        def read(self):
            return json.dumps(
                {
                    "message": {
                        "content": "{this is not valid JSON"
                    }
                }
            ).encode("utf-8")

    def fake_urlopen(request, timeout):
        return FakeResponse()

    monkeypatch.setattr(
        ai_reviewer.urllib.request,
        "urlopen",
        fake_urlopen,
    )

    result = ai_reviewer.explain_findings(
        "def calculate(value):\n    return eval(value)\n",
        SAMPLE_FINDINGS,
    )

    assert result["summary"] == (
        "AI explanations are temporarily unavailable."
    )
    assert result["explanations"] == []


def test_no_findings_skips_ai_request(monkeypatch):
    """No findings should return immediately without contacting Ollama."""

    def unexpected_urlopen(request, timeout):
        raise AssertionError(
            "Ollama should not be called when there are no findings."
        )

    monkeypatch.setattr(
        ai_reviewer.urllib.request,
        "urlopen",
        unexpected_urlopen,
    )

    result = ai_reviewer.explain_findings(
        "def add(a, b):\n    return a + b\n",
        [],
    )

    assert result["summary"] == (
        "No issues were detected by the static analyzers."
    )
    assert result["explanations"] == []



def test_review_keeps_static_findings_when_ai_unavailable(monkeypatch):
    """Static analysis should work even when AI explanations are unavailable."""

    monkeypatch.setattr(
        main,
        "explain_findings",
        lambda code, findings: {
            "summary": "AI explanations are temporarily unavailable.",
            "explanations": [],
        },
    )

    code = "def calculate(user_input):\n    return eval(user_input)\n"

    response = client.post("/review", json={"code": code})

    assert response.status_code == 200
    result = response.json()

    assert result["issue_count"] >= 1

    rule_ids = {
        finding["rule_id"] for finding in result["findings"]
    }
    assert "B307" in rule_ids

    assert result["ai_review"]["summary"] == (
        "AI explanations are temporarily unavailable."
    )
    assert result["ai_review"]["explanations"] == []
