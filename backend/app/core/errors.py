"""Standardized error responses for the API.

All errors returned to clients follow this envelope:

    {
      "error": {
        "code": "RESOURCE_NOT_FOUND",
        "message": "Resource not found",
        "request_id": "uuid"
      }
    }

The exception handlers in main.py wrap raw exceptions into this shape.
For per-endpoint errors, use the helpers here so the envelope is consistent.
"""

from __future__ import annotations

from typing import Any

from fastapi import HTTPException, status

from app.core.logging import get_request_id


class APIError(HTTPException):
    """HTTPException that carries a stable error code and optional request ID for the envelope.

    Example:
        raise APIError(status.HTTP_404_NOT_FOUND, "not_found", "Resume not found")
    """

    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        request_id: str | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        self.code = code
        self.message = message
        self.request_id = request_id
        super().__init__(status_code=status_code, detail=message, headers=headers)


def not_found(resource: str = "Resource", request_id: str | None = None) -> APIError:
    return APIError(
        status.HTTP_404_NOT_FOUND,
        "not_found",
        f"{resource} not found",
        request_id=request_id,
    )


def forbidden(message: str = "Access denied", request_id: str | None = None) -> APIError:
    return APIError(
        status.HTTP_403_FORBIDDEN,
        "forbidden",
        message,
        request_id=request_id,
    )


def unauthorized(message: str = "Authentication required", request_id: str | None = None) -> APIError:
    return APIError(
        status.HTTP_401_UNAUTHORIZED,
        "unauthorized",
        message,
        request_id=request_id,
        headers={"WWW-Authenticate": "Bearer"},
    )


def bad_request(message: str = "Invalid request", request_id: str | None = None) -> APIError:
    return APIError(
        status.HTTP_400_BAD_REQUEST,
        "bad_request",
        message,
        request_id=request_id,
    )


def payload_too_large(message: str | None = None, limit_mb: int = 5, request_id: str | None = None) -> APIError:
    msg = message or f"File too large. Maximum size is {limit_mb} MB"
    return APIError(
        status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
        "payload_too_large",
        msg,
        request_id=request_id,
    )


def rate_limited(retry_after: int, request_id: str | None = None) -> APIError:
    return APIError(
        status.HTTP_429_TOO_MANY_REQUESTS,
        "rate_limited",
        f"Rate limit exceeded. Try again in {retry_after} seconds.",
        request_id=request_id,
        headers={"Retry-After": str(retry_after)},
    )


def envelope(
    error_or_code: APIError | str,
    message: str | None = None,
    details: Any = None,
    request_id: str | None = None,
) -> dict[str, Any]:
    """Build the standard error envelope body.

    Supports calling with an APIError instance: `envelope(err, request_id=...)`
    or with code and message strings: `envelope("validation_error", "Invalid payload")`.
    """
    if isinstance(error_or_code, APIError):
        code = error_or_code.code
        msg = error_or_code.message
        req_id = request_id or error_or_code.request_id or get_request_id()
    else:
        code = error_or_code
        msg = message or "An error occurred"
        req_id = request_id or get_request_id()

    body: dict[str, Any] = {
        "error": {
            "code": code,
            "message": msg,
            "request_id": req_id,
        }
    }
    if details is not None:
        body["error"]["details"] = details
    return body
