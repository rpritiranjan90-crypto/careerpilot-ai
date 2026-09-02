"""Authentication helpers using Supabase JWTs.

Supabase signs its access tokens with HS256 using the project's JWT secret
(set in the Supabase dashboard under Project Settings → API → JWT Secret).
The secret is verified on every request via the Authorization: Bearer header.

In production:
  - SUPABASE_JWT_SECRET must be set
  - DEV_TOKEN_AUTH must be False (default)

In development, if SUPABASE_JWT_SECRET is not set and DEV_TOKEN_AUTH is True,
the server accepts "Bearer <user_id>" tokens. This is for local testing only.
"""

from __future__ import annotations

import logging
from typing import Any

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import User

logger = logging.getLogger("app.auth")

security = HTTPBearer(auto_error=False)


def _decode_supabase_jwt(token: str) -> dict[str, Any]:
    """Verify a Supabase JWT and return its claims.

    Supabase tokens are HS256-signed with the project's JWT secret.
    Claims verified:
      - signature (HS256 with supabase_jwt_secret)
      - exp (expiration)
      - sub (user id; required)
    """
    if not settings.supabase_jwt_secret:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server auth is not configured (SUPABASE_JWT_SECRET missing)",
        )

    try:
        claims = jwt.decode(
            token,
            settings.supabase_jwt_secret,
            algorithms=["HS256"],
            audience="authenticated",
            options={
                "require": ["exp", "sub", "aud"],
                "verify_exp": True,
                "verify_aud": True,
            },
        )
        # Supabase iss is always https://<project>.supabase.co
        if settings.supabase_url:
            expected_iss = settings.supabase_url.rstrip("/")
            actual_iss = claims.get("iss", "").rstrip("/")
            if expected_iss and actual_iss and actual_iss != expected_iss:
                raise jwt.InvalidTokenError("Unexpected issuer claim")
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    except jwt.InvalidTokenError as exc:
        logger.info("Invalid JWT: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    return claims


def _decode_dev_token(token: str) -> dict[str, Any]:
    """Development fallback: accept "Bearer <user_id>".

    Only enabled when settings.dev_token_auth is True. This is for local
    testing without a real Supabase project.
    """
    return {
        "sub": token,
        "email": f"{token}@dev.local",
        "dev_mode": True,
    }


def verify_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),  # noqa: B008
) -> dict[str, Any]:
    """Verify the Authorization header and return user claims.

    Returns a dict with at minimum:
      - user_id: the Supabase user id (sub claim)
      - email: the user's email (if present in token)
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    if not token or len(token) < 8:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
        )

    if settings.supabase_jwt_secret:
        claims = _decode_supabase_jwt(token)
    elif settings.dev_token_auth:
        if token.count(".") == 2:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        claims = _decode_dev_token(token)
    else:
        # No JWT secret + dev mode disabled → reject all auth
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server auth is not configured",
        )

    user_id = claims.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing required claim: sub",
        )

    return {
        "user_id": user_id,
        "email": claims.get("email"),
        "claims": claims,
    }


async def get_current_user(user: dict = Depends(verify_user)) -> dict[str, Any]:  # noqa: B008
    """FastAPI dependency: returns the authenticated user dict."""
    return user


def get_or_create_user(db: Session, user_id: str, email: str | None = None) -> User:
    """Look up the user by id; create if missing. Idempotent and collision-safe."""
    user = db.query(User).filter(User.id == user_id).first()
    if user is not None:
        if email and user.email != email:
            existing = db.query(User).filter(User.email == email, User.id != user_id).first()
            if not existing:
                user.email = email
                db.commit()
                db.refresh(user)
        return user

    target_email = email or f"{user_id}@unknown.local"
    existing_by_email = db.query(User).filter(User.email == target_email).first()
    if existing_by_email is not None:
        return existing_by_email

    user = User(
        id=user_id,
        email=target_email,
        name=None,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
