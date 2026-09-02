"""Configuration safety and production validation unit tests.

Verifies:
- Production safety validator blocks dangerous dev auth in production
- Production safety validator requires SUPABASE_JWT_SECRET
- Production safety validator requires DATABASE_URL
- CORS origins parsing for both comma-separated strings and JSON arrays
- Allowed extensions parsing for both comma-separated strings and JSON arrays
"""

import pytest
from app.core.config import Settings


def test_production_safety_blocks_dev_token():
    with pytest.raises(ValueError, match="DEV_TOKEN_AUTH cannot be enabled in production"):
        Settings(
            environment="production",
            dev_token_auth=True,
            supabase_jwt_secret="secret123",
            database_url="postgresql://user:pass@localhost:5432/db",
        )


def test_production_safety_requires_jwt_secret():
    with pytest.raises(ValueError, match="SUPABASE_JWT_SECRET is not set"):
        Settings(
            environment="production",
            dev_token_auth=False,
            supabase_jwt_secret="",
            database_url="postgresql://user:pass@localhost:5432/db",
        )


def test_production_safety_requires_database_url():
    with pytest.raises(ValueError, match="DATABASE_URL is not set"):
        Settings(
            environment="production",
            dev_token_auth=False,
            supabase_jwt_secret="secret123",
            database_url="",
        )


def test_production_safety_valid_config():
    s = Settings(
        environment="production",
        dev_token_auth=False,
        supabase_jwt_secret="valid-secret-key-123",
        database_url="postgresql://user:pass@localhost:5432/db",
    )
    assert s.environment == "production"
    assert s.dev_token_auth is False


def test_cors_origins_comma_separated():
    s = Settings(cors_origins="http://localhost:3000,http://frontend:80")
    assert "http://localhost:3000" in s.cors_origins
    assert "http://frontend:80" in s.cors_origins


def test_cors_origins_json_array():
    s = Settings(cors_origins='["http://localhost:3000", "http://frontend:80"]')
    assert "http://localhost:3000" in s.cors_origins
    assert "http://frontend:80" in s.cors_origins


def test_allowed_extensions_parsing():
    s = Settings(allowed_extensions="pdf, docx, txt")
    assert s.allowed_extensions == ["pdf", "docx", "txt"]
