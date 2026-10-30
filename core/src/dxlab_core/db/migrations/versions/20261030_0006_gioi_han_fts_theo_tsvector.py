# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

"""Hạ giới hạn văn bản đưa vào chỉ mục toàn văn để tsvector luôn dưới 1 MiB của PostgreSQL (CORE-08)

Giới hạn của PostgreSQL tính theo kích thước biểu diễn tsvector, không phải số ký tự: với từ CJK phân biệt,
mỗi ký tự cho khoảng 4,4 byte (200.000 ký tự ≈ 889 KB), nên `left(..., 500000)` vẫn làm upload hợp lệ lỗi 500.
150.000 ký tự (≈ 664 KB trong trường hợp xấu nhất đã đo) còn dư cho tiêu đề và overhead.

Revision ID: 0006
Revises: 0005
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0006"
down_revision: str | None = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _recreate(limit: int) -> None:
    # Cột sinh sẵn không đổi được biểu thức: bỏ chỉ mục và cột, tạo lại (PostgreSQL tự tính lại cho mọi hàng).
    op.drop_index("ix_documents_fts", table_name="documents", postgresql_using="gin")
    op.drop_column("documents", "fts")
    op.add_column("documents", sa.Column("fts", postgresql.TSVECTOR(), sa.Computed(
        "setweight(to_tsvector('simple', dxlab_unaccent(title)), 'A') || "
        f"setweight(to_tsvector('simple', dxlab_unaccent(left(coalesce(\"text\", ''), {limit}))), 'B')",
        persisted=True), nullable=False))
    op.create_index("ix_documents_fts", "documents", ["fts"], unique=False, postgresql_using="gin")


def upgrade() -> None:
    _recreate(150000)


def downgrade() -> None:
    _recreate(500000)
