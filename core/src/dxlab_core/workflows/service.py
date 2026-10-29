# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

"""Runtime Spiff: chỉ dữ liệu form được ghi; trạng thái và spec luôn do server giữ."""
import json
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker
from sqlalchemy import select
from sqlalchemy.orm import Session
from SpiffWorkflow.bpmn import BpmnWorkflow
from SpiffWorkflow.bpmn.serializer.workflow import BpmnWorkflowSerializer
from SpiffWorkflow.spiff.serializer.config import SPIFF_CONFIG
from SpiffWorkflow.util.task import TaskState

from dxlab_core.audit.service import events_for, record
from dxlab_core.auth.principal import Principal
from dxlab_core.definitions.engine import form_of
from dxlab_core.definitions.service import active_version, files_of, loaded_package
from dxlab_core.errors import ApiError, NotFound
from dxlab_core.workflows.models import Workflow

SERIALIZER = BpmnWorkflowSerializer(BpmnWorkflowSerializer.configure(SPIFF_CONFIG))


def validate_form(schema: dict, data: dict) -> dict:
    # Không cho client chèn output DMN hay trạng thái phân quyền ngoài form.
    unknown = set(data) - set(schema.get("properties", {}))
    issues = [{"field": k, "message": "Trường không thuộc form của bước này."} for k in sorted(unknown)]
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    issues.extend({"field": ".".join(map(str, error.absolute_path)), "message": error.message}
                  for error in validator.iter_errors(data))
    if issues:
        raise ApiError(422, "VALIDATION_FAILED", "Dữ liệu form chưa hợp lệ.", {"errors": issues})
    return dict(data)


def ready_tasks(engine: BpmnWorkflow) -> list:
    return engine.get_tasks(state=TaskState.READY, manual=True)


def save_engine(instance: Workflow, engine: BpmnWorkflow) -> None:
    ready = ready_tasks(engine)
    if ready:
        current = ready[0]
        instance.status = current.task_spec.bpmn_id
        instance.status_name = current.task_spec.bpmn_name or instance.status
        instance.data = dict(current.data)
    else:
        ends = [t for t in engine.get_tasks(state=TaskState.COMPLETED)
                if t.task_spec.__class__.__name__ in {"EndEvent", "TerminateEndEvent"}]
        last = ends[-1] if ends else engine.last_task
        instance.status = getattr(last.task_spec, "bpmn_id", None) or "completed"
        instance.status_name = getattr(last.task_spec, "bpmn_name", None) or instance.status
        instance.data = dict(engine.data)
    hours = instance.data.get("inspect_within_hours" if instance.status == "pending_assessment" else "complete_within_hours")
    instance.due_at = (instance.created_at + timedelta(hours=float(hours))) if ready and hours is not None else None
    instance.updated_at = datetime.now(UTC)
    instance.engine_state = json.loads(SERIALIZER.serialize_json(engine))


def restore(instance: Workflow) -> BpmnWorkflow:
    return SERIALIZER.deserialize_json(json.dumps(instance.engine_state))


def create(session: Session, principal: Principal, app_id: str, data: dict[str, Any]) -> Workflow:
    definition = active_version(session, app_id)
    package = loaded_package(definition)
    engine = BpmnWorkflow(package.spec, package.subprocess_specs)
    engine.do_engine_steps()
    tasks = ready_tasks(engine)
    if len(tasks) != 1 or tasks[0].task_spec.lane != "reporter":
        raise ApiError(422, "DEFINITION_REJECTED", "Ứng dụng phải bắt đầu bằng một form của người tạo.")
    task = tasks[0]
    schema, _ = form_of(task.task_spec, files_of(definition))
    submitted = validate_form(schema, data)
    metadata = json.loads(files_of(definition)["process_model.json"])
    task.data.update(metadata.get("data_defaults", {}))
    task.data.update(submitted)
    if "data_processing_consent" in schema.get("properties", {}):
        task.data["consent_notice_version"] = schema["properties"].get("consent_notice_version", {}).get("default", "v1.0")
        task.data["consent_recorded_at"] = datetime.now(UTC).isoformat()
    task.run()
    engine.do_engine_steps()
    instance = Workflow(id=uuid.uuid4(), app_id=app_id, definition=definition,
                        created_by=principal.username, created_at=datetime.now(UTC), revision=1)
    save_engine(instance, engine)
    session.add(instance)
    session.flush()
    record(session, actor=principal, action="report.create", object_type="workflow", object_id=str(instance.id),
           details={"step_id": task.task_spec.bpmn_id, "version": definition.version})
    return instance


def find(session: Session, workflow_id: uuid.UUID, *, lock: bool = False) -> Workflow:
    query = select(Workflow).where(Workflow.id == workflow_id)
    instance = session.scalar(query.with_for_update() if lock else query)
    if instance is None:
        raise NotFound("Không có phiếu này.")
    return instance


def can_read(principal: Principal, instance: Workflow) -> bool:
    # CORE-04a chưa mở hàng đợi nghiệp vụ: chỉ chủ phiếu xem được, mặc định từ chối người khác.
    return principal.username == instance.created_by


def summary(instance: Workflow) -> dict:
    return {"workflow_id": str(instance.id), "app_id": instance.app_id,
            "version": instance.definition.version, "status": instance.status,
            "status_name": instance.status_name, "created_by": instance.created_by,
            "created_at": instance.created_at, "updated_at": instance.updated_at, "due_at": instance.due_at,
            "revision": instance.revision}


def detail(session: Session, principal: Principal, instance: Workflow) -> dict:
    if not can_read(principal, instance):
        raise ApiError(403, "FORBIDDEN_SCOPE", "Bạn không được xem phiếu này.", {"layer": 2})
    result = summary(instance)
    result["data"] = instance.data
    result["history"] = [{"actor": e.actor, "action": e.action, "step_id": e.details.get("step_id"),
                          "at": e.occurred_at, "details": e.details}
                         for e in events_for(session, "workflow", str(instance.id))]
    return result
