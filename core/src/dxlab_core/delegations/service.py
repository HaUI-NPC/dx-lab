# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

"""Ủy quyền TUQ. theo docs/AUTHZ.md mục 9.

- Chỉ người đang giữ vai trò (theo token) mới ủy quyền được, nên quyền nhận ủy quyền không ủy quyền lại được.
- Thời hạn tối đa 30 ngày; bắt buộc số giấy ủy quyền; người ủy quyền thu hồi được bất kỳ lúc nào.
- Người nhận dùng tài khoản của chính mình và phải giữ một vai trò thuộc đơn vị của người ủy quyền.
- Ủy quyền chỉ trao đúng vai trò và đơn vị của người ủy quyền: bước duyệt cần vai trò cao hơn (hạn mức lớn hơn)
  không dùng được ủy quyền này.
"""

import uuid
from collections.abc import Iterable
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from dxlab_core.audit.service import record
from dxlab_core.auth.principal import REPORTER, Principal, unit_contains
from dxlab_core.delegations.models import Delegation
from dxlab_core.errors import ApiError, Conflict, NotFound, ValidationFailed

APPROVE = "repair.approve"
MAX_DURATION = timedelta(days=30)


def status_of(delegation: Delegation, now: datetime | None = None) -> str:
    now = now or datetime.now(UTC)
    if delegation.revoked_at is not None:
        return "revoked"
    if now >= delegation.ends_at:
        return "expired"
    if now < delegation.starts_at:
        return "scheduled"
    return "active"


def out(delegation: Delegation) -> dict:
    return {"id": delegation.id, "number": delegation.number, "action": delegation.action,
            "delegator": delegation.delegator, "role": delegation.role, "unit": delegation.unit,
            "delegate": delegation.delegate, "starts_at": delegation.starts_at, "ends_at": delegation.ends_at,
            "created_at": delegation.created_at, "revoked_at": delegation.revoked_at,
            "status": status_of(delegation)}


def create(session: Session, principal: Principal, *, delegate: str, role: str, unit: str | None, number: str,
           starts_at: datetime, ends_at: datetime, action: str) -> Delegation:
    if principal.is_system_admin:
        raise ApiError(403, "FORBIDDEN_ROLE", "Quản trị hệ thống không được làm nghiệp vụ.", {"layer": 1, "rule": "SoD-4"})
    units = principal.units_for(role) if role != REPORTER else ()
    if not units:
        raise ApiError(403, "FORBIDDEN_ROLE", "Chỉ người đang giữ vai trò này mới ủy quyền được; quyền nhận ủy quyền "
                       "không được ủy quyền lại.", {"layer": 1, "role": role})
    if unit is None:
        if len(units) > 1:
            raise ValidationFailed([{"path": "unit", "message": "Bạn giữ vai trò này ở nhiều đơn vị; hãy chọn đơn vị."}])
        unit = units[0]
    elif unit not in units:
        raise ApiError(403, "FORBIDDEN_SCOPE", "Bạn không giữ vai trò này tại đơn vị đã chọn.", {"layer": 2})
    errors = []
    if delegate == principal.username:
        errors.append({"path": "delegate", "message": "Không tự ủy quyền cho chính mình."})
    if ends_at <= starts_at:
        errors.append({"path": "ends_at", "message": "Thời điểm kết thúc phải sau thời điểm bắt đầu."})
    elif ends_at - starts_at > MAX_DURATION:
        errors.append({"path": "ends_at", "message": "Ủy quyền tối đa 30 ngày."})
    elif ends_at <= datetime.now(UTC):
        errors.append({"path": "ends_at", "message": "Thời hạn ủy quyền đã qua."})
    if errors:
        raise ValidationFailed(errors)
    delegation = Delegation(number=number, action=action, delegator=principal.username, role=role, unit=unit,
                            delegate=delegate, starts_at=starts_at, ends_at=ends_at)
    session.add(delegation)
    session.flush()
    record(session, actor=principal, action="delegation.create", object_type="delegation",
           object_id=str(delegation.id),
           details={"number": number, "action": action, "role": role, "unit": unit, "delegate": delegate,
                    "starts_at": starts_at.isoformat(), "ends_at": ends_at.isoformat()})
    session.refresh(delegation)
    return delegation


def revoke(session: Session, principal: Principal, delegation_id: uuid.UUID) -> Delegation:
    delegation = session.get(Delegation, delegation_id, with_for_update=True)
    if delegation is None or principal.username not in (delegation.delegator, delegation.delegate):
        raise NotFound("Không có ủy quyền này.")
    if delegation.delegator != principal.username:
        raise ApiError(403, "FORBIDDEN_ROLE", "Chỉ người ủy quyền được thu hồi.", {"layer": 1})
    if delegation.revoked_at is not None:
        raise Conflict("Ủy quyền đã bị thu hồi.")
    delegation.revoked_at = datetime.now(UTC)
    delegation.revoked_by = principal.username
    record(session, actor=principal, action="delegation.revoke", object_type="delegation",
           object_id=str(delegation.id), details={"number": delegation.number})
    session.flush()
    return delegation


def listing(session: Session, principal: Principal, limit: int, offset: int) -> dict:
    mine = or_(Delegation.delegator == principal.username, Delegation.delegate == principal.username)
    total = session.scalar(select(func.count()).select_from(Delegation).where(mine))
    rows = session.scalars(select(Delegation).where(mine)
                           .order_by(Delegation.created_at.desc(), Delegation.id).limit(limit).offset(offset))
    return {"items": [out(d) for d in rows], "total": total}


def active_for(session: Session, username: str) -> list[Delegation]:
    """Ủy quyền đang có hiệu lực mà `username` được nhận."""
    now = datetime.now(UTC)
    return list(session.scalars(select(Delegation).where(
        Delegation.delegate == username, Delegation.revoked_at.is_(None),
        Delegation.starts_at <= now, Delegation.ends_at > now)))


def applicable(principal: Principal, delegations: Iterable[Delegation], role: str, unit: str) -> Delegation | None:
    """Ủy quyền cho phép `principal` làm bước duyệt cần `role` tại `unit` (rỗng: phạm vi toàn trường)."""
    for delegation in delegations:
        if delegation.action != APPROVE or delegation.role != role:
            continue
        if unit and not unit_contains(delegation.unit, unit):
            continue
        if not any(unit_contains(delegation.unit, assignment.unit) for assignment in principal.roles):
            continue
        return delegation
    return None
