"""Mock interview API endpoints with real DB persistence."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.ai import get_ai_provider
from app.core.config import settings
from app.core.database import get_db
from app.models import Interview, InterviewQuestion
from app.schemas.interview import InterviewRequest, InterviewResponse
from app.security.auth import get_current_user, get_or_create_user
from app.security.rate_limit import check_rate_limit
from app.services.interview_service import start_interview as do_start

router = APIRouter(prefix="/interviews", tags=["interviews"])


class AnswerSubmission(BaseModel):
    answer: str
    context: str = ""


class EvaluationResponse(BaseModel):
    interview_id: str
    score: int
    feedback: str
    dimensions: list
    improvements: list


class InterviewDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    interview_type: str
    status: str
    created_at: str
    completed_at: str | None


@router.post(
    "",
    response_model=InterviewResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start interview",
)
async def start_interview_endpoint(
    request: InterviewRequest,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> InterviewResponse:
    """Start a new mock interview session. Persisted to DB."""
    get_or_create_user(db, user["user_id"], user.get("email"))

    result = do_start(
        interview_type=request.interview_type,
        question=request.question,
    )

    # Persist interview session
    interview = Interview(
        id=result.interview_id,
        user_id=user["user_id"],
        interview_type=result.category,
        status="active",
    )
    db.add(interview)

    # Persist the first question
    question = InterviewQuestion(
        interview_id=result.interview_id,
        question=result.question,
    )
    db.add(question)
    db.commit()

    return result


@router.post(
    "/{interview_id}/answers",
    response_model=EvaluationResponse,
    summary="Submit answer",
)
async def submit_answer_endpoint(
    interview_id: str,
    submission: AnswerSubmission,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> EvaluationResponse:
    """Submit an interview answer for AI evaluation. Persisted to DB."""
    check_rate_limit(
        user_id=user["user_id"],
        action="interview",
        max_requests=settings.rate_limit_interview,
    )

    # Verify ownership
    interview = db.query(Interview).filter(Interview.id == interview_id).first()
    if not interview:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interview not found")
    if interview.user_id != user["user_id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    # Find the active question or context
    existing_q = (
        db.query(InterviewQuestion)
        .filter(InterviewQuestion.interview_id == interview_id)
        .order_by(InterviewQuestion.asked_at.desc())
        .first()
    )
    question_text = (
        existing_q.question
        if (existing_q and existing_q.question)
        else (submission.context or "General interview question")
    )

    ai_provider = get_ai_provider()
    result = await ai_provider.evaluate_answer(
        question=question_text,
        answer=submission.answer,
    )
    result["interview_id"] = interview_id

    # Update the existing question row in-place, or create if missing
    if existing_q and not existing_q.answer:
        existing_q.answer = submission.answer
        existing_q.evaluation_json = result
        existing_q.score = result.get("score")
        existing_q.answered_at = datetime.now(timezone.utc)
    else:
        new_q = InterviewQuestion(
            interview_id=interview_id,
            question=question_text,
            answer=submission.answer,
            evaluation_json=result,
            score=result.get("score"),
            answered_at=datetime.now(timezone.utc),
        )
        db.add(new_q)

    db.commit()

    return EvaluationResponse(**result)


@router.get(
    "/{interview_id}",
    response_model=InterviewDetail,
    summary="Get interview details",
)
async def get_interview_details(
    interview_id: str,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> InterviewDetail:
    """Get interview session details. Ownership enforced."""
    interview = db.query(Interview).filter(Interview.id == interview_id).first()
    if not interview:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interview not found")
    if interview.user_id != user["user_id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    return InterviewDetail(
        id=interview.id,
        interview_type=interview.interview_type,
        status=interview.status,
        created_at=interview.created_at.isoformat(),
        completed_at=interview.completed_at.isoformat() if interview.completed_at else None,
    )


@router.post(
    "/{interview_id}/complete",
    summary="Mark interview as complete",
)
async def complete_interview(
    interview_id: str,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Mark an interview session as completed."""
    interview = db.query(Interview).filter(Interview.id == interview_id).first()
    if not interview:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interview not found")
    if interview.user_id != user["user_id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    interview.status = "completed"
    interview.completed_at = datetime.now(timezone.utc)
    db.commit()
    return {"message": "Interview marked as completed", "interview_id": interview_id}
