"""Test fixtures and configuration for backend tests."""

# Patch settings before importing app
import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("ENVIRONMENT", "test")  # Don't trigger production config guards
os.environ.setdefault("DEV_TOKEN_AUTH", "true")
os.environ.setdefault("SUPABASE_JWT_SECRET", "")  # Empty so dev token auth path is used

from app.core.database import Base, get_db
from app.main import app
from app.security.auth import get_current_user

# ---------------------------------------------------------------------------
# Test database (in-memory SQLite for speed; Alembic migration tested separately)
# StaticPool keeps a single connection alive so the in-memory DB is shared
# across threads (FastAPI runs the test endpoint in another thread).
# ---------------------------------------------------------------------------

TEST_DATABASE_URL = "sqlite:///:memory:"
_test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
_TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_test_engine)


def _override_get_db():
    db = _TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


def _override_get_current_user():
    return {"user_id": "test-user-001", "email": "test@example.com"}


@pytest.fixture(scope="session", autouse=True)
def _setup_db():
    """Create all tables once per test session."""
    Base.metadata.create_all(bind=_test_engine)
    yield
    Base.metadata.drop_all(bind=_test_engine)


@pytest.fixture(scope="function")
def db_session():
    """Per-test database session with rollback."""
    session = _TestSessionLocal()
    yield session
    session.rollback()
    session.close()


@pytest.fixture(autouse=True)
def _apply_db_override():
    app.dependency_overrides[get_db] = _override_get_db
    yield


@pytest.fixture(scope="function")
def client(db_session):
    """FastAPI test client with overridden DB and auth."""
    app.dependency_overrides[get_current_user] = _override_get_current_user
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture(scope="function")
def anon_client():
    """Test client without auth override (no user)."""
    app.dependency_overrides[get_db] = _override_get_db
    # Remove auth override so endpoints return 401
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Sample data fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_resume_text():
    return """
    John Doe
    Software Engineer
    john.doe@email.com

    EXPERIENCE
    Senior Software Engineer at Tech Corp (2020-Present)
    - Developed Python applications serving 100,000+ users
    - Led team of 5 engineers on cloud migration project
    - Improved system performance by 40%

    Software Developer at StartupXYZ (2018-2020)
    - Built REST APIs using Django and PostgreSQL
    - Implemented CI/CD pipelines with Docker and Kubernetes
    - Collaborated with cross-functional teams

    EDUCATION
    Bachelor of Technology in Computer Science
    State University, 2018

    SKILLS
    Python, JavaScript, TypeScript, SQL, Docker, Kubernetes, AWS, Git
    """


@pytest.fixture
def sample_job_description():
    return """
    We are looking for a Senior Software Engineer to join our team.

    Requirements:
    - 5+ years of experience in software development
    - Strong Python and SQL skills
    - Experience with cloud platforms (AWS or Azure)
    - Familiarity with containerization (Docker, Kubernetes)
    - Excellent communication and teamwork skills
    - Experience leading technical teams is a plus

    Preferred:
    - Experience with machine learning
    - Knowledge of data engineering
    - Published open source contributions
    """


@pytest.fixture
def sample_interview_answer():
    return """
    In my previous role at Tech Corp, I was leading a team of 5 engineers on a cloud migration project.
    We needed to migrate our monolithic application to microservices architecture within 6 months.

    I started by analyzing our existing codebase and identifying the best approach.
    Then I created a detailed migration plan and distributed tasks among team members.

    By implementing CI/CD pipelines with Docker and Kubernetes, we reduced deployment time by 60%.
    The project was completed 2 weeks ahead of schedule and improved system reliability by 99.9%.

    This experience taught me the importance of thorough planning and effective team communication.
    """
