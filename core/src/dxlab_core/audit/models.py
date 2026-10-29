# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import BigInteger, DateTime, Identity, Index, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from dxlab_core.db import Base


class AuditEvent(Base):
    """Một dòng audit. Không bao giờ sửa hay xóa; không chứa dữ liệu cá nhân (docs/AUTHZ.md mục 8)."""

    __tablename__ = "audit_events"
    __table_args__ = (Index("ix_audit_events_object", "object_type", "object_id"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # Thứ tự ghi tuyệt đối: nhiều sự kiện trong cùng transaction có cùng `occurred_at`.
    seq: Mapped[int] = mapped_column(BigInteger, Identity(), unique=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    actor: Mapped[str | None] = mapped_column(String(255))
    actor_roles: Mapped[list[dict[str, str]]] = mapped_column(JSONB, default=list)
    action: Mapped[str] = mapped_column(String(100))
    object_type: Mapped[str] = mapped_column(String(100))
    object_id: Mapped[str] = mapped_column(String(255))
    details: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    request_id: Mapped[str | None] = mapped_column(String(128))
