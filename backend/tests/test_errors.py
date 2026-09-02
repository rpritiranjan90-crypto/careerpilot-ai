"""Unit tests for the standardized error envelope helpers."""

from app.core.errors import (
    APIError,
    bad_request,
    envelope,
    forbidden,
    not_found,
    payload_too_large,
    rate_limited,
    unauthorized,
)


def test_api_error_carries_code_and_message():
    e = APIError(404, "not_found", "User not found")
    assert e.status_code == 404
    assert e.code == "not_found"
    assert e.message == "User not found"
    assert e.request_id is None


def test_api_error_serializes_to_envelope():
    e = APIError(401, "unauthorized", "Bad token", request_id="abc-123")
    body = envelope(e, request_id="abc-123")
    assert body == {
        "error": {
            "code": "unauthorized",
            "message": "Bad token",
            "request_id": "abc-123",
        }
    }


def test_not_found_helper():
    e = not_found("Resume")
    assert e.status_code == 404
    assert e.code == "not_found"
    assert "Resume" in e.message


def test_forbidden_helper():
    e = forbidden()
    assert e.status_code == 403
    assert e.code == "forbidden"


def test_unauthorized_helper():
    e = unauthorized()
    assert e.status_code == 401
    assert e.code == "unauthorized"


def test_bad_request_helper():
    e = bad_request("Invalid input")
    assert e.status_code == 400
    assert e.code == "bad_request"
    assert e.message == "Invalid input"


def test_payload_too_large_helper():
    e = payload_too_large(limit_mb=5)
    assert e.status_code == 413
    assert "5" in e.message


def test_rate_limited_helper():
    e = rate_limited(retry_after=42)
    assert e.status_code == 429
    assert e.code == "rate_limited"
    assert e.headers is not None
    assert e.headers.get("Retry-After") == "42"
