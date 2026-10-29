# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

"""Quyền lane/phạm vi và không kiêm nhiệm của bước BPMN; mặc định từ chối."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from dxlab_core.audit.service import events_for, record
from dxlab_core.auth.principal import Principal, unit_contains
from dxlab_core.definitions.engine import task_properties
from dxlab_core.errors import ApiError
from dxlab_core.workflows.models import Workflow, WorkflowTask
from dxlab_core.workflows.privacy import mask_personal_data


def required_role(instance: Workflow, task) -> str:
    lane = task.task_spec.lane
    if lane == "technician":
        return str(instance.data.get("tech_role", ""))
    if lane == "approver":
        return str(instance.data.get("approver_role", ""))
    return lane or ""


def required_unit(instance: Workflow, task) -> str:
    lane = task.task_spec.lane
    if lane == "technician":
        unit = str(instance.data.get("tech_unit", ""))
        return str(instance.data.get(unit, "")) if not unit.startswith("/") else unit
    if lane == "approver":
        scope = instance.data.get("approval_scope")
        if scope == "university":
            return ""
        return str(instance.data.get({"faculty": "owner_faculty", "school": "owner_school"}.get(scope, ""), ""))
    return str(instance.data.get("room_unit", ""))


def authorize_task(session: Session, principal: Principal, instance: Workflow, task) -> None:
    if principal.is_system_admin:
        raise ApiError(403, "FORBIDDEN_ROLE", "Quản trị hệ thống không được làm nghiệp vụ.", {"layer": 1, "rule": "SoD-4"})
    excludes = task_properties(task.task_spec).get("dxlabExcludeActorsOf", "")
    excluded_steps = {s.strip() for s in excludes.split(",") if s.strip()}
    if any(e.actor == principal.username and e.details.get("step_id") in excluded_steps
           for e in events_for(session, "workflow", str(instance.id))):
        raise ApiError(403, "FORBIDDEN_SOD", "Bạn đã làm bước không được kiêm nhiệm với bước này.", {"layer": 4})
    role = required_role(instance, task)
    if role == "reporter":
        if instance.created_by != principal.username:
            raise ApiError(403, "FORBIDDEN_SCOPE", "Chỉ người tạo được làm bước này.", {"layer": 2})
        return
    if role == "lab_manager" and instance.data.get("room_manager_role") == "faculty_head":
        role = "faculty_head"
    if not role or not principal.has_role(role):
        raise ApiError(403, "FORBIDDEN_ROLE", "Bạn không giữ vai trò của bước này.", {"layer": 1, "role": role})
    unit = required_unit(instance, task)
    university = task.task_spec.lane == "approver" and instance.data.get("approval_scope") == "university"
    if not university and (not unit or not any(unit_contains(u, unit) for u in principal.units_for(role))):
        raise ApiError(403, "FORBIDDEN_SCOPE", "Bước nằm ngoài phạm vi đơn vị của bạn.", {"layer": 2})


def can_read(principal: Principal, instance: Workflow) -> bool:
    if principal.is_system_admin:
        return False
    if principal.username == instance.created_by:
        return True
    room = str(instance.data.get("room_unit", ""))
    for a in principal.roles:
        if a.role in {"internal_auditor", "facility_officer", "facility_director", "vice_president", "president"}:
            return True
        if a.role == "finance_officer" and instance.data.get("estimated_cost_vnd", 0) > 0:
            return True
        if a.role in {"lab_manager", "faculty_head", "faculty_deputy", "school_head"} and room and unit_contains(a.unit, room):
            return True
        if a.role == instance.data.get("tech_role"):
            tech = instance.data.get("tech_unit", "")
            tech = instance.data.get(tech, "") if not str(tech).startswith("/") else tech
            if tech and unit_contains(a.unit, tech):
                return True
    return False


def data_for(session: Session, principal: Principal, instance: Workflow) -> dict:
    room = str(instance.data.get("room_unit", ""))
    can_contact = principal.username == instance.created_by or principal.has_role("internal_auditor")
    can_contact = can_contact or any(a.role in {"lab_manager", "faculty_head", "faculty_deputy"}
                                     and room and unit_contains(a.unit, room) for a in principal.roles)
    tech = str(instance.data.get("tech_unit", ""))
    if tech and not tech.startswith("/"):
        tech = str(instance.data.get(tech, ""))
    assigned = session.scalar(select(WorkflowTask.id).where(
        WorkflowTask.workflow_id == instance.id, WorkflowTask.lane == "technician",
        WorkflowTask.status == "ready").limit(1))
    if assigned is not None:
        can_contact = can_contact or any(a.role == instance.data.get("tech_role") and tech
                                         and unit_contains(a.unit, tech) for a in principal.roles)
    masked = mask_personal_data(instance, instance.data)
    if not can_contact:
        return masked
    if masked != instance.data:
        record(session, actor=principal, action="reporter_contact.read", object_type="workflow",
               object_id=str(instance.id), details={"purpose": "request.read"})
    return dict(instance.data)
