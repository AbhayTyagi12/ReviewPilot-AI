
import subprocess

import pytest

from app import review_engine


def test_run_ruff_timeout_raises_runtime_error(monkeypatch, tmp_path):
    """A Ruff timeout should raise a clear error."""

    def fake_run(*args, **kwargs):
        raise subprocess.TimeoutExpired(
            cmd="ruff",
            timeout=10,
        )

    monkeypatch.setattr(review_engine.subprocess, "run", fake_run)

    target = tmp_path / "sample.py"
    target.write_text("print('hello')\n", encoding="utf-8")

    with pytest.raises(
        RuntimeError,
        match="Ruff timed out after 10 seconds",
    ):
        review_engine.run_ruff(str(target))

def test_run_bandit_timeout_raises_runtime_error(monkeypatch, tmp_path):
    """A Bandit timeout should raise a clear error."""

    def fake_run(*args, **kwargs):
        raise subprocess.TimeoutExpired(
            cmd="bandit",
            timeout=10,
        )

    monkeypatch.setattr(review_engine.subprocess, "run", fake_run)

    target = tmp_path / "sample.py"
    target.write_text("print('hello')\n", encoding="utf-8")

    with pytest.raises(
        RuntimeError,
        match="Bandit timed out after 10 seconds",
    ):
        review_engine.run_bandit(str(target))

def test_run_ruff_invalid_json_raises_runtime_error(monkeypatch, tmp_path):
    """Malformed Ruff output should raise a clear error."""

    class FakeResult:
        returncode = 0
        stdout = "not valid JSON"
        stderr = ""

    def fake_run(*args, **kwargs):
        return FakeResult()

    monkeypatch.setattr(review_engine.subprocess, "run", fake_run)

    target = tmp_path / "sample.py"
    target.write_text("print('hello')\n", encoding="utf-8")

    with pytest.raises(
        RuntimeError,
        match="Ruff returned invalid JSON",
    ):
        review_engine.run_ruff(str(target))

def test_run_bandit_invalid_json_raises_runtime_error(monkeypatch, tmp_path):
    """Malformed Bandit output should raise a clear error."""

    class FakeResult:
        returncode = 0
        stdout = "not valid JSON"
        stderr = ""

    def fake_run(*args, **kwargs):
        return FakeResult()

    monkeypatch.setattr(review_engine.subprocess, "run", fake_run)

    target = tmp_path / "sample.py"
    target.write_text("print('hello')\n", encoding="utf-8")

    with pytest.raises(
        RuntimeError,
        match="Bandit returned invalid JSON",
    ):
        review_engine.run_bandit(str(target))
