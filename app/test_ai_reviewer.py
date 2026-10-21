import json

from fastapi.testclient import TestClient

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

def test_valid_ai_response_returns_matching_explanation(monkeypatch):
    """A valid Ollama response should return its summary and explanation."""

    ai_content = {
        "summary": "The code uses eval(), which can be unsafe.",
        "explanations": [
            {
                "rule_id": "B307",
                "explanation": "eval() can execute arbitrary code.",
                "suggestion": "Replace eval() with a safe alternative.",
            }
        ],
    }

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            return False

        def read(self):
            return json.dumps(
                {
                    "message": {
                        "content": json.dumps(ai_content)
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

    assert result["summary"] == ai_content["summary"]
    assert len(result["explanations"]) == 1
    assert result["explanations"][0]["rule_id"] == "B307"

def test_ai_rejects_explanations_for_unknown_rules(monkeypatch):
    """Reject AI explanations for rules not reported by static analysis."""

    ai_content = {
        "summary": "Review completed.",
        "explanations": [
            {
                "rule_id": "B307",
                "explanation": "eval() can execute arbitrary code.",
                "suggestion": "Avoid eval() on untrusted input.",
            },
            {
                "rule_id": "FAKE999",
                "explanation": "This rule was not reported by static analysis.",
                "suggestion": "Unsupported suggestion.",
            },
        ],
    }

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            return False

        def read(self):
            return json.dumps({
                "message": {
                    "content": json.dumps(ai_content)
                }
            }).encode("utf-8")

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

    returned_rule_ids = {
        item["rule_id"] for item in result["explanations"]
    }

    assert "B307" in returned_rule_ids
    assert "FAKE999" not in returned_rule_ids
    assert len(result["explanations"]) == 1

def test_missing_message_in_ollama_response_returns_fallback(monkeypatch):
    """A response without the message field should fail gracefully."""

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            return False

        def read(self):
            return json.dumps({"unexpected": "response"}).encode("utf-8")

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

def test_invalid_explanations_type_returns_fallback(monkeypatch):
    """A non-list explanations field should return a safe fallback."""

    ai_content = {
        "summary": "Review completed.",
        "explanations": "This should be a list, not a string.",
    }

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            return False

        def read(self):
            return json.dumps(
                {
                    "message": {
                        "content": json.dumps(ai_content)
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
