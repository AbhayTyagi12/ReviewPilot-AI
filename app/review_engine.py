
import json
import subprocess
import sys
from pathlib import Path

from pydantic import BaseModel


class Finding(BaseModel):
    tool: str
    rule_id: str
    severity: str
    message: str
    file: str
    line: int
    confidence: str | None = None
    description: str | None = None
    suggestion: str | None = None


def run_ruff(file_path: str) -> list[Finding]:
    """Run Ruff on a Python file and normalize its findings."""
    target = Path(file_path).resolve()

    try:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "ruff",
                "check",
                str(target),
                "--output-format",
                "json",
            ],
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )
    except subprocess.TimeoutExpired as error:
        raise RuntimeError("Ruff timed out after 10 seconds.") from error

    if result.returncode not in (0, 1):
        raise RuntimeError(
            f"Ruff failed with exit code {result.returncode}: "
            f"{result.stderr.strip() or result.stdout[:300]}"
        )

    try:
        raw_findings = json.loads(result.stdout)
    except json.JSONDecodeError as error:
        raise RuntimeError(
            "Ruff returned invalid JSON. "
            f"Exit code: {result.returncode}. "
            f"Output: {result.stdout[:300]!r}. "
            f"Stderr: {result.stderr[:300]!r}"
        ) from error

    findings = []

    for item in raw_findings:
        findings.append(
            Finding(
                tool="ruff",
                rule_id=item["code"],
                severity=item["severity"],
                message=item["message"],
                file=str(file_path),
                line=item["location"]["row"],
                description=item.get("name"),
                suggestion=(
                    item["fix"]["message"]
                    if item.get("fix")
                    else None
                ),
            )
        )

    return findings


def run_bandit(file_path: str) -> list[Finding]:
    """Run Bandit on a Python file and normalize its findings."""
    target = Path(file_path).resolve()

    try:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "bandit",
                "-f",
                "json",
                str(target),
            ],
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )
    except subprocess.TimeoutExpired as error:
        raise RuntimeError("Bandit timed out after 10 seconds.") from error

    if result.returncode not in (0, 1):
        raise RuntimeError(
            f"Bandit failed with exit code {result.returncode}: "
            f"{result.stderr.strip() or result.stdout[:300]}"
        )

    try:
        report = json.loads(result.stdout)
    except json.JSONDecodeError as error:
        raise RuntimeError(
            "Bandit returned invalid JSON. "
            f"Exit code: {result.returncode}. "
            f"Output: {result.stdout[:300]!r}. "
            f"Stderr: {result.stderr[:300]!r}"
        ) from error

    findings = []

    for item in report.get("results", []):
        findings.append(
            Finding(
                tool="bandit",
                rule_id=item["test_id"],
                severity=item.get("issue_severity", "LOW").lower(),
                message=item["issue_text"],
                file=str(file_path),
                line=item["line_number"],
                confidence=item.get("issue_confidence", "").lower(),
                description=item.get("test_name"),
                suggestion=item.get("more_info"),
            )
        )

    return findings


def review_python_file(file_path: str) -> dict:
    """Run all configured analyzers on a Python file."""
    ruff_findings = run_ruff(file_path)
    bandit_findings = run_bandit(file_path)

    findings = ruff_findings + bandit_findings

    return {
        "file": file_path,
        "issue_count": len(findings),
        "findings": [finding.model_dump() for finding in findings],
    }
