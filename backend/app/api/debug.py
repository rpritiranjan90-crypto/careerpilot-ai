"""Debug endpoints — for verifying integrations in production.

These are safe to leave in production but only trigger when explicitly hit.
"""

from fastapi import APIRouter, HTTPException

router = APIRouter(tags=["debug"])


@router.get("/debug/error")
async def trigger_error() -> dict:
    """Trigger a test error to verify Sentry integration.

    Returns:
        Always raises an HTTPException 500.

    Example:
        curl https://careerpilot-api-q5ur.onrender.com/api/debug/error
    """
    raise HTTPException(status_code=500, detail="Test error from /api/debug/error")


@router.get("/debug/ok")
async def ok() -> dict:
    """Confirm the debug endpoints are reachable.

    Returns:
        A simple ok message.
    """
    return {"status": "ok", "message": "Debug endpoints are live"}
