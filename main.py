
from fastapi import FastAPI

app = FastAPI(
    title="ReviewPilot AI",
    description="AI-powered code review and bug detection agent",
    version="0.1.0",
)


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
