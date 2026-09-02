"""User management and career readiness dashboard API."""

from __future__ import annotations

import os

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.errors import not_found
from app.models import Interview, JobMatch, Resume, ResumeAnalysis, User
from app.security.auth import get_current_user, get_or_create_user
from app.services.scoring import calculate_career_readiness

router = APIRouter(prefix="/users", tags=["users"])


@router.get(
    "/me",
    summary="Get current user profile",
)
def get_my_profile(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Get authenticated user info."""
    user_id = current_user["user_id"]
    email = current_user.get("email")
    user = get_or_create_user(db, user_id, email)
    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "created_at": user.created_at.isoformat(),
    }


@router.get(
    "/me/dashboard",
    summary="Get user career readiness dashboard data",
)
def get_user_dashboard(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Get dynamic career readiness score and activity summaries for the current user."""
    user_id = current_user["user_id"]
    get_or_create_user(db, user_id, current_user.get("email"))

    # Fetch latest resume analysis
    latest_resume = (
        db.query(Resume)
        .filter(Resume.user_id == user_id)
        .order_by(Resume.created_at.desc())
        .first()
    )
    latest_analysis = None
    if latest_resume and latest_resume.analyses:
        latest_analysis = latest_resume.analyses[-1]

    # Fetch latest job match
    latest_job_matches = (
        db.query(JobMatch)
        .join(JobMatch.job_description)
        .filter(JobMatch.job_description.has(user_id=user_id))
        .order_by(JobMatch.created_at.desc())
        .all()
    )
    latest_match = latest_job_matches[0] if latest_job_matches else None

    # Fetch latest interview score
    interviews = (
        db.query(Interview)
        .filter(Interview.user_id == user_id)
        .order_by(Interview.created_at.desc())
        .all()
    )
    interview_scores: list[int] = []
    for itw in interviews:
        for q in itw.questions:
            if q.score is not None:
                interview_scores.append(q.score)

    avg_interview_score = (
        int(sum(interview_scores) / len(interview_scores))
        if interview_scores
        else None
    )

    resume_score = latest_analysis.score if latest_analysis else None
    job_match_score = int(latest_match.match_score) if latest_match and latest_match.match_score is not None else None
    interview_score = avg_interview_score

    # Estimate skill coverage
    skill_coverage = None
    if latest_analysis and latest_analysis.result_json:
        skills = latest_analysis.result_json.get("skills", [])
        if skills:
            skill_coverage = min(100, len(skills) * 8)

    has_data = any(
        v is not None
        for v in [resume_score, job_match_score, interview_score, skill_coverage]
    )

    career_readiness = calculate_career_readiness(
        resume_score=resume_score,
        job_match_score=job_match_score,
        interview_score=interview_score,
        skill_coverage=skill_coverage,
    )

    return {
        "has_data": has_data,
        "career_readiness": career_readiness,
        "resume_count": db.query(Resume).filter(Resume.user_id == user_id).count(),
        "job_match_count": len(latest_job_matches),
        "interview_count": len(interviews),
    }


@router.delete(
    "/me",
    summary="Delete my account and all associated data",
    description=(
        "Permanently deletes the authenticated user's account and all resumes, "
        "analyses, job descriptions, interviews, and associated physical files on disk. "
        "GDPR Article 17 – Right to Erasure."
    ),
)
def delete_my_account(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Delete the requesting user's account, all personal data, and physical files."""
    user_id = current_user["user_id"]
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise not_found("User")

    # Collect storage paths before cascade deletion
    storage_paths = [r.storage_path for r in user.resumes if r.storage_path]

    # Delete DB records
    db.delete(user)
    db.commit()

    # Delete physical files from disk
    upload_dir = settings.upload_dir
    for path in storage_paths:
        file_path = os.path.join(upload_dir, path)
        try:
            os.remove(file_path)
        except OSError:
            pass

    return {
        "message": "Account and all associated data have been permanently deleted.",
        "deleted_user_id": user_id,
        "files_deleted": len(storage_paths),
    }
