"""Add persistence for the discharge coding review Agent.

Revision ID: 20260724_review_agent
Revises: 2d2d716d01fb
Create Date: 2026-07-24
"""

from alembic import op
import sqlalchemy as sa


revision = "20260724_review_agent"
down_revision = "2d2d716d01fb"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "review_sessions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("mode", sa.String(length=32), nullable=False),
        sa.Column("preferred_mode", sa.String(length=16), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("documents", sa.JSON(), nullable=False),
        sa.Column("patient_context", sa.JSON(), nullable=False),
        sa.Column("redaction_receipt", sa.JSON(), nullable=False),
        sa.Column("analysis", sa.JSON(), nullable=False),
        sa.Column("pending_actions", sa.JSON(), nullable=False),
        sa.Column("operator_hash", sa.String(length=128), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_review_sessions_status", "review_sessions", ["status"], unique=False)
    op.create_index("ix_review_sessions_updated_at", "review_sessions", ["updated_at"], unique=False)
    op.create_table(
        "review_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("review_id", sa.String(length=36), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("phase", sa.String(length=32), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["review_id"], ["review_sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("review_id", "sequence", name="uq_review_events_review_sequence"),
    )
    op.create_index("ix_review_events_review_id", "review_events", ["review_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_review_events_review_id", table_name="review_events")
    op.drop_table("review_events")
    op.drop_index("ix_review_sessions_updated_at", table_name="review_sessions")
    op.drop_index("ix_review_sessions_status", table_name="review_sessions")
    op.drop_table("review_sessions")
