# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

"""Tổng hợp phiếu được phép xem; không trả dữ liệu cá nhân của phiếu."""
from collections import Counter
from datetime import UTC, datetime

from sqlalchemy import exists, select
from sqlalchemy.orm import Session

from dxlab_core.auth.principal import Principal
from dxlab_core.workflows.access import can_read
from dxlab_core.workflows.models import Workflow, WorkflowTask


def collect(session: Session, principal: Principal, app_id: str | None = None) -> dict:
    """Đếm mọi phiếu hiển thị, kể cả phiếu chưa có đơn vị; chi phí tính bằng đồng."""
    has_ready_task = exists().where(
        WorkflowTask.workflow_id == Workflow.id, WorkflowTask.status == "ready"
    )
    query = select(Workflow, has_ready_task)
    if app_id is not None:
        query = query.where(Workflow.app_id == app_id)
    statuses: Counter[tuple[str, str]] = Counter()
    units: Counter[str | None] = Counter()
    approved_total = actual_total = overdue = 0
    now = datetime.now(UTC)
    for instance, ready in session.execute(query):
        if not can_read(principal, instance):
            continue
        statuses[(instance.status, instance.status_name)] += 1
        unit = instance.data.get("room_unit")
        units[unit if isinstance(unit, str) and unit else None] += 1
        for field in ("approved_amount_vnd", "actual_cost_vnd"):
            value = instance.data.get(field)
            if type(value) is int:
                if field == "approved_amount_vnd":
                    approved_total += value
                else:
                    actual_total += value
        if ready and instance.due_at is not None and instance.due_at < now:
            overdue += 1
    return {
        "by_status": [{"status": status, "status_name": name, "count": count}
                      for (status, name), count in sorted(statuses.items())],
        "by_unit": [{"unit": unit, "count": count}
                    for unit, count in sorted(units.items(), key=lambda item: item[0] or "")],
        "overdue": overdue,
        "cost": {"approved_total": approved_total, "actual_total": actual_total},
    }
