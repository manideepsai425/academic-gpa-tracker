"""
Application entry point. Run locally with:
    uvicorn app.main:app --reload
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, compare, records
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title="Academic GPA Tracker API",
    version="1.0.0",
    description="Backend API for tracking academic GPA history over time.",
)

# allow_credentials=True is required for the httpOnly cookie to be sent
# cross-origin — but the CORS spec forbids combining that with a
# wildcard "*" origin, hence the explicit origin list from settings
# rather than allow_origins=["*"].
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(records.router)
app.include_router(compare.router)


@app.get("/")
def root():
    return {"status": "ok", "service": "Academic GPA Tracker API"}


@app.get("/health")
def health_check():
    """Render pings this to keep a free-tier instance from sleeping,
    and to verify the deploy succeeded."""
    return {"status": "healthy"}
