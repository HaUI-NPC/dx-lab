# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

"""Trạng thái workflow và bước người dùng, gắn phiên bản định nghĩa bất biến."""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("workflows",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("app_id", sa.String(64), nullable=False),
        sa.Column("definition_version_id", sa.UUID(), sa.ForeignKey("definition_versions.id"), nullable=False),
        sa.Column("created_by", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("due_at", sa.DateTime(timezone=True)),
        sa.Column("status", sa.String(255), nullable=False),
        sa.Column("status_name", sa.String(255), nullable=False),
        sa.Column("data", postgresql.JSONB(), nullable=False),
        sa.Column("engine_state", postgresql.JSONB(), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False))
    for name in ("app_id", "created_by", "status"):
        op.create_index(f"ix_workflows_{name}", "workflows", [name])
    op.create_table("workflow_tasks",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("workflow_id", sa.UUID(), sa.ForeignKey("workflows.id", ondelete="CASCADE"), nullable=False),
        sa.Column("engine_task_id", sa.String(36), nullable=False, unique=True),
        sa.Column("step_id", sa.String(255), nullable=False),
        sa.Column("step_name", sa.String(255), nullable=False),
        sa.Column("lane", sa.String(64), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("completed_by", sa.String(255)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("due_at", sa.DateTime(timezone=True)))
    for name in ("workflow_id", "status"):
        op.create_index(f"ix_workflow_tasks_{name}", "workflow_tasks", [name])


def downgrade() -> None:
    op.drop_table("workflow_tasks")
    op.drop_table("workflows")
