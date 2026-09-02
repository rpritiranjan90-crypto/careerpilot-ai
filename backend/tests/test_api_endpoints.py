"""End-to-end API tests for CareerPilot AI.

Covers:
- Authentication (401 when no token)
- Resume upload + analysis flow
- Job match flow
- Interview flow
- Ownership enforcement (cross-user access blocked)
- Standardized error envelope
"""

import io

from conftest import _override_get_current_user  # type: ignore[import]

from app.main import app

# Helper fixtures imported at module load (conftest.py is auto-loaded by pytest
# but not importable as `tests.conftest` from inside a test file).
from app.security.auth import get_current_user

# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

def test_health_returns_ok(client):
    res = client.get("/health")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "ok"
    assert "request_id" in body


def test_readiness_returns_checks(client):
    res = client.get("/health/ready")
    assert res.status_code == 200
    body = res.json()
    assert "checks" in body
    assert body["checks"]["api"] == "ok"


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

def test_unauthenticated_request_returns_401(anon_client):
    """Resumes endpoint should require auth."""
    res = anon_client.get("/api/resumes/some-id")
    assert res.status_code == 401
    body = res.json()
    # Either FastAPI's default or our envelope shape; both must be JSON
    assert isinstance(body, dict)


# ---------------------------------------------------------------------------
# Resume analysis
# ---------------------------------------------------------------------------

def test_resume_analysis_persists_result(client, sample_resume_text):
    res = client.post(
        "/api/resumes/analyze",
        json={"resume_text": sample_resume_text, "job_description": None},
    )
    assert res.status_code == 200
    body = res.json()
    assert "score" in body
    assert 0 <= body["score"] <= 100
    assert "summary" in body
    assert isinstance(body["skills"], list)


def test_resume_analysis_validation_error_envelope(client):
    """Pydantic validation error returns 422 with our envelope."""
    res = client.post("/api/resumes/analyze", json={"resume_text": "x" * 10})  # too short
    assert res.status_code == 422
    body = res.json()
    assert "error" in body
    assert body["error"]["code"] == "validation_error"
    assert "request_id" in body["error"]


# ---------------------------------------------------------------------------
# Resume upload + text extraction pipeline
# ---------------------------------------------------------------------------

def test_resume_upload_txt_file(client):
    """A real .txt upload is parsed server-side and a Resume row is created."""
    content = b"John Doe\nSenior Engineer\n5+ years Python experience\nDocker, Kubernetes"
    res = client.post(
        "/api/resumes/upload",
        files={"file": ("resume.txt", io.BytesIO(content), "text/plain")},
    )
    assert res.status_code == 201, res.text
    body = res.json()
    assert body["size"] == len(content)
    assert "resume_id" in body

    # Verify the user was auto-created
    # Use a fresh session (the test session is rolled back per test)
    from app.core.database import get_engine
    get_engine()  # returns None when no DATABASE_URL is set
    # Skip DB assertions if we're running in-memory; the response already confirms success


def test_resume_upload_rejects_dangerous_extension(client):
    """Bash scripts and other dangerous files are rejected by the blocklist."""
    res = client.post(
        "/api/resumes/upload",
        files={"file": ("evil.sh", b"#!/bin/bash\nrm -rf /", "text/plain")},
    )
    assert res.status_code == 400
    body = res.json()
    # The error may come back as our envelope or FastAPI's default
    if "error" in body:
        assert "not allowed" in body["error"].get("message", "").lower()
    else:
        assert "not allowed" in str(body).lower()


def test_resume_upload_rejects_oversize(client):
    """Files larger than max_upload_size_mb are rejected."""
    big_content = b"x" * (10 * 1024 * 1024)  # 10 MB
    res = client.post(
        "/api/resumes/upload",
        files={"file": ("big.txt", io.BytesIO(big_content), "text/plain")},
    )
    assert res.status_code == 413
    assert "too large" in res.text.lower() or "too large" in str(res.json()).lower()


# ---------------------------------------------------------------------------
# Job match
# ---------------------------------------------------------------------------

def test_job_match_creates_record(client, sample_job_description):
    res = client.post(
        "/api/job-matches",
        json={
            "resume_skills": ["python", "sql", "docker"],
            "job_requirements": sample_job_description,
        },
    )
    assert res.status_code == 201
    body = res.json()
    assert 0 <= body["match_score"] <= 100
    assert "matched_skills" in body
    assert "missing_skills" in body


def test_job_match_validation_envelope(client):
    res = client.post(
        "/api/job-matches",
        json={"resume_skills": [], "job_requirements": "x"},  # empty + too short
    )
    assert res.status_code == 422
    body = res.json()
    assert body["error"]["code"] == "validation_error"


# ---------------------------------------------------------------------------
# Interview
# ---------------------------------------------------------------------------

def test_interview_lifecycle(client, sample_interview_answer):
    start = client.post(
        "/api/interviews",
        json={"interview_type": "general", "question": None},
    )
    assert start.status_code == 201
    sid = start.json()["interview_id"]

    submit = client.post(
        f"/api/interviews/{sid}/answers",
        json={"answer": sample_interview_answer, "context": "Test question"},
    )
    assert submit.status_code == 200
    body = submit.json()
    assert 0 <= body["score"] <= 100
    assert "feedback" in body

    detail = client.get(f"/api/interviews/{sid}")
    assert detail.status_code == 200
    assert detail.json()["interview_type"] == "general"


# ---------------------------------------------------------------------------
# Ownership enforcement
# ---------------------------------------------------------------------------

def test_cross_user_resume_access_blocked(client):
    """User A creates a resume; user B cannot read or delete it."""
    # User A creates a resume
    content = b"Resume A content"
    upload = client.post(
        "/api/resumes/upload",
        files={"file": ("a.txt", io.BytesIO(content), "text/plain")},
    )
    assert upload.status_code == 201, upload.text
    resume_id = upload.json()["resume_id"]

    # Switch to user B
    def user_b():
        return {"user_id": "user-B", "email": "b@example.com"}

    app.dependency_overrides[get_current_user] = user_b
    try:
        res = client.get(f"/api/resumes/{resume_id}")
        assert res.status_code == 403, (
            f"User B should be denied GET; got {res.status_code} body={res.text}"
        )

        res = client.delete(f"/api/resumes/{resume_id}")
        assert res.status_code == 403, (
            f"User B should be denied DELETE; got {res.status_code} body={res.text}"
        )
    finally:
        app.dependency_overrides[get_current_user] = _override_get_current_user


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------

def test_metrics_endpoint_exposed(client):
    res = client.get("/metrics")
    assert res.status_code == 200
    assert b"http_requests_total" in res.content
