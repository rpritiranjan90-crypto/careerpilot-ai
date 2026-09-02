"""Initial schema - all tables

Revision ID: 001
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Switch to the CareerPilot schema for all table operations
    op.execute("SET search_path TO careerpilot")

    # Enable UUID extension (PostgreSQL) — must be in public schema
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    # Users table
    op.create_table(
        "users",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("email", sa.String(), nullable=False, unique=True),
        sa.Column("name", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_id", "users", ["id"])

    # Resumes table
    op.create_table(
        "resumes",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("user_id", sa.String(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("filename", sa.String(), nullable=False),
        sa.Column("storage_path", sa.String(), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False),
        sa.Column("mime_type", sa.String(), nullable=True),
        sa.Column("extracted_text", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_resumes_id", "resumes", ["id"])
    op.create_index("ix_resumes_user_id", "resumes", ["user_id"])

    # Resume analyses table
    op.create_table(
        "resume_analyses",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("resume_id", sa.String(), sa.ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("result_json", sa.JSON(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_resume_analyses_id", "resume_analyses", ["id"])
    op.create_index("ix_resume_analyses_resume_id", "resume_analyses", ["resume_id"])

    # Job descriptions table
    op.create_table(
        "job_descriptions",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("user_id", sa.String(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(), nullable=True),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_job_descriptions_id", "job_descriptions", ["id"])
    op.create_index("ix_job_descriptions_user_id", "job_descriptions", ["user_id"])

    # Job matches table
    op.create_table(
        "job_matches",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("job_description_id", sa.String(), sa.ForeignKey("job_descriptions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("resume_id", sa.String(), sa.ForeignKey("resumes.id", ondelete="SET NULL"), nullable=True),
        sa.Column("match_score", sa.Integer(), nullable=False),
        sa.Column("result_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_job_matches_id", "job_matches", ["id"])
    op.create_index("ix_job_matches_job_description_id", "job_matches", ["job_description_id"])
    op.create_index("ix_job_matches_resume_id", "job_matches", ["resume_id"])

    # Interviews table
    op.create_table(
        "interviews",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("user_id", sa.String(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("interview_type", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_interviews_id", "interviews", ["id"])
    op.create_index("ix_interviews_user_id", "interviews", ["user_id"])

    # Interview questions table
    op.create_table(
        "interview_questions",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("interview_id", sa.String(), sa.ForeignKey("interviews.id", ondelete="CASCADE"), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("answer", sa.Text(), nullable=True),
        sa.Column("evaluation_json", sa.JSON(), nullable=True),
        sa.Column("score", sa.Integer(), nullable=True),
        sa.Column("asked_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("answered_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_interview_questions_id", "interview_questions", ["id"])
    op.create_index("ix_interview_questions_interview_id", "interview_questions", ["interview_id"])


def downgrade() -> None:
    op.execute("SET search_path TO careerpilot")
    op.drop_table("interview_questions")
    op.drop_table("interviews")
    op.drop_table("job_matches")
    op.drop_table("job_descriptions")
    op.drop_table("resume_analyses")
    op.drop_table("resumes")
    op.drop_table("users")
