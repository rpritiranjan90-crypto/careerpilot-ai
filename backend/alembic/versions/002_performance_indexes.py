"""Add additional indexes for query performance.

Adds composite indexes for common query patterns:
- resumes: (user_id, created_at DESC) for listing user's resumes in reverse-chronological order
- interview_questions: (interview_id, asked_at) for fetching Q&A history
- job_descriptions: (user_id, created_at DESC) for listing user's job descriptions

Revision ID: 002
Revises: 001
Create Date: 2026-09-01 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("SET search_path TO careerpilot")
    # Composite index for listing user's resumes newest first
    op.create_index(
        "ix_resumes_user_id_created_at",
        "resumes",
        ["user_id", sa.text("created_at DESC")],
    )
    # Composite index for fetching Q&A history of an interview
    op.create_index(
        "ix_interview_questions_interview_id_asked_at",
        "interview_questions",
        ["interview_id", "asked_at"],
    )
    # Composite index for listing user's job descriptions
    op.create_index(
        "ix_job_descriptions_user_id_created_at",
        "job_descriptions",
        ["user_id", sa.text("created_at DESC")],
    )
    # Composite index for user's analyses
    op.create_index(
        "ix_resume_analyses_resume_id_created_at",
        "resume_analyses",
        ["resume_id", sa.text("created_at DESC")],
    )


def downgrade() -> None:
    op.execute("SET search_path TO careerpilot")
    op.drop_index("ix_resume_analyses_resume_id_created_at", table_name="resume_analyses")
    op.drop_index("ix_job_descriptions_user_id_created_at", table_name="job_descriptions")
    op.drop_index("ix_interview_questions_interview_id_asked_at", table_name="interview_questions")
    op.drop_index("ix_resumes_user_id_created_at", table_name="resumes")
