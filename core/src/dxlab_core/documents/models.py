# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

import uuid
from datetime import datetime

from sqlalchemy import BigInteger, CheckConstraint, Computed, DateTime, Index, String, Text
from sqlalchemy.dialects.postgresql import TSVECTOR, UUID
from sqlalchemy.orm import Mapped, mapped_column

from dxlab_core.db import Base

KINDS = ("sop", "quote", "other")


class Document(Base):
    """Metadata của một tệp tải lên. Nội dung nằm trên volume ở `<documents_dir>/<sha256[:2]>/<sha256>`."""

    __tablename__ = "documents"
    __table_args__ = (
        CheckConstraint("kind IN ('sop', 'quote', 'other')", name="kind"),
        Index("ix_documents_fts", "fts", postgresql_using="gin"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    app_id: Mapped[str] = mapped_column(String(64), index=True)
    kind: Mapped[str] = mapped_column(String(16), index=True)
    title: Mapped[str] = mapped_column(String(255))
    filename: Mapped[str] = mapped_column(String(255))
    content_type: Mapped[str] = mapped_column(String(255))
    size: Mapped[int] = mapped_column(BigInteger)
    sha256: Mapped[str] = mapped_column(String(64), index=True)
    # Văn bản trích từ tệp `.md` / `text/*` để CORE-08 đánh chỉ mục; tệp khác để trống.
    text: Mapped[str | None] = mapped_column(Text, deferred=True)
    # Chỉ mục toàn văn của CORE-08: tiêu đề (trọng số A) và nội dung (B), `simple` + bỏ dấu qua hàm `dxlab_unaccent`
    # do migration tạo. `left(…, 150000)` giữ tsvector dưới giới hạn 1 MiB của PostgreSQL (tính theo byte tsvector, xem migration 0006).
    fts: Mapped[str] = mapped_column(
        TSVECTOR,
        Computed(
            "setweight(to_tsvector('simple', dxlab_unaccent(title)), 'A') || "
            "setweight(to_tsvector('simple', dxlab_unaccent(left(coalesce(\"text\", ''), 150000))), 'B')",
            persisted=True,
        ),
        deferred=True,
    )
    # Tên mô hình đã dùng để đưa các đoạn của tài liệu vào chỉ mục vector zvec; khác mô hình hiện tại = cần lập lại.
    embedded_model: Mapped[str | None] = mapped_column(String(255))
    # Phiếu (workflow) mà tài liệu đính kèm, nếu có. Chưa có khóa ngoại: bảng workflows do CORE-04a tạo.
    workflow_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), index=True)
    source: Mapped[str] = mapped_column(Text)
    license: Mapped[str] = mapped_column(String(255))
    source_ref: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
