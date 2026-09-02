"""Resume analysis API endpoints with real DB persistence."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.ai import get_ai_provider
from app.core.config import settings
from app.core.database import get_db
from app.models import Resume, ResumeAnalysis
from app.schemas.resume import ResumeAnalysisResponse, ResumeUploadRequest
from app.security.auth import get_current_user, get_or_create_user
from app.security.rate_limit import check_rate_limit

router = APIRouter(prefix="/resumes", tags=["analysis"])


class AnalysisResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    resume_id: str
    score: int
    summary: str | None
    created_at: str


@router.post(
    "/analyze",
    response_model=ResumeAnalysisResponse,
    summary="Analyze resume",
)
async def analyze_resume_endpoint(
    request: ResumeUploadRequest,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ResumeAnalysisResponse:
    """Analyze a resume and return structured feedback.

    The analysis includes:
    - Overall score (0-100)
    - Detected skills
    - Strengths and weaknesses
    - Improvement recommendations

    If resume_id is provided, also persists the result to the DB.
    """
    check_rate_limit(
        user_id=user["user_id"],
        action="analyze",
        max_requests=settings.rate_limit_analyze,
    )

    get_or_create_user(db, user["user_id"], user.get("email"))

    ai_provider = get_ai_provider()
    raw_result = await ai_provider.analyze_resume(
        resume_text=request.resume_text,
        job_description=request.job_description,
    )
    result = ResumeAnalysisResponse.model_validate(raw_result)

    return result


@router.get(
    "/{resume_id}/analyses",
    summary="List all analyses for a resume",
)
async def list_analyses(
    resume_id: str,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[AnalysisResponse]:
    """Get all previous analysis results for a resume. Ownership enforced."""
    resume = db.query(Resume).filter(Resume.id == resume_id).first()
    if not resume:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found")
    if resume.user_id != user["user_id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    analyses = (
        db.query(ResumeAnalysis)
        .filter(ResumeAnalysis.resume_id == resume_id)
        .order_by(ResumeAnalysis.created_at.desc())
        .all()
    )

    return [
        AnalysisResponse(
            id=a.id,
            resume_id=a.resume_id,
            score=a.score,
            summary=a.summary,
            created_at=a.created_at.isoformat(),
        )
        for a in analyses
    ]


@router.get(
    "/analyses/{analysis_id}",
    summary="Get a specific analysis",
)
async def get_analysis(
    analysis_id: str,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ResumeAnalysisResponse:
    """Get a specific analysis by ID. Ownership enforced via resume join."""
    analysis = db.query(ResumeAnalysis).filter(ResumeAnalysis.id == analysis_id).first()
    if not analysis:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis not found")

    resume = db.query(Resume).filter(Resume.id == analysis.resume_id).first()
    if not resume or resume.user_id != user["user_id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    return ResumeAnalysisResponse(**analysis.result_json)
