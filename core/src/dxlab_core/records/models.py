# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKeyConstraint, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from dxlab_core.db import Base


class RecordType(Base):
    """Loại bản ghi của một ứng dụng: JSON Schema (Draft 2020-12) lấy từ `records/<loại>-record.json` của gói."""

    __tablename__ = "record_types"

    app_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    record_type: Mapped[str] = mapped_column(String(64), primary_key=True)
    schema: Mapped[dict[str, Any]] = mapped_column(JSONB)
    # Tăng 1 mỗi lần schema đổi nội dung; bản ghi nhớ phiên bản schema đã kiểm dữ liệu của nó.
    version: Mapped[int] = mapped_column(Integer, default=1)
    registered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Record(Base):
    """Một bản ghi danh mục kèm nguồn gốc: `source`, `license`, ai tạo / sửa lần cuối và lúc nào."""

    __tablename__ = "records"
    __table_args__ = (
        ForeignKeyConstraint(
            ["app_id", "record_type"], ["record_types.app_id", "record_types.record_type"], ondelete="RESTRICT"
        ),
    )

    app_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    record_type: Mapped[str] = mapped_column(String(64), primary_key=True)
    key: Mapped[str] = mapped_column(String(128), primary_key=True)
    data: Mapped[dict[str, Any]] = mapped_column(JSONB)
    schema_version: Mapped[int] = mapped_column(Integer)
    source: Mapped[str] = mapped_column(Text)
    license: Mapped[str] = mapped_column(String(255))
    source_ref: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_by: Mapped[str] = mapped_column(String(255))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
