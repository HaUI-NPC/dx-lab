# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from dxlab_core.audit.models import AuditEvent
from dxlab_core.auth.principal import Principal
from dxlab_core.request_id import current_request_id


def record(
    session: Session,
    *,
    actor: Principal | None,
    action: str,
    object_type: str,
    object_id: str,
    details: dict[str, Any] | None = None,
) -> AuditEvent:
    """Ghi một sự kiện audit trong cùng transaction với thay đổi nghiệp vụ.

    `action` dùng khóa hành động của docs/AUTHZ.md mục 4 (ví dụ `definition.publish`); `details` chứa căn cứ,
    hình thức (KT./TUQ.), phiên bản — không chứa dữ liệu cá nhân.
    """
    event = AuditEvent(
        actor=actor.username if actor else None,
        actor_roles=[{"role": a.role, "unit": a.unit} for a in actor.roles] if actor else [],
        action=action,
        object_type=object_type,
        object_id=object_id,
        details=details or {},
        request_id=current_request_id(),
    )
    session.add(event)
    session.flush()
    return event


def events_for(session: Session, object_type: str, object_id: str) -> list[AuditEvent]:
    """Lịch sử của một đối tượng, cũ trước mới sau."""
    stmt = (
        select(AuditEvent)
        .where(AuditEvent.object_type == object_type, AuditEvent.object_id == object_id)
        .order_by(AuditEvent.seq)
    )
    return list(session.scalars(stmt))
