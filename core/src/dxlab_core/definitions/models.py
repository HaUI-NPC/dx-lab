# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, LargeBinary, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from dxlab_core.db import Base

PENDING = "pending_approval"
ACTIVE = "active"
SUPERSEDED = "superseded"


class DefinitionVersion(Base):
    """Một phiên bản gói ứng dụng. Không sửa nội dung sau khi nạp; chỉ đổi trạng thái."""

    __tablename__ = "definition_versions"
    __table_args__ = (UniqueConstraint("app_id", "version"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    app_id: Mapped[str] = mapped_column(String(64), index=True)
    version: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(32))
    display_name: Mapped[str] = mapped_column(String(255))
    process_id: Mapped[str] = mapped_column(String(255))
    checksum: Mapped[str] = mapped_column(String(64))
    published_by: Mapped[str] = mapped_column(String(255))
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    activated_by: Mapped[str | None] = mapped_column(String(255))
    activated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    files: Mapped[list["DefinitionFile"]] = relationship(
        back_populates="definition_version", cascade="all, delete-orphan", order_by="DefinitionFile.path"
    )


class DefinitionFile(Base):
    __tablename__ = "definition_files"

    version_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("definition_versions.id", ondelete="CASCADE"), primary_key=True
    )
    path: Mapped[str] = mapped_column(String(512), primary_key=True)
    sha256: Mapped[str] = mapped_column(String(64))
    content: Mapped[bytes] = mapped_column(LargeBinary)

    definition_version: Mapped[DefinitionVersion] = relationship(back_populates="files")
