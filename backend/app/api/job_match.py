"""Job matching API endpoints with real DB persistence."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.ai import get_ai_provider
from app.core.database import get_db
from app.models import JobDescription, JobMatch
from app.schemas.job_match import JobMatchRequest, JobMatchResponse
from app.security.auth import get_current_user, get_or_create_user

router = APIRouter(prefix="/job-matches", tags=["job-matches"])


class JobDescriptionCreate(BaseModel):
    title: str | None = None
    description: str


class JobDescriptionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str | None
    description: str
    created_at: str


class JobMatchDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    job_description_id: str
    match_score: int
    created_at: str


@router.post(
    "",
    response_model=JobMatchResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create job match",
)
async def create_job_match(
    request: JobMatchRequest,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> JobMatchResponse:
    """Compare resume skills against a job description and persist the result."""
    get_or_create_user(db, user["user_id"], user.get("email"))

    resume_text_sample = "Skills: " + ", ".join(request.resume_skills)
    ai_provider = get_ai_provider()
    raw_result = await ai_provider.match_job(
        resume_text=resume_text_sample,
        job_description=request.job_requirements,
    )
    result = JobMatchResponse.model_validate(raw_result)

    # Persist job description
    title = (
        request.job_requirements[:80]
        if len(request.job_requirements) > 80
        else request.job_requirements
    )
    job_desc = JobDescription(
        user_id=user["user_id"],
        title=title,
        description=request.job_requirements,
    )
    db.add(job_desc)
    db.commit()
    db.refresh(job_desc)

    # Persist match result
    match = JobMatch(
        job_description_id=job_desc.id,
        match_score=result.match_score,
        result_json=result.model_dump(),
    )
    db.add(match)
    db.commit()

    return result


@router.get(
    "",
    summary="List user's job descriptions",
)
async def list_job_descriptions(
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[JobDescriptionResponse]:
    """List all job descriptions saved by the current user."""
    jobs = (
        db.query(JobDescription)
        .filter(JobDescription.user_id == user["user_id"])
        .order_by(JobDescription.created_at.desc())
        .all()
    )

    return [
        JobDescriptionResponse(
            id=j.id,
            title=j.title,
            description=j.description,
            created_at=j.created_at.isoformat(),
        )
        for j in jobs
    ]


@router.get(
    "/{match_id}",
    summary="Get match details",
)
async def get_match_details(
    match_id: str,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> JobMatchResponse:
    """Get a specific job match. Ownership enforced."""
    match = db.query(JobMatch).filter(JobMatch.id == match_id).first()
    if not match:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Match not found")

    job_desc = (
        db.query(JobDescription)
        .filter(JobDescription.id == match.job_description_id)
        .first()
    )
    if not job_desc or job_desc.user_id != user["user_id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    return JobMatchResponse(**match.result_json)
