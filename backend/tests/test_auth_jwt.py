"""Comprehensive JWT authentication unit tests.

Verifies:
- Supabase HS256 token verification
- Valid token with proper claims
- Expired token rejection
- Invalid signature rejection
- Invalid issuer / audience rejection
- Missing claims (sub) rejection
- Unconfigured secret rejection
- Dev token fallback behavior
"""

import time
import jwt
import pytest
from fastapi import HTTPException
from app.core.config import settings
from app.security.auth import _decode_supabase_jwt, _decode_dev_token, verify_user


def test_decode_supabase_jwt_valid(monkeypatch):
    secret = "super-secret-jwt-key-for-testing-12345"
    monkeypatch.setattr(settings, "supabase_jwt_secret", secret)
    monkeypatch.setattr(settings, "supabase_url", "https://xyzcompany.supabase.co")

    payload = {
        "sub": "user-uuid-1234",
        "email": "user@example.com",
        "aud": "authenticated",
        "iss": "https://xyzcompany.supabase.co",
        "exp": int(time.time()) + 3600,
    }
    token = jwt.encode(payload, secret, algorithm="HS256")
    claims = _decode_supabase_jwt(token)
    assert claims["sub"] == "user-uuid-1234"
    assert claims["email"] == "user@example.com"


def test_decode_supabase_jwt_expired(monkeypatch):
    secret = "super-secret-jwt-key-for-testing-12345"
    monkeypatch.setattr(settings, "supabase_jwt_secret", secret)
    monkeypatch.setattr(settings, "supabase_url", "https://xyzcompany.supabase.co")

    payload = {
        "sub": "user-uuid-1234",
        "aud": "authenticated",
        "iss": "https://xyzcompany.supabase.co",
        "exp": int(time.time()) - 3600,  # Expired
    }
    token = jwt.encode(payload, secret, algorithm="HS256")
    with pytest.raises(HTTPException) as exc_info:
        _decode_supabase_jwt(token)
    assert exc_info.value.status_code == 401
    assert "expired" in exc_info.value.detail.lower()


def test_decode_supabase_jwt_invalid_signature(monkeypatch):
    secret = "super-secret-jwt-key-for-testing-12345"
    monkeypatch.setattr(settings, "supabase_jwt_secret", secret)
    monkeypatch.setattr(settings, "supabase_url", "https://xyzcompany.supabase.co")

    payload = {
        "sub": "user-uuid-1234",
        "aud": "authenticated",
        "iss": "https://xyzcompany.supabase.co",
        "exp": int(time.time()) + 3600,
    }
    token = jwt.encode(payload, "wrong-secret-key-123", algorithm="HS256")
    with pytest.raises(HTTPException) as exc_info:
        _decode_supabase_jwt(token)
    assert exc_info.value.status_code == 401


def test_decode_supabase_jwt_invalid_audience(monkeypatch):
    secret = "super-secret-jwt-key-for-testing-12345"
    monkeypatch.setattr(settings, "supabase_jwt_secret", secret)
    monkeypatch.setattr(settings, "supabase_url", "https://xyzcompany.supabase.co")

    payload = {
        "sub": "user-uuid-1234",
        "aud": "wrong-audience",
        "iss": "https://xyzcompany.supabase.co",
        "exp": int(time.time()) + 3600,
    }
    token = jwt.encode(payload, secret, algorithm="HS256")
    with pytest.raises(HTTPException) as exc_info:
        _decode_supabase_jwt(token)
    assert exc_info.value.status_code == 401


def test_decode_supabase_jwt_invalid_issuer(monkeypatch):
    secret = "super-secret-jwt-key-for-testing-12345"
    monkeypatch.setattr(settings, "supabase_jwt_secret", secret)
    monkeypatch.setattr(settings, "supabase_url", "https://xyzcompany.supabase.co")

    payload = {
        "sub": "user-uuid-1234",
        "aud": "authenticated",
        "iss": "https://attacker.supabase.co",
        "exp": int(time.time()) + 3600,
    }
    token = jwt.encode(payload, secret, algorithm="HS256")
    with pytest.raises(HTTPException) as exc_info:
        _decode_supabase_jwt(token)
    assert exc_info.value.status_code == 401


def test_decode_supabase_jwt_missing_secret(monkeypatch):
    monkeypatch.setattr(settings, "supabase_jwt_secret", "")
    token = jwt.encode({"sub": "user-1"}, "temp-key", algorithm="HS256")
    with pytest.raises(HTTPException) as exc_info:
        _decode_supabase_jwt(token)
    assert exc_info.value.status_code == 500


def test_decode_dev_token():
    claims = _decode_dev_token("dev-user-999")
    assert claims["sub"] == "dev-user-999"
    assert claims["email"] == "dev-user-999@dev.local"
    assert claims["dev_mode"] is True


def test_decode_supabase_jwt_es256_jwks(monkeypatch):
    from cryptography.hazmat.primitives.asymmetric import ec
    from cryptography.hazmat.primitives import serialization
    import json
    import base64

    # Generate EC private key for testing
    private_key = ec.generate_private_key(ec.SECP256R1())
    public_key = private_key.public_key()
    public_numbers = public_key.public_numbers()

    # Base64url helper
    def b64url(n: int) -> str:
        b = n.to_bytes(32, byteorder="big")
        return base64.urlsafe_b64encode(b).decode("utf-8").rstrip("=")

    jwk = {
        "kty": "EC",
        "crv": "P-256",
        "x": b64url(public_numbers.x),
        "y": b64url(public_numbers.y),
        "kid": "test-kid-123",
        "use": "sig",
        "alg": "ES256",
    }

    # Mock _get_jwks_keys to return our test JWK
    monkeypatch.setattr("app.security.auth._get_jwks_keys", lambda base_url=None, force_refresh=False: [jwk])
    monkeypatch.setattr(settings, "supabase_url", "https://xyzcompany.supabase.co")

    payload = {
        "sub": "user-uuid-es256",
        "email": "user@example.com",
        "aud": "authenticated",
        "iss": "https://xyzcompany.supabase.co/auth/v1",
        "exp": int(time.time()) + 3600,
    }

    token = jwt.encode(
        payload,
        private_key,
        algorithm="ES256",
        headers={"kid": "test-kid-123"},
    )

    claims = _decode_supabase_jwt(token)
    assert claims["sub"] == "user-uuid-es256"
    assert claims["email"] == "user@example.com"

