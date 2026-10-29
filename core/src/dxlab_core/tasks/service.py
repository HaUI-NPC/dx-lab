# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

import json
import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session
from SpiffWorkflow.util.task import TaskState

from dxlab_core.audit.service import events_for, record
from dxlab_core.auth.principal import Principal
from dxlab_core.definitions.engine import form_of, task_properties
from dxlab_core.definitions.service import files_of
from dxlab_core.errors import ApiError, Conflict, NotFound
from dxlab_core.workflows import access
from dxlab_core.workflows.authority import escalate
from dxlab_core.workflows import service as workflows
from dxlab_core.workflows.models import Workflow, WorkflowTask


def synchronize(session: Session, instance: Workflow, engine) -> None:
    existing = {t.engine_task_id: t for t in session.scalars(select(WorkflowTask).where(WorkflowTask.workflow_id == instance.id))}
    for task in workflows.ready_tasks(engine):
        key = str(task.id)
        if key not in existing:
            session.add(WorkflowTask(workflow_id=instance.id, engine_task_id=key,
                         step_id=task.task_spec.bpmn_id, step_name=task.task_spec.bpmn_name or task.task_spec.bpmn_id,
                         lane=task.task_spec.lane, status="ready", due_at=instance.due_at))
        elif existing[key].status == "ready":
            existing[key].due_at = instance.due_at
    session.flush()


def find(session: Session, task_id: uuid.UUID) -> WorkflowTask:
    task = session.get(WorkflowTask, task_id)
    if task is None:
        raise NotFound("Không có bước công việc này.")
    return task


def _engine_task(instance: Workflow, task: WorkflowTask):
    engine = workflows.restore(instance)
    current = engine.get_task_from_id(uuid.UUID(task.engine_task_id))
    if current is None or current.state != TaskState.READY or task.status != "ready":
        raise Conflict("Bước đã hoàn thành hoặc không còn sẵn sàng.")
    return engine, current


def summary(task: WorkflowTask, instance: Workflow) -> dict:
    return {"task_id": str(task.id), "workflow_id": str(instance.id), "app_id": instance.app_id,
            "step_id": task.step_id, "step_name": task.step_name, "lane": task.lane,
            "due_at": task.due_at, "overdue": bool(task.due_at and task.due_at < datetime.now(UTC))}


def listing(session: Session, principal: Principal, limit: int, offset: int, workflow_id: uuid.UUID | None = None) -> dict:
    query = select(WorkflowTask, Workflow).join(Workflow, Workflow.id == WorkflowTask.workflow_id).where(WorkflowTask.status == "ready")
    if workflow_id:
        query = query.where(Workflow.id == workflow_id)
    visible = []
    for task, instance in session.execute(query.order_by(WorkflowTask.created_at, WorkflowTask.id)):
        _, current = _engine_task(instance, task)
        try:
            access.authorize_task(session, principal, instance, current)
        except ApiError as exc:
            if exc.status == 403:
                continue
            raise
        visible.append(summary(task, instance))
    return {"items": visible[offset:offset+limit], "total": len(visible)}


def detail(session: Session, principal: Principal, task: WorkflowTask) -> dict:
    instance = workflows.find(session, task.workflow_id)
    _, current = _engine_task(instance, task)
    access.authorize_task(session, principal, instance, current)
    schema, uischema = form_of(current.task_spec, files_of(instance.definition))
    return {**summary(task, instance), "form": {"schema": schema, "uischema": uischema},
            "data": access.data_for(session, principal, instance)}


def complete(session: Session, principal: Principal, task_id: uuid.UUID, data: dict) -> Workflow:
    task = find(session, task_id)
    # Khóa phiếu trước khi đọc lại bước: mỗi workflow chỉ chuyển trạng thái một lần tại một thời điểm.
    instance = workflows.find(session, task.workflow_id, lock=True)
    session.refresh(task)
    engine, current = _engine_task(instance, task)
    access.authorize_task(session, principal, instance, current)
    schema, _ = form_of(current.task_spec, files_of(instance.definition))
    submitted = workflows.validate_form(schema, data)
    metadata = json.loads(files_of(instance.definition)["process_model.json"])
    bound = {field for binding in metadata.get("record_bindings", [])
             for field in binding.get("fields", {}).values()}
    if "room_unit" in bound:
        bound.update({"owner_faculty", "owner_school", "room_manager_role"})
    if bound & submitted.keys():
        raise ApiError(422, "VALIDATION_FAILED", "Không được sửa thuộc tính lấy từ danh mục.")
    if current.task_spec.lane == "approver":
        limit = current.data.get("approval_limit_vnd")
        amount = submitted.get("approved_amount_vnd")
        if amount is not None and (not isinstance(limit, (int, float)) or amount > limit):
            raise ApiError(403, "FORBIDDEN_AUTHORITY", "Số tiền duyệt vượt hạn mức.", {"layer": 3})
        for key in ("approver_role", "signing_type"):
            if key in submitted and submitted[key] != current.data.get(key):
                raise ApiError(403, "FORBIDDEN_AUTHORITY", "Thông tin duyệt không khớp thẩm quyền.", {"layer": 3})
    current.data.update(submitted)
    if "actual_cost_vnd" in submitted:
        current.data["repair_recorded"] = True
    current.run()
    engine.do_engine_steps()
    task.status = "completed"
    task.completed_by = principal.username
    task.completed_at = datetime.now(UTC)
    workflows.save_engine(instance, engine)
    details = {"step_id": task.step_id, "step_name": task.step_name, "task_id": str(task.id),
               "version": instance.definition.version}
    if task.lane == "approver":  # căn cứ thẩm quyền và hình thức ký chỉ thuộc về bước duyệt
        details |= {"authority_basis": instance.data.get("authority_basis"),
                    "signing_type": instance.data.get("signing_type")}
    record(session, actor=principal, action="repair.approve" if task.lane == "approver" else "task.complete",
           object_type="workflow", object_id=str(instance.id), details=details)
    for next_task in workflows.ready_tasks(engine):
        if next_task.task_spec.lane != "approver":
            continue
        excluded = {s.strip() for s in task_properties(next_task.task_spec).get("dxlabExcludeActorsOf", "").split(",")}
        manager_steps = set(session.scalars(select(WorkflowTask.step_id).where(
            WorkflowTask.workflow_id == instance.id, WorkflowTask.lane == "lab_manager",
            WorkflowTask.status == "completed")))
        eligible_events = [e for e in events_for(session, "workflow", str(instance.id))
                           if e.details.get("step_id") in excluded | manager_steps]
        escalate(instance, next_task.data, eligible_events)
        workflows.save_engine(instance, engine)
    synchronize(session, instance, engine)
    session.flush()
    return instance
