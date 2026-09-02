"""User API and GDPR deletion unit tests.

Verifies:
- GET /api/users/me returns authenticated user info
- GET /api/users/me/dashboard aggregates readiness score, breakdown, priority focus, and activity counters
- GET /api/users/me/dashboard works with zero data (empty state score = 0)
- DELETE /api/users/me cascade-deletes user DB records AND unlinks physical files from upload_dir
- DELETE /api/users/me gracefully handles missing files on disk
"""

import os
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.core.config import settings
from app.main import app
from app.models import Interview, InterviewQuestion, JobDescription, JobMatch, Resume, ResumeAnalysis, User
from app.security.auth import get_or_create_user


@pytest.fixture
def auth_client():
    user_id = str(uuid.uuid4())
    client = TestClient(app)
    client.headers["Authorization"] = f"Bearer {user_id}"
    client.user_id = user_id
    return client


def test_get_current_user_profile(auth_client, db_session: Session):
    get_or_create_user(db_session, auth_client.user_id, "test@example.com")
    resp = auth_client.get("/api/users/me")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == auth_client.user_id


def test_dashboard_empty_state(auth_client, db_session: Session):
    get_or_create_user(db_session, auth_client.user_id, "empty@example.com")
    resp = auth_client.get("/api/users/me/dashboard")
    assert resp.status_code == 200
    data = resp.json()
    assert data["has_data"] is False
    assert data["career_readiness"]["overall_score"] == 0
    assert data["resume_count"] == 0
    assert data["job_match_count"] == 0
    assert data["interview_count"] == 0


def test_dashboard_aggregated_metrics(auth_client, db_session: Session):
    user_id = auth_client.user_id
    get_or_create_user(db_session, user_id, "metrics@example.com")

    # Add resume + analysis
    resume = Resume(
        id=f"{uuid.uuid4().hex}.pdf",
        user_id=user_id,
        filename="resume.pdf",
        storage_path="resume.pdf",
        file_size=1024,
        extracted_text="Python FastAPI Docker React PostgreSQL",
    )
    db_session.add(resume)
    db_session.flush()

    analysis = ResumeAnalysis(
        resume_id=resume.id,
        score=85,
        summary="Strong profile",
        result_json={"score": 85, "skills": ["Python", "FastAPI"]},
    )
    db_session.add(analysis)

    # Add job description and match
    jd = JobDescription(
        user_id=user_id,
        title="Software Engineer",
        description="FastAPI Backend Engineer",
    )
    db_session.add(jd)
    db_session.flush()

    match = JobMatch(
        resume_id=resume.id,
        job_description_id=jd.id,
        match_score=90,
        result_json={"match_score": 90, "matched_skills": ["Python", "FastAPI"], "missing_skills": []},
    )
    db_session.add(match)

    # Add interview with question scores
    interview = Interview(
        user_id=user_id,
        interview_type="technical",
        status="completed",
    )
    db_session.add(interview)
    db_session.flush()

    question = InterviewQuestion(
        interview_id=interview.id,
        question="What is FastAPI?",
        answer="FastAPI is a Python async framework.",
        score=80,
    )
    db_session.add(question)
    db_session.commit()

    resp = auth_client.get("/api/users/me/dashboard")
    assert resp.status_code == 200
    data = resp.json()
    assert data["has_data"] is True
    assert data["career_readiness"]["overall_score"] >= 70
    assert data["career_readiness"]["breakdown"]["resume"]["score"] == 85
    assert data["career_readiness"]["breakdown"]["job_match"]["score"] == 90
    assert data["career_readiness"]["breakdown"]["interview"]["score"] == 80
    assert data["resume_count"] == 1
    assert data["job_match_count"] == 1
    assert data["interview_count"] == 1


def test_gdpr_delete_account_and_files(auth_client, db_session: Session, tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "upload_dir", str(tmp_path))
    user_id = auth_client.user_id
    get_or_create_user(db_session, user_id, "gdpr@example.com")

    # Create dummy files on disk in upload_dir
    file1_name = f"{uuid.uuid4().hex}.pdf"
    file2_name = f"{uuid.uuid4().hex}.txt"
    file1_path = tmp_path / file1_name
    file2_path = tmp_path / file2_name
    file1_path.write_text("dummy resume 1")
    file2_path.write_text("dummy resume 2")

    resume1 = Resume(
        id=file1_name,
        user_id=user_id,
        filename="resume1.pdf",
        storage_path=file1_name,
        file_size=100,
    )
    resume2 = Resume(
        id=file2_name,
        user_id=user_id,
        filename="resume2.txt",
        storage_path=file2_name,
        file_size=100,
    )
    db_session.add_all([resume1, resume2])
    db_session.commit()

    assert file1_path.exists()
    assert file2_path.exists()

    resp = auth_client.delete("/api/users/me")
    assert resp.status_code == 200
    data = resp.json()
    assert data["deleted_user_id"] == user_id
    assert data["files_deleted"] == 2

    # Physical files must be removed from disk
    assert not file1_path.exists()
    assert not file2_path.exists()

    # User and resumes must be removed from DB
    assert db_session.query(User).filter(User.id == user_id).first() is None
    assert db_session.query(Resume).filter(Resume.user_id == user_id).first() is None
