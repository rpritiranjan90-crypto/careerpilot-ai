"""SQLAlchemy ORM models for CareerPilot AI.

All tables use UUID string primary keys and timezone-aware timestamps.
Ownership is enforced at the API layer (authorization middleware).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    JSON,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def generate_uuid() -> str:
    return str(uuid.uuid4())


class User(Base):
    """Authenticated user (mirrors Supabase Auth user)."""

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
    email: Mapped[str] = mapped_column(
        String, unique=True, nullable=False, index=True
    )
    name: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utcnow,
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        onupdate=utcnow,
    )

    resumes: Mapped[list[Resume]] = relationship(
        "Resume",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    job_descriptions: Mapped[list[JobDescription]] = relationship(
        "JobDescription",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    interviews: Mapped[list[Interview]] = relationship(
        "Interview",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    snapshots: Mapped[list[CareerReadinessSnapshot]] = relationship(
        "CareerReadinessSnapshot",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    action_items: Mapped[list[UserActionItem]] = relationship(
        "UserActionItem",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class Resume(Base):
    """Uploaded resume file and extracted text."""

    __tablename__ = "resumes"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    filename: Mapped[str] = mapped_column(String, nullable=False)
    storage_path: Mapped[str] = mapped_column(String, nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    mime_type: Mapped[str | None] = mapped_column(String, nullable=True)
    extracted_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utcnow,
    )

    user: Mapped[User] = relationship("User", back_populates="resumes")
    analyses: Mapped[list[ResumeAnalysis]] = relationship(
        "ResumeAnalysis",
        back_populates="resume",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    job_matches: Mapped[list[JobMatch]] = relationship(
        "JobMatch",
        back_populates="resume",
        lazy="selectin",
    )


class ResumeAnalysis(Base):
    """Stored result of a resume analysis."""

    __tablename__ = "resume_analyses"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
    resume_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("resumes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    result_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utcnow,
    )

    resume: Mapped[Resume] = relationship("Resume", back_populates="analyses")


class JobDescription(Base):
    """Job description saved by a user for matching."""

    __tablename__ = "job_descriptions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str | None] = mapped_column(String, nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utcnow,
    )

    user: Mapped[User] = relationship("User", back_populates="job_descriptions")
    matches: Mapped[list[JobMatch]] = relationship(
        "JobMatch",
        back_populates="job_description",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class JobMatch(Base):
    """Result of matching a resume against a job description."""

    __tablename__ = "job_matches"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
    job_description_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("job_descriptions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    resume_id: Mapped[str | None] = mapped_column(
        String,
        ForeignKey("resumes.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    match_score: Mapped[int] = mapped_column(Integer, nullable=False)
    result_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utcnow,
    )

    job_description: Mapped[JobDescription] = relationship(
        "JobDescription", back_populates="matches"
    )
    resume: Mapped[Resume | None] = relationship(
        "Resume", back_populates="job_matches"
    )


class Interview(Base):
    """Mock interview session."""

    __tablename__ = "interviews"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    interview_type: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(
        String, nullable=False, default="active"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utcnow,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    user: Mapped[User] = relationship("User", back_populates="interviews")
    questions: Mapped[list[InterviewQuestion]] = relationship(
        "InterviewQuestion",
        back_populates="interview",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class InterviewQuestion(Base):
    """Individual question + answer + evaluation within an interview session."""

    __tablename__ = "interview_questions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
    interview_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("interviews.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    evaluation_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    asked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utcnow,
    )
    answered_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    interview: Mapped[Interview] = relationship(
        "Interview", back_populates="questions"
    )


class CareerReadinessSnapshot(Base):
    """Historical snapshot of a user's verified career readiness metrics."""

    __tablename__ = "career_readiness_snapshots"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    overall_score: Mapped[int] = mapped_column(Integer, nullable=False)
    resume_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    job_match_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    interview_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    skills_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utcnow,
    )

    user: Mapped[User] = relationship("User", back_populates="snapshots")


class UserActionItem(Base):
    """Persisted completion state for personalized action items."""

    __tablename__ = "user_action_items"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    task_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    is_completed: Mapped[bool] = mapped_column(default=False, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utcnow,
    )

    user: Mapped[User] = relationship("User", back_populates="action_items")

