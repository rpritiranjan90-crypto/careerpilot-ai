"""Career Improvement Plan API endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.improvement import CareerImprovementPlan
from app.security.auth import get_current_user, get_or_create_user
from app.services.improvement_service import (
    generate_career_improvement_plan,
    record_career_readiness_snapshot,
    toggle_user_action_item,
)

router = APIRouter(prefix="/improvement-plan", tags=["improvement"])


@router.get(
    "",
    response_model=CareerImprovementPlan,
    summary="Get current user personalized career improvement plan",
)
def get_improvement_plan(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CareerImprovementPlan:
    """Retrieve the verified, actionable career improvement plan for the authenticated user."""
    user_id = current_user["user_id"]
    get_or_create_user(db, user_id, current_user.get("email"))

    return generate_career_improvement_plan(
        db=db, user_id=user_id, create_snapshot_if_none=True
    )


@router.post(
    "/refresh",
    response_model=CareerImprovementPlan,
    summary="Refresh improvement plan and record new historical snapshot",
)
def refresh_improvement_plan(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CareerImprovementPlan:
    """Recalculate improvement plan and record an explicit snapshot."""
    user_id = current_user["user_id"]
    get_or_create_user(db, user_id, current_user.get("email"))

    plan = generate_career_improvement_plan(
        db=db, user_id=user_id, create_snapshot_if_none=False
    )
    if plan.has_data:
        record_career_readiness_snapshot(
            db=db,
            user_id=user_id,
            overall_score=plan.overall_score,
            resume_score=plan.progress_tracking.resume_score.current or None,
            job_match_score=plan.progress_tracking.job_match_score.current or None,
            interview_score=plan.progress_tracking.interview_score.current or None,
            skills_score=plan.progress_tracking.skills_score.current or None,
        )

    # Return freshly generated plan with new snapshot history
    return generate_career_improvement_plan(
        db=db, user_id=user_id, create_snapshot_if_none=False
    )


@router.post(
    "/actions/{task_id}/toggle",
    summary="Toggle completion status of an action plan task",
)
def toggle_action_item(
    task_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Persist the toggled completion state of a personalized action item."""
    user_id = current_user["user_id"]
    get_or_create_user(db, user_id, current_user.get("email"))

    return toggle_user_action_item(db=db, user_id=user_id, task_id=task_id)
