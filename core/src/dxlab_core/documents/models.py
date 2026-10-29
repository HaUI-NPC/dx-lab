# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

import uuid
from datetime import datetime

from sqlalchemy import BigInteger, CheckConstraint, DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from dxlab_core.db import Base

KINDS = ("sop", "quote", "other")


class Document(Base):
    """Metadata của một tệp tải lên. Nội dung nằm trên volume ở `<documents_dir>/<sha256[:2]>/<sha256>`."""

    __tablename__ = "documents"
    __table_args__ = (CheckConstraint("kind IN ('sop', 'quote', 'other')", name="kind"),)

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
    # Phiếu (workflow) mà tài liệu đính kèm, nếu có. Chưa có khóa ngoại: bảng workflows do CORE-04a tạo.
    workflow_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), index=True)
    source: Mapped[str] = mapped_column(Text)
    license: Mapped[str] = mapped_column(String(255))
    source_ref: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
