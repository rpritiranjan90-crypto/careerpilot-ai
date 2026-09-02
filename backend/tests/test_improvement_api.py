"""Tests for the Career Improvement Engine API."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.models import (
    CareerReadinessSnapshot,
    JobDescription,
    JobMatch,
    Resume,
    ResumeAnalysis,
    User,
    UserActionItem,
)
from app.security.auth import get_or_create_user


def test_get_improvement_plan_unauthenticated(anon_client: TestClient) -> None:
    """Unauthenticated requests without header must be rejected with 401."""
    response = anon_client.get("/api/improvement-plan")
    assert response.status_code == 401


def test_get_improvement_plan_empty_user(anon_client: TestClient, db_session) -> None:
    """New user with no uploaded data should receive a clean onboarding plan."""
    user_id = "new-empty-user-123"
    get_or_create_user(db_session, user_id, "empty@example.com")

    headers = {"Authorization": f"Bearer {user_id}"}
    response = anon_client.get("/api/improvement-plan", headers=headers)
    assert response.status_code == 200
    data = response.json()

    assert data["has_data"] is False
    assert data["data_completeness"] == "no_data"
    assert data["overall_score"] == 0
    assert data["next_best_action"]["cta_link"] == "/resume"
    assert data["progress_tracking"]["has_history"] is False
    assert data["progress_tracking"]["overall_readiness"]["previous"] is None


def test_get_improvement_plan_resume_only(anon_client: TestClient, db_session) -> None:
    """User with a resume gets resume enhancements, action items, and baseline snapshot."""
    user_id = "user-with-resume-456"
    get_or_create_user(db_session, user_id, "resume_user@example.com")

    resume = Resume(
        id="resume-uuid-1",
        user_id=user_id,
        filename="engineer_resume.pdf",
        storage_path="engineer_resume.pdf",
        file_size=2048,
    )
    db_session.add(resume)
    db_session.commit()

    analysis = ResumeAnalysis(
        id="analysis-uuid-1",
        resume_id="resume-uuid-1",
        score=72,
        result_json={
            "score": 72,
            "summary": "Good technical baseline with gaps in measurable impact.",
            "skills": [{"name": "Python"}, {"name": "SQL"}],
            "strengths": ["Strong core syntax"],
            "weaknesses": ["Lacks quantified metrics"],
            "recommendations": ["Add percentages to achievements"],
        },
        summary="Good technical baseline",
    )
    db_session.add(analysis)
    db_session.commit()

    headers = {"Authorization": f"Bearer {user_id}"}
    response = anon_client.get("/api/improvement-plan", headers=headers)
    assert response.status_code == 200
    data = response.json()

    assert data["has_data"] is True
    assert data["data_completeness"] == "resume_only"
    assert len(data["resume_enhancements"]) >= 2
    assert data["resume_enhancements"][0]["is_placeholder_example"] is True
    assert len(data["action_plan"]["today"]) >= 1
    assert len(data["action_plan"]["this_week"]) >= 1


def test_toggle_action_item_persistence(anon_client: TestClient, db_session) -> None:
    """Toggling an action item persists completion state in the database."""
    user_id = "user-action-toggle-789"
    get_or_create_user(db_session, user_id, "toggle@example.com")
    headers = {"Authorization": f"Bearer {user_id}"}

    # Initial toggle -> Completed True
    res1 = anon_client.post(
        "/api/improvement-plan/actions/action_rewrite_summary/toggle",
        headers=headers,
    )
    assert res1.status_code == 200
    data1 = res1.json()
    assert data1["task_id"] == "action_rewrite_summary"
    assert data1["is_completed"] is True
    assert data1["completed_at"] is not None

    # Fetch plan -> verifies item is marked completed
    plan_res = anon_client.get("/api/improvement-plan", headers=headers)
    assert plan_res.status_code == 200
    plan_data = plan_res.json()
    today_items = plan_data["action_plan"]["today"]
    matching = [i for i in today_items if i["task_id"] == "action_rewrite_summary"]
    assert len(matching) == 1
    assert matching[0]["is_completed"] is True

    # Second toggle -> Completed False
    res2 = anon_client.post(
        "/api/improvement-plan/actions/action_rewrite_summary/toggle",
        headers=headers,
    )
    assert res2.status_code == 200
    assert res2.json()["is_completed"] is False


def test_refresh_and_real_historical_snapshot(anon_client: TestClient, db_session) -> None:
    """Historical scores are only shown when verified past snapshots exist."""
    user_id = "user-snapshots-history-999"
    get_or_create_user(db_session, user_id, "history_user@example.com")

    # Add verified previous snapshot
    snap1 = CareerReadinessSnapshot(
        id="snap-1",
        user_id=user_id,
        overall_score=60,
        resume_score=55,
        job_match_score=65,
        interview_score=60,
        skills_score=50,
    )
    db_session.add(snap1)

    # Add improved resume
    resume = Resume(
        id="resume-uuid-improved",
        user_id=user_id,
        filename="improved.pdf",
        storage_path="improved.pdf",
        file_size=3000,
    )
    db_session.add(resume)
    db_session.commit()

    analysis = ResumeAnalysis(
        id="analysis-uuid-improved",
        resume_id="resume-uuid-improved",
        score=85,
        result_json={"score": 85, "skills": [{"name": "Python"}, {"name": "Docker"}]},
    )
    db_session.add(analysis)
    db_session.commit()

    headers = {"Authorization": f"Bearer {user_id}"}

    # Refresh plan
    res = anon_client.post("/api/improvement-plan/refresh", headers=headers)
    assert res.status_code == 200
    data = res.json()

    # Verified historical progression
    assert data["progress_tracking"]["has_history"] is True
    assert data["progress_tracking"]["overall_readiness"]["previous"] == 60
    assert data["progress_tracking"]["overall_readiness"]["delta"] is not None
    assert data["progress_tracking"]["resume_score"]["previous"] == 55
    assert data["progress_tracking"]["resume_score"]["current"] == 85
    assert data["progress_tracking"]["resume_score"]["delta"] == 30
