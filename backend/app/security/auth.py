"""Authentication helpers using Supabase JWTs.

Supabase signs access tokens with either HS256 (legacy) or ES256 (current
default for new projects). The backend supports both:
  - HS256: verified using the project's JWT secret
    (Supabase dashboard → Project Settings → API → JWT Secret)
  - ES256: verified using the public keys fetched from Supabase's
    JWKS endpoint (https://<project>.supabase.co/auth/v1/.well-known/jwks.json)

In production:
  - SUPABASE_JWT_SECRET must be set (for HS256 fallback)
  - DEV_TOKEN_AUTH must be False (default)

In development, if SUPABASE_JWT_SECRET is not set and DEV_TOKEN_AUTH is True,
the server accepts "Bearer <user_id>" tokens. This is for local testing only.
"""

from __future__ import annotations

import logging
import time
from typing import Any

import httpx
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import User

logger = logging.getLogger("app.auth")

security = HTTPBearer(auto_error=False)


# ---------------------------------------------------------------------------
# JWKS cache for ES256 verification
# ---------------------------------------------------------------------------

_jwks_cache: dict[str, Any] = {"keys": None, "fetched_at": 0.0}
_JWKS_TTL_SECONDS = 3600  # 1 hour


def _get_jwks_keys(base_url: str | None = None, force_refresh: bool = False) -> list[dict[str, Any]]:
    """Fetch Supabase JWKS keys (cached)."""
    target_url = base_url or settings.supabase_url
    if not target_url:
        return []

    clean_base = target_url.rstrip("/")
    if clean_base.endswith("/auth/v1"):
        jwks_url = f"{clean_base}/.well-known/jwks.json"
    else:
        jwks_url = f"{clean_base}/auth/v1/.well-known/jwks.json"

    now = time.monotonic()
    if (
        not force_refresh
        and _jwks_cache["keys"] is not None
        and (now - _jwks_cache["fetched_at"]) < _JWKS_TTL_SECONDS
    ):
        return _jwks_cache["keys"]

    try:
        with httpx.Client(timeout=5.0) as client:
            resp = client.get(jwks_url)
        resp.raise_for_status()
        keys = resp.json().get("keys", [])
        _jwks_cache["keys"] = keys
        _jwks_cache["fetched_at"] = now
        logger.info("Loaded %d JWKS keys from Supabase (%s)", len(keys), jwks_url)
        return keys
    except Exception as exc:
        logger.warning("Failed to fetch JWKS from %s: %s", jwks_url, exc)
        return _jwks_cache.get("keys") or []


def _decode_supabase_jwt(token: str) -> dict[str, Any]:
    """Verify a Supabase JWT and return its claims.

    Supports both HS256 (legacy, uses JWT secret) and ES256/RS256 (current default,
    uses JWKS public keys).

    Claims verified:
      - signature (HS256 with secret, or ES256 with JWKS)
      - exp (expiration)
      - aud (must be "authenticated")
      - sub (user id; required)
      - iss (must match Supabase project URL)
    """
    # Inspect the token header to determine the algorithm
    try:
        unverified_header = jwt.get_unverified_header(token)
    except jwt.InvalidTokenError as exc:
        logger.info("Could not parse JWT header: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    algorithm = unverified_header.get("alg", "HS256")
    key_id = unverified_header.get("kid")

    # Pick the key based on the algorithm
    key: Any = None
    algorithms: list[str] = []

    if algorithm == "HS256":
        if not settings.supabase_jwt_secret:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="HS256 token received but SUPABASE_JWT_SECRET is not configured",
            )
        key = settings.supabase_jwt_secret
        algorithms = ["HS256"]
    elif algorithm in ("ES256", "RS256"):
        # Auto-discover issuer from unverified claims if SUPABASE_URL is omitted
        token_iss = None
        try:
            unverified_claims = jwt.decode(token, options={"verify_signature": False})
            token_iss = unverified_claims.get("iss")
        except Exception:
            pass

        keys = _get_jwks_keys(base_url=settings.supabase_url or token_iss)
        if not keys and token_iss:
            keys = _get_jwks_keys(base_url=token_iss, force_refresh=True)

        if not keys:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not fetch JWKS keys for token verification. Please configure SUPABASE_URL in your backend environment variables.",
            )

        # Find the key by kid
        matching_jwk = None
        for k in keys:
            if k.get("kid") == key_id:
                matching_jwk = k
                break
        if matching_jwk is None:
            # Refresh JWKS in case the key was rotated
            keys = _get_jwks_keys(base_url=settings.supabase_url or token_iss, force_refresh=True)
            for k in keys:
                if k.get("kid") == key_id:
                    matching_jwk = k
                    break
        if matching_jwk is None:
            logger.warning("No matching JWKS key for kid=%s", key_id)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        try:
            pyjwk = jwt.PyJWK.from_dict(matching_jwk)
            key = pyjwk.key
        except Exception as exc:
            logger.error("Failed to parse JWK key: %s", exc)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Invalid JWKS key format",
            ) from exc

        algorithms = [algorithm]
    else:
        logger.warning("Unsupported JWT algorithm: %s", algorithm)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        claims = jwt.decode(
            token,
            key,
            algorithms=algorithms,
            audience="authenticated",
            options={
                "require": ["exp", "sub", "aud"],
                "verify_exp": True,
                "verify_aud": True,
            },
        )
        # Supabase iss is always https://<project>.supabase.co or https://<project>.supabase.co/auth/v1
        if settings.supabase_url:
            expected_prefix = settings.supabase_url.rstrip("/")
            actual_iss = claims.get("iss", "").rstrip("/")
            if expected_prefix and actual_iss:
                norm_expected = expected_prefix[:-8] if expected_prefix.endswith("/auth/v1") else expected_prefix
                norm_actual = actual_iss[:-8] if actual_iss.endswith("/auth/v1") else actual_iss
                if norm_expected != norm_actual:
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

    if token.count(".") == 2:
        if settings.supabase_jwt_secret or settings.supabase_url:
            claims = _decode_supabase_jwt(token)
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token",
                headers={"WWW-Authenticate": "Bearer"},
            )
    elif settings.dev_token_auth:
        claims = _decode_dev_token(token)
    elif settings.supabase_jwt_secret or settings.supabase_url:
        claims = _decode_supabase_jwt(token)
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
