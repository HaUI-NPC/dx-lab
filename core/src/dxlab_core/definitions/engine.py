# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

"""Đọc gói ứng dụng thành spec SpiffWorkflow. Dùng chung cho validator, `/api/definitions` và runtime."""

import json
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from typing import Any

from SpiffWorkflow.bpmn.specs.bpmn_process_spec import BpmnProcessSpec
from SpiffWorkflow.bpmn.specs.bpmn_task_spec import BpmnTaskSpec
from SpiffWorkflow.spiff.parser.process import SpiffBpmnParser

PROCESS_MODEL = "process_model.json"
FORM_SCHEMA_PROPERTY = "formJsonSchemaFilename"
FORM_UI_SCHEMA_PROPERTY = "formUiSchemaFilename"
EXCLUDE_ACTORS_PROPERTY = "dxlabExcludeActorsOf"

Files = Mapping[str, bytes]


@dataclass(frozen=True)
class ProcessModel:
    display_name: str
    primary_file_name: str
    primary_process_id: str


@dataclass(frozen=True)
class LoadedPackage:
    model: ProcessModel
    spec: BpmnProcessSpec
    subprocess_specs: dict[str, BpmnProcessSpec]


def read_process_model(files: Files) -> ProcessModel:
    data = json.loads(files[PROCESS_MODEL])
    return ProcessModel(
        display_name=str(data.get("display_name") or data["primary_process_id"]),
        primary_file_name=str(data["primary_file_name"]),
        primary_process_id=str(data["primary_process_id"]),
    )


def load_package(files: Files) -> LoadedPackage:
    """Parse mọi BPMN/DMN của gói. Ném lỗi của SpiffWorkflow nếu gói không parse được."""
    model = read_process_model(files)
    parser = SpiffBpmnParser()
    for path, content in sorted(files.items()):
        if path.endswith(".bpmn"):
            parser.add_bpmn_str(content, filename=path)
        elif path.endswith(".dmn"):
            parser.add_dmn_str(content, filename=path)
    spec = parser.get_spec(model.primary_process_id)
    subprocess_specs = parser.get_subprocess_specs(model.primary_process_id)
    return LoadedPackage(model=model, spec=spec, subprocess_specs=subprocess_specs)


def task_properties(task_spec: Any) -> dict[str, str]:
    extensions = getattr(task_spec, "extensions", None) or {}
    return dict(extensions.get("properties") or {})


def user_task_specs(spec: BpmnProcessSpec) -> Iterator[BpmnTaskSpec]:
    for task_spec in spec.task_specs.values():
        if getattr(task_spec, "manual", False):
            yield task_spec


def first_user_task(spec: BpmnProcessSpec) -> BpmnTaskSpec | None:
    """Bước người dùng đầu tiên đi được từ điểm bắt đầu: form khởi tạo của ứng dụng."""
    seen: set[str] = set()
    queue = [spec.start]
    while queue:
        task_spec = queue.pop(0)
        if task_spec.name in seen:
            continue
        seen.add(task_spec.name)
        if getattr(task_spec, "manual", False):
            return task_spec
        queue.extend(task_spec.outputs)
    return None


def form_of(task_spec: Any, files: Files) -> tuple[dict[str, Any], dict[str, Any]]:
    """`(schema, uischema)` của một bước người dùng; bước không có form trả `({}, {})`."""
    props = task_properties(task_spec)
    schema_file = props.get(FORM_SCHEMA_PROPERTY)
    ui_file = props.get(FORM_UI_SCHEMA_PROPERTY)
    schema = json.loads(files[schema_file]) if schema_file else {}
    uischema = json.loads(files[ui_file]) if ui_file else {}
    return schema, uischema
