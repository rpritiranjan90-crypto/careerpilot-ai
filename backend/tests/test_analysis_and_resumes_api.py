"""Resume and Analysis CRUD and IDOR unit tests.

Verifies:
- GET /api/resumes lists user's resumes
- GET /api/resumes/{resume_id} returns resume metadata
- GET /api/resumes/{resume_id} rejects unauthorized users (403/404)
- DELETE /api/resumes/{resume_id} deletes resume from DB and unlinks file from disk
- DELETE /api/resumes/{resume_id} rejects unauthorized deletion attempts (403/404)
- GET /api/resumes/{resume_id}/analyses lists analyses for resume
- GET /api/resumes/analyses/{analysis_id} returns specific analysis with IDOR ownership check
"""

import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.core.config import settings
from app.main import app
from app.models import Resume, ResumeAnalysis
from app.security.auth import get_or_create_user


@pytest.fixture
def user_a():
    uid = str(uuid.uuid4())
    client = TestClient(app)
    client.headers["Authorization"] = f"Bearer {uid}"
    client.user_id = uid
    return client


@pytest.fixture
def user_b():
    uid = str(uuid.uuid4())
    client = TestClient(app)
    client.headers["Authorization"] = f"Bearer {uid}"
    client.user_id = uid
    return client


def test_resume_crud_and_idor(user_a, user_b, db_session: Session, tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "upload_dir", str(tmp_path))
    get_or_create_user(db_session, user_a.user_id, "usera@example.com")
    get_or_create_user(db_session, user_b.user_id, "userb@example.com")

    # Create a resume for User A
    file_name = f"{uuid.uuid4().hex}.pdf"
    file_path = tmp_path / file_name
    file_path.write_text("dummy resume content")

    resume_a = Resume(
        id=file_name,
        user_id=user_a.user_id,
        filename="user_a_resume.pdf",
        storage_path=file_name,
        file_size=128,
        mime_type="application/pdf",
        extracted_text="Python FastAPI Engineer",
    )
    db_session.add(resume_a)
    db_session.commit()

    # User A lists resumes
    resp = user_a.get("/api/resumes")
    assert resp.status_code == 200
    resumes = resp.json()
    assert len(resumes) >= 1
    assert any(r["id"] == file_name for r in resumes)

    # User A reads resume
    resp = user_a.get(f"/api/resumes/{file_name}")
    assert resp.status_code == 200
    assert resp.json()["filename"] == "user_a_resume.pdf"

    # User B attempts to read User A's resume (IDOR)
    resp = user_b.get(f"/api/resumes/{file_name}")
    assert resp.status_code in (403, 404)

    # User B attempts to delete User A's resume (IDOR)
    resp = user_b.delete(f"/api/resumes/{file_name}")
    assert resp.status_code in (403, 404)

    # User A deletes resume
    resp = user_a.delete(f"/api/resumes/{file_name}")
    assert resp.status_code == 204
    assert not file_path.exists()
    assert db_session.query(Resume).filter(Resume.id == file_name).first() is None


def test_analysis_listing_and_idor(user_a, user_b, db_session: Session):
    get_or_create_user(db_session, user_a.user_id, "usera@example.com")
    get_or_create_user(db_session, user_b.user_id, "userb@example.com")

    resume = Resume(
        id=f"{uuid.uuid4().hex}.pdf",
        user_id=user_a.user_id,
        filename="resume.pdf",
        storage_path="resume.pdf",
        file_size=128,
    )
    db_session.add(resume)
    db_session.flush()

    analysis_id = str(uuid.uuid4())
    analysis = ResumeAnalysis(
        id=analysis_id,
        resume_id=resume.id,
        score=88,
        summary="Good resume",
        result_json={
            "score": 88,
            "skills": [
                {"name": "Python", "category": "technical", "confidence": 0.95},
                {"name": "FastAPI", "category": "framework", "confidence": 0.9},
            ],
            "strengths": ["FastAPI backend experience"],
            "weaknesses": ["None"],
            "recommendations": ["Great profile"],
            "summary": "Good resume",
        },
    )
    db_session.add(analysis)
    db_session.commit()

    # User A lists analyses for resume
    resp = user_a.get(f"/api/resumes/{resume.id}/analyses")
    assert resp.status_code == 200
    analyses = resp.json()
    assert len(analyses) == 1
    assert analyses[0]["score"] == 88

    # User B attempts to list analyses for User A's resume (IDOR)
    resp = user_b.get(f"/api/resumes/{resume.id}/analyses")
    assert resp.status_code in (403, 404)

    # User A gets specific analysis
    resp = user_a.get(f"/api/resumes/analyses/{analysis_id}")
    assert resp.status_code == 200
    assert resp.json()["score"] == 88

    # User B attempts to get specific analysis of User A (IDOR)
    resp = user_b.get(f"/api/resumes/analyses/{analysis_id}")
    assert resp.status_code in (403, 404)
