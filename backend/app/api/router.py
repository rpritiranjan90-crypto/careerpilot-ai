"""Core API routes for CareerPilot AI."""

from fastapi import APIRouter

from app.api import analysis, improvement, interview, job_match
from app.api.upload import router as upload_router
from app.api.user import router as user_router

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(upload_router)
api_router.include_router(analysis.router)
api_router.include_router(job_match.router)
api_router.include_router(interview.router)
api_router.include_router(user_router)
api_router.include_router(improvement.router)
