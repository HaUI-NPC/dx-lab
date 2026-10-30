# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from dxlab_core.db import Base


class Delegation(Base):
    """Một giấy ủy quyền: `delegator` giữ `role` tại `unit`, giao cho `delegate` làm `action` trong thời hạn."""

    __tablename__ = "delegations"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    number: Mapped[str] = mapped_column(String(50))
    action: Mapped[str] = mapped_column(String(100))
    delegator: Mapped[str] = mapped_column(String(255), index=True)
    role: Mapped[str] = mapped_column(String(64))
    unit: Mapped[str] = mapped_column(String(255))
    delegate: Mapped[str] = mapped_column(String(255), index=True)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_by: Mapped[str | None] = mapped_column(String(255))
