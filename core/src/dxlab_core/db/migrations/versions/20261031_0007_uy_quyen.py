# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

"""Ủy quyền TUQ. có thời hạn (CORE-05b, docs/AUTHZ.md mục 9)."""
import sqlalchemy as sa
from alembic import op

revision: str = "0007"
down_revision: str | None = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("delegations",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("number", sa.String(50), nullable=False),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("delegator", sa.String(255), nullable=False),
        sa.Column("role", sa.String(64), nullable=False),
        sa.Column("unit", sa.String(255), nullable=False),
        sa.Column("delegate", sa.String(255), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
        sa.Column("revoked_by", sa.String(255)))
    for name in ("delegator", "delegate"):
        op.create_index(f"ix_delegations_{name}", "delegations", [name])


def downgrade() -> None:
    op.drop_table("delegations")
