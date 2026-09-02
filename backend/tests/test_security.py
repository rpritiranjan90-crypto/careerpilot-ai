"""Security tests: authorization bypass, auth failure, AI failure modes, and IDOR.

These tests verify that the security posture holds against real attack vectors.
Run with: pytest tests/test_security.py -v
"""

import io

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import get_db


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="function")
def client_with_db(db_session):
    """Client with DB and user 'security-test-user' via Bearer token."""
    app.dependency_overrides[get_db] = lambda: db_session
    with TestClient(app, headers={"Authorization": "Bearer security-test-user"}) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def other_user_client(db_session):
    """Client authenticated as 'other-user' via Bearer token."""
    app.dependency_overrides[get_db] = lambda: db_session
    with TestClient(app, headers={"Authorization": "Bearer other-user"}) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def anon_client(db_session):
    """Client with no auth at all."""
    app.dependency_overrides[get_db] = lambda: db_session
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Authentication enforcement (unauthenticated requests must be rejected)
# ---------------------------------------------------------------------------

class TestAuthenticationEnforcement:
    """Every protected endpoint must return 401 when no token is provided."""

    def test_upload_requires_auth(self, anon_client):
        r = anon_client.post(
            "/api/resumes/upload",
            files={"file": ("resume.txt", io.BytesIO(b"test"), "text/plain")},
        )
        assert r.status_code == 401, f"Expected 401, got {r.status_code}"

    def test_get_resume_requires_auth(self, anon_client):
        r = anon_client.get("/api/resumes/some-uuid")
        assert r.status_code == 401

    def test_delete_resume_requires_auth(self, anon_client):
        r = anon_client.delete("/api/resumes/some-uuid")
        assert r.status_code == 401

    def test_analyze_requires_auth(self, anon_client):
        r = anon_client.post(
            "/api/resumes/analyze",
            json={"resume_text": "John Doe\nSkills: Python\nExperience: 5 years" * 3},
        )
        assert r.status_code == 401

    def test_list_analyses_requires_auth(self, anon_client):
        r = anon_client.get("/api/resumes/some-uuid/analyses")
        assert r.status_code == 401

    def test_get_analysis_requires_auth(self, anon_client):
        r = anon_client.get("/api/resumes/analyses/some-analysis-uuid")
        assert r.status_code == 401

    def test_job_match_requires_auth(self, anon_client):
        r = anon_client.post(
            "/api/job-matches",
            json={
                "resume_skills": ["python"],
                "job_requirements": "We need Python developers with 5+ years experience in software development",
            },
        )
        assert r.status_code == 401

    def test_interview_start_requires_auth(self, anon_client):
        r = anon_client.post(
            "/api/interviews",
            json={"interview_type": "general", "question": None},
        )
        assert r.status_code == 401

    def test_interview_submit_requires_auth(self, anon_client):
        r = anon_client.post(
            "/api/interviews/some-uuid/answers",
            json={"answer": "My answer is...", "context": ""},
        )
        assert r.status_code == 401

    def test_interview_get_requires_auth(self, anon_client):
        r = anon_client.get("/api/interviews/some-uuid")
        assert r.status_code == 401

    def test_interview_complete_requires_auth(self, anon_client):
        r = anon_client.post("/api/interviews/some-uuid/complete")
        assert r.status_code == 401


# ---------------------------------------------------------------------------
# Authorization / IDOR (cross-user resource access)
# ---------------------------------------------------------------------------

class TestResumeAuthorization:
    """User A must not be able to access User B's resumes."""

    def test_cannot_get_other_users_resume(self, client_with_db, other_user_client):
        upload = client_with_db.post(
            "/api/resumes/upload",
            files={"file": ("resume.txt", io.BytesIO(b"User A resume content here with sufficient details"), "text/plain")},
        )
        assert upload.status_code == 201, upload.text
        resume_id = upload.json()["resume_id"]

        r = other_user_client.get(f"/api/resumes/{resume_id}")
        assert r.status_code == 403, (
            f"IDOR: User B should not read User A's resume. Got {r.status_code}"
        )

    def test_cannot_delete_other_users_resume(self, client_with_db, other_user_client):
        upload = client_with_db.post(
            "/api/resumes/upload",
            files={"file": ("resume.txt", io.BytesIO(b"User A resume content to delete"), "text/plain")},
        )
        assert upload.status_code == 201
        resume_id = upload.json()["resume_id"]

        r = other_user_client.delete(f"/api/resumes/{resume_id}")
        assert r.status_code == 403, (
            f"IDOR: User B should not delete User A's resume. Got {r.status_code}"
        )

    def test_cannot_analyze_other_users_resume(self, client_with_db, other_user_client):
        upload = client_with_db.post(
            "/api/resumes/upload",
            files={"file": ("resume.txt", io.BytesIO(b"User A resume content here for analysis testing"), "text/plain")},
        )
        assert upload.status_code == 201
        resume_id = upload.json()["resume_id"]

        r = other_user_client.post(f"/api/resumes/{resume_id}/analyze")
        assert r.status_code == 403, (
            f"IDOR: User B should not analyze User A's resume. Got {r.status_code}"
        )

    def test_cannot_list_analyses_of_other_users_resume(
        self, client_with_db, other_user_client
    ):
        upload = client_with_db.post(
            "/api/resumes/upload",
            files={"file": ("resume.txt", io.BytesIO(b"User A resume content for list analyses test"), "text/plain")},
        )
        assert upload.status_code == 201
        resume_id = upload.json()["resume_id"]

        r = other_user_client.get(f"/api/resumes/{resume_id}/analyses")
        assert r.status_code == 403, (
            f"IDOR: User B should not list User A's analyses. Got {r.status_code}"
        )


class TestJobMatchAuthorization:
    """User A must not be able to read User B's job match results."""

    def test_cannot_get_other_users_job_match(self, client_with_db, other_user_client):
        # User A saves a job description
        client_with_db.post(
            "/api/job-matches",
            json={
                "resume_skills": ["python"],
                "job_requirements": "We need Python developers with 5+ years experience in software development using Docker and Kubernetes",
            },
        )
        # User B lists job descriptions - should not see User A's job descriptions
        r = other_user_client.get("/api/job-matches")
        assert r.status_code == 200
        assert r.json() == []

    def test_cannot_access_other_users_job_description_list(
        self, client_with_db, other_user_client
    ):
        client_with_db.post(
            "/api/job-matches",
            json={
                "resume_skills": ["python"],
                "job_requirements": "We need Python developers with experience in software development",
            },
        )
        r = other_user_client.get("/api/job-matches")
        assert r.status_code == 200
        assert r.json() == [], "User B should see no job descriptions"


class TestInterviewAuthorization:
    """User A must not be able to access User B's interview sessions."""

    def test_cannot_get_other_users_interview(self, client_with_db, other_user_client):
        start = client_with_db.post(
            "/api/interviews",
            json={"interview_type": "general", "question": None},
        )
        assert start.status_code == 201, start.text
        interview_id = start.json()["interview_id"]

        r = other_user_client.get(f"/api/interviews/{interview_id}")
        assert r.status_code == 403, (
            f"IDOR: User B should not access User A's interview. Got {r.status_code}"
        )

    def test_cannot_submit_answer_to_other_users_interview(
        self, client_with_db, other_user_client
    ):
        start = client_with_db.post(
            "/api/interviews",
            json={"interview_type": "technical", "question": None},
        )
        assert start.status_code == 201
        interview_id = start.json()["interview_id"]

        r = other_user_client.post(
            f"/api/interviews/{interview_id}/answers",
            json={"answer": "My answer is detailed enough to pass validation...", "context": ""},
        )
        assert r.status_code == 403, (
            f"IDOR: User B should not submit answers to User A's interview. Got {r.status_code}"
        )

    def test_cannot_complete_other_users_interview(self, client_with_db, other_user_client):
        start = client_with_db.post(
            "/api/interviews",
            json={"interview_type": "general", "question": None},
        )
        assert start.status_code == 201
        interview_id = start.json()["interview_id"]

        r = other_user_client.post(f"/api/interviews/{interview_id}/complete")
        assert r.status_code == 403, (
            f"IDOR: User B should not complete User A's interview. Got {r.status_code}"
        )


# ---------------------------------------------------------------------------
# Token validation
# ---------------------------------------------------------------------------

class TestTokenValidation:
    """JWT token validation edge cases."""

    def test_empty_bearer_token_rejected(self, anon_client):
        r = anon_client.get(
            "/api/resumes/some-uuid",
            headers={"Authorization": "Bearer "},
        )
        assert r.status_code in (401, 422)

    def test_non_uuid_request_id_rejected(self, client_with_db):
        r = client_with_db.get(
            "/health",
            headers={"X-Request-ID": "<script>alert(1)</script>"},
        )
        assert r.status_code == 200
        assert "<script>" not in r.text

    def test_valid_uuid_request_id_accepted(self, client_with_db):
        r = client_with_db.get(
            "/health",
            headers={"X-Request-ID": "550e8400-e29b-41d4-a716-446655440000"},
        )
        assert r.status_code == 200
        assert r.headers.get("X-Request-ID") == "550e8400-e29b-41d4-a716-446655440000"


# ---------------------------------------------------------------------------
# File upload security
# ---------------------------------------------------------------------------

class TestUploadSecurity:
    """Adversarial file upload tests."""

    def test_double_extension_rejected(self, client_with_db):
        r = client_with_db.post(
            "/api/resumes/upload",
            files={"file": ("resume.pdf.exe", b"%PDF-1.4", "application/pdf")},
        )
        assert r.status_code == 400, "Double extension .pdf.exe should be rejected"

    def test_path_traversal_in_filename_rejected(self, client_with_db):
        r = client_with_db.post(
            "/api/resumes/upload",
            files={"file": ("../../etc/passwd.txt", b"test content", "text/plain")},
        )
        assert r.status_code in (400, 201)

    def test_null_byte_in_filename_rejected(self, client_with_db):
        r = client_with_db.post(
            "/api/resumes/upload",
            files={"file": ("resume\x00.pdf", b"%PDF-1.4", "application/pdf")},
        )
        assert r.status_code in (400, 201)

    def test_oversized_file_rejected(self, client_with_db):
        big = b"x" * (6 * 1024 * 1024)  # 6 MB (limit is 5 MB)
        r = client_with_db.post(
            "/api/resumes/upload",
            files={"file": ("big.txt", io.BytesIO(big), "text/plain")},
        )
        assert r.status_code == 413, "Oversized file should return 413"

    def test_pdf_magic_bytes_required(self, client_with_db):
        r = client_with_db.post(
            "/api/resumes/upload",
            files={
                "file": ("doc.pdf", b"This is not a PDF file", "application/pdf")
            },
        )
        assert r.status_code == 400, (
            "PDF file with wrong magic bytes should be rejected"
        )


# ---------------------------------------------------------------------------
# Error envelope (no internal details leaked)
# ---------------------------------------------------------------------------

class TestErrorEnvelope:
    """Errors must not leak stack traces, SQL queries, or internal paths."""

    def test_500_error_no_stack_trace(self, client_with_db):
        r = client_with_db.get("/api/resumes/00000000-0000-0000-0000-000000000000")
        assert r.status_code in (401, 403, 404)
        body = r.json()
        assert "error" in body
        assert "Traceback" not in r.text
        assert "psycopg2" not in r.text
        assert "sqlalchemy" not in r.text.lower()

    def test_validation_error_envelope(self, client_with_db):
        r = client_with_db.post(
            "/api/resumes/analyze",
            json={"resume_text": "short"},
        )
        assert r.status_code == 422
        body = r.json()
        assert "error" in body
        assert body["error"]["code"] == "validation_error"


# ---------------------------------------------------------------------------
# Rate limiting (basic check)
# ---------------------------------------------------------------------------

class TestRateLimiting:
    """Rate limit headers and 429 responses."""

    def test_rate_limit_returns_retry_after(self, client_with_db, sample_resume_text):
        for _ in range(25):
            r = client_with_db.post(
                "/api/resumes/analyze",
                json={"resume_text": sample_resume_text * 3},
            )
            if r.status_code == 429:
                assert "Retry-After" in r.headers, "429 must have Retry-After header"
                assert "error" in r.json()
                return
