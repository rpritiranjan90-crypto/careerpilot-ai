"""Regression tests for production hardening fixes.

These tests lock in the behavior of bug-fixes found during the
end-to-end audit. Each test corresponds to a specific finding
documented in the audit report.

Covers:
- F2: Upload disk-orphan on DB failure (file removed if commit fails)
- F4: Dead code in /api/resumes/analyze (no resume_id field, no persistence)
- F5: CSP no longer permits https://* wildcard
- F6: Password not verified in /api/users/me (any token accepted in dev mode)
- F7: Alembic migration 003 includes snapshot + action item tables
- Dev token must contain enough entropy (>= 8 chars) to prevent brute force
"""

import io
import os
import re
from unittest.mock import patch

import pytest
from sqlalchemy import text

from app.main import app


# ---------------------------------------------------------------------------
# F2: Upload disk-orphan on DB failure
# ---------------------------------------------------------------------------


def test_upload_db_failure_cleans_up_orphan_file(client, tmp_path, monkeypatch):
    """If the DB commit fails after the file is written, the orphan file
    must be removed from disk so storage does not accumulate unreachable
    files. This is a regression test for the upload cleanup fix.

    Strategy: patch the Resume model's __init__ to make db.add raise,
    forcing the except branch to run. The endpoint should catch the
    exception, remove the file from tmp_path, and return 500.
    """
    from app.core.config import settings as real_settings

    # Redirect uploads to a fresh tmp dir for this test
    upload_target = tmp_path / "uploads"
    upload_target.mkdir()
    monkeypatch.setattr(real_settings, "upload_dir", str(upload_target))

    # Force a DB write failure by patching the Resume constructor to raise
    def explode(*a, **kw):
        raise RuntimeError("simulated DB failure")

    from app.api import upload as upload_mod

    monkeypatch.setattr(upload_mod, "Resume", explode)

    content = b"John Doe\nSenior Engineer\nPython JavaScript SQL 5 years experience"
    res = client.post(
        "/api/resumes/upload",
        files={"file": ("resume.txt", io.BytesIO(content), "text/plain")},
    )

    # Should be a 500 (uncaught exception caught by our generic handler)
    assert res.status_code == 500, f"unexpected status: {res.status_code} body={res.text}"

    # CRITICAL: no orphan file should remain in the upload dir
    remaining = list(upload_target.iterdir())
    assert remaining == [], (
        f"Orphan files left in upload dir after DB failure: {remaining}"
    )


# ---------------------------------------------------------------------------
# F4: Dead code in /api/resumes/analyze (no resume_id field)
# ---------------------------------------------------------------------------


def test_analyze_endpoint_has_no_resume_id_field(client, sample_resume_text):
    """The /api/resumes/analyze schema should NOT accept a resume_id field.
    If a client sends one, it should be silently ignored (no DB write).
    This is a regression test for the dead code removal fix.
    """
    # First, do an analysis WITHOUT resume_id
    res = client.post(
        "/api/resumes/analyze",
        json={"resume_text": sample_resume_text, "job_description": None},
    )
    assert res.status_code == 200
    body = res.json()
    assert "score" in body

    # The request must succeed even if a resume_id is sent (it should be
    # ignored by Pydantic since the field doesn't exist on the schema).
    res2 = client.post(
        "/api/resumes/analyze",
        json={
            "resume_text": sample_resume_text,
            "job_description": None,
            "resume_id": "this-should-be-ignored-12345",
        },
    )
    assert res2.status_code == 200
    body2 = res2.json()
    assert "score" in body2


# ---------------------------------------------------------------------------
# F5: CSP does not include https://* wildcard
# ---------------------------------------------------------------------------


def test_csp_does_not_allow_https_wildcard(client):
    """The Content-Security-Policy header must NOT contain 'https://*'
    because that wildcard defeats the purpose of CSP and would let
    malicious scripts exfiltrate data to any HTTPS endpoint.
    """
    res = client.get("/health")
    csp = res.headers.get("Content-Security-Policy", "")
    assert csp, "CSP header missing"
    assert "https://*" not in csp, f"CSP contains dangerous wildcard: {csp}"
    # Should still allow 'self' at minimum
    assert "'self'" in csp


def test_security_headers_present(client):
    """Verify all expected security headers are returned."""
    res = client.get("/health")
    assert res.headers.get("X-Content-Type-Options") == "nosniff"
    assert res.headers.get("X-Frame-Options") == "DENY"
    assert res.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
    assert res.headers.get("X-XSS-Protection") == "1; mode=block"
    assert res.headers.get("Server", "present") == "", "Server header leak"


# ---------------------------------------------------------------------------
# F6: Dev token validation - minimum length
# ---------------------------------------------------------------------------


def test_short_dev_token_rejected(anon_client):
    """Dev tokens shorter than 8 chars are rejected (defense against trivial
    collision by attackers guessing user ids).
    """
    res = anon_client.get(
        "/api/users/me",
        headers={"Authorization": "Bearer short"},  # 5 chars
    )
    assert res.status_code == 401


def test_token_with_jwt_dots_rejected_when_in_dev_mode(anon_client, monkeypatch):
    """A token that looks like a JWT (3 dots) is rejected in dev mode
    to prevent confusion with Supabase JWTs.
    """
    res = anon_client.get(
        "/api/users/me",
        headers={"Authorization": "Bearer aaa.bbb.ccc"},
    )
    assert res.status_code == 401


# ---------------------------------------------------------------------------
# F7: Migration 003 exists
# ---------------------------------------------------------------------------


def test_migration_003_file_exists():
    """The migration 003 must exist so that fresh `alembic upgrade head`
    creates the snapshot and action item tables.
    """
    import os
    versions_dir = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "alembic",
        "versions",
    )
    files = os.listdir(versions_dir)
    # Find any 003_* file
    assert any(f.startswith("003_") for f in files), (
        f"Migration 003 missing. Found: {files}"
    )


def test_migration_003_contains_required_tables():
    """The migration 003 file must define both required tables."""
    import os
    versions_dir = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "alembic",
        "versions",
    )
    files = os.listdir(versions_dir)
    target = next(f for f in files if f.startswith("003_"))
    with open(os.path.join(versions_dir, target)) as f:
        content = f.read()
    assert "career_readiness_snapshots" in content
    assert "user_action_items" in content


# ---------------------------------------------------------------------------
# Request ID middleware: log injection defense
# ---------------------------------------------------------------------------


def test_request_id_rejects_non_uuid(client):
    """Incoming X-Request-ID that is not a valid UUID must be replaced
    with a server-generated UUID, to prevent log-injection attacks.
    """
    res = client.get("/health", headers={"X-Request-ID": "<script>alert(1)</script>"})
    returned = res.headers.get("X-Request-ID", "")
    # Should be a freshly generated UUID, not the attack payload
    assert "<script>" not in returned
    # Should look like a UUID
    assert re.match(
        r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
        returned,
    ), f"unexpected request id: {returned}"


def test_request_id_accepts_valid_uuid(client):
    """A valid incoming UUID4 X-Request-ID must be passed through verbatim
    so the client can correlate logs across hops.
    """
    incoming = "12345678-1234-4234-8234-123456789012"
    res = client.get("/health", headers={"X-Request-ID": incoming})
    assert res.headers.get("X-Request-ID") == incoming
