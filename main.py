import tempfile
import subprocess
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from app.review_engine import review_python_file
from app.ai_reviewer import explain_findings

app = FastAPI(
    title="ReviewPilot AI",
    description="AI-powered code review and bug detection agent",
    version="0.1.0",
)


class ReviewRequest(BaseModel):
    code: str


@app.get("/")
def home():
    return {
        "message": "Welcome to ReviewPilot AI!",
        "status": "running",
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "ReviewPilot AI",
    }



@app.post("/review")
def review_code(request: ReviewRequest):
    """Review submitted Python code for quality and security issues."""

    if not request.code.strip():
        raise HTTPException(
            status_code=400,
            detail="Code cannot be empty.",
        )

    if len(request.code.encode("utf-8")) > 100_000:
        raise HTTPException(
            status_code=413,
            detail="Code exceeds the 100 KB limit.",
        )

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "review_input.py"
            target.write_text(request.code, encoding="utf-8")

            result = review_python_file(str(target))

        # Add local AI explanations without replacing static findings.
        try:
            result["ai_review"] = explain_findings(
                request.code,
                result.get("findings", []),
            )
        except Exception:
            # Static analysis should remain useful if AI fails.
            result["ai_review"] = {
                "summary": "AI explanations are temporarily unavailable.",
                "explanations": [],
            }

        return result

    except subprocess.TimeoutExpired:
        raise HTTPException(
            status_code=504,
            detail="Code analysis timed out.",
        )
    except RuntimeError as error:
        raise HTTPException(
            status_code=500,
            detail=f"Code review failed: {error}",
        ) from error
    except OSError as error:
        raise HTTPException(
            status_code=500,
            detail="Unable to process the submitted code.",
        ) from error
