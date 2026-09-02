"""Add career readiness snapshots and user action items tables.

These tables back the Career Improvement Engine (historical snapshots and
persisted action-item completion state) and were previously created only
by Base.metadata.create_all() at runtime. This migration makes them
manageable via Alembic and ensures fresh databases get the same schema
as a long-running production deployment.

Revision ID: 003
Revises: 002
Create Date: 2026-09-02 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("SET search_path TO careerpilot")
    # Career readiness snapshots - historical progress records
    op.create_table(
        "career_readiness_snapshots",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column(
            "user_id",
            sa.String(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("overall_score", sa.Integer(), nullable=False),
        sa.Column("resume_score", sa.Integer(), nullable=True),
        sa.Column("job_match_score", sa.Integer(), nullable=True),
        sa.Column("interview_score", sa.Integer(), nullable=True),
        sa.Column("skills_score", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index(
        "ix_career_readiness_snapshots_id",
        "career_readiness_snapshots",
        ["id"],
    )
    op.create_index(
        "ix_career_readiness_snapshots_user_id",
        "career_readiness_snapshots",
        ["user_id"],
    )
    # Composite index for the per-user timeline read path
    op.create_index(
        "ix_career_readiness_snapshots_user_id_created_at",
        "career_readiness_snapshots",
        ["user_id", sa.text("created_at DESC")],
    )

    # User action items - persisted completion state of improvement plan tasks
    op.create_table(
        "user_action_items",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column(
            "user_id",
            sa.String(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("task_id", sa.String(), nullable=False),
        sa.Column("is_completed", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index(
        "ix_user_action_items_id",
        "user_action_items",
        ["id"],
    )
    op.create_index(
        "ix_user_action_items_user_id",
        "user_action_items",
        ["user_id"],
    )
    op.create_index(
        "ix_user_action_items_task_id",
        "user_action_items",
        ["task_id"],
    )
    # Composite index for the hot read path: lookup by (user, task)
    op.create_index(
        "ix_user_action_items_user_id_task_id",
        "user_action_items",
        ["user_id", "task_id"],
        unique=True,
    )


def downgrade() -> None:
    op.execute("SET search_path TO careerpilot")
    op.drop_index("ix_user_action_items_user_id_task_id", table_name="user_action_items")
    op.drop_index("ix_user_action_items_task_id", table_name="user_action_items")
    op.drop_index("ix_user_action_items_user_id", table_name="user_action_items")
    op.drop_index("ix_user_action_items_id", table_name="user_action_items")
    op.drop_table("user_action_items")

    op.drop_index(
        "ix_career_readiness_snapshots_user_id_created_at",
        table_name="career_readiness_snapshots",
    )
    op.drop_index(
        "ix_career_readiness_snapshots_user_id",
        table_name="career_readiness_snapshots",
    )
    op.drop_index(
        "ix_career_readiness_snapshots_id",
        table_name="career_readiness_snapshots",
    )
    op.drop_table("career_readiness_snapshots")
