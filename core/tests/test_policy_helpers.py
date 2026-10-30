# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

import json
from types import SimpleNamespace

from dxlab_core.workflows.authority import actor_has_authority, escalate, next_authority
from dxlab_core.workflows.privacy import mask_personal_data


def instance(files):
    return SimpleNamespace(definition=SimpleNamespace(files=[
        SimpleNamespace(path=path, content=content) for path, content in files.items()
    ]))


def test_personal_schema_masks_nested_arrays_and_references():
    schema = {"$defs": {"contact": {"type": "object", "properties": {
        "phone": {"x-personal-data": True}, "label": {"type": "string"}}},
        "secret": {"x-personal-data": True}},
        "properties": {"contacts": {"type": "array", "items": {"$ref": "#/$defs/contact"}},
                       "private": {"$ref": "#/$defs/secret"}}}
    workflow = instance({"report-schema.json": json.dumps(schema).encode()})
    original = {"contacts": [{"phone": "secret", "label": "work"}], "private": "secret", "public": 1}
    assert mask_personal_data(workflow, original) == {"contacts": [{"label": "work"}], "public": 1}
    assert original["contacts"][0]["phone"] == "secret"


def test_escalation_follows_dmn_outputs_without_fixed_amounts():
    dmn = b'''<definitions><decisionTable>
      <output name="approval_required"/><output name="approver_role"/>
      <output name="approval_scope"/><output name="approval_limit_vnd"/>
      <rule><outputEntry><text>True</text></outputEntry><outputEntry><text>"local"</text></outputEntry><outputEntry><text>"faculty"</text></outputEntry><outputEntry><text>7</text></outputEntry></rule>
      <rule><outputEntry><text>True</text></outputEntry><outputEntry><text>"higher"</text></outputEntry><outputEntry><text>"school"</text></outputEntry><outputEntry><text>42</text></outputEntry></rule>
    </decisionTable></definitions>'''
    workflow = instance({"rules.dmn": dmn})
    assert next_authority(workflow, "local")["approver_role"] == "higher"
    assert next_authority(workflow, "higher") is None
    event = SimpleNamespace(actor_roles=[{"role": "local", "unit": "/org/faculty"}])
    assert actor_has_authority(event, "local", "/org/faculty/room")
    assert not actor_has_authority(event, "local", "/org/other/room")
    data = {"approver_role": "local", "approval_scope": "faculty",
            "owner_faculty": "/org/faculty", "owner_school": "/org"}
    escalate(workflow, data, [event])
    assert data["approver_role"] == "higher"
    assert data["approval_limit_vnd"] == 42


def test_bound_room_overrides_untrusted_value(monkeypatch):
    from dxlab_core.records import service
    from dxlab_core.workflows.bindings import apply_record_bindings

    monkeypatch.setattr(service, "get_record", lambda *_: SimpleNamespace(
        data={"org_path": "/org/school/faculty/room"}))
    data = {"room_id": "room", "room_unit": "/org/forged"}
    metadata = {"record_bindings": [{"type": "room", "key_field": "room_id",
                                     "fields": {"org_path": "room_unit"}}]}
    apply_record_bindings(None, "app", metadata, data)
    assert data["room_unit"] == "/org/school/faculty/room"
    assert data["owner_faculty"] == "/org/school/faculty"
    assert data["owner_school"] == "/org/school"


def test_export_requires_auditor_and_reason_without_logging_data(monkeypatch):
    import pytest
    from dxlab_core.auth.principal import Principal, RoleAssignment
    from dxlab_core.errors import ApiError
    from dxlab_core.workflows import privacy

    events = []
    monkeypatch.setattr(privacy, "record", lambda *args, **kwargs: events.append(kwargs))
    auditor = Principal("audit", "Audit", (RoleAssignment("internal_auditor", "/org/audit"),))
    other = Principal("other", "Other", ())
    workflow = SimpleNamespace(id="id", data={"phone": "sensitive"})
    with pytest.raises(ApiError) as denied:
        privacy.export_personal_data(None, other, workflow, "kiểm tra")
    assert denied.value.code == "FORBIDDEN_PERSONAL_DATA"
    with pytest.raises(ApiError):
        privacy.export_personal_data(None, auditor, workflow, " ")
    assert privacy.export_personal_data(None, auditor, workflow, "kiểm tra") == workflow.data
    assert events[0]["details"] == {"reason": "kiểm tra"}


def test_scope_sod_and_admin_are_enforced(monkeypatch):
    import pytest
    from dxlab_core.auth.principal import Principal, RoleAssignment
    from dxlab_core.errors import ApiError
    from dxlab_core.workflows import access

    workflow = SimpleNamespace(id="id", created_by="reporter", data={
        "room_unit": "/org/school/faculty/room", "owner_faculty": "/org/school/faculty",
        "approval_scope": "faculty", "approver_role": "faculty_head"})
    task = SimpleNamespace(task_spec=SimpleNamespace(lane="approver", extensions={"properties": {}}))
    monkeypatch.setattr(access, "events_for", lambda *_: [])
    outsider = Principal("other", "Other", (RoleAssignment("faculty_head", "/org/other/faculty"),))
    with pytest.raises(ApiError) as denied:
        access.authorize_task(None, outsider, workflow, task)
    assert denied.value.code == "FORBIDDEN_SCOPE"
    admin = Principal("admin", "Admin", (RoleAssignment("system_admin", "/org"),))
    with pytest.raises(ApiError) as denied:
        access.authorize_task(None, admin, workflow, task)
    assert denied.value.code == "FORBIDDEN_ROLE"
    task.task_spec.extensions = {"properties": {"dxlabExcludeActorsOf": "repair"}}
    monkeypatch.setattr(access, "events_for", lambda *_: [
        SimpleNamespace(actor="technician", details={"step_id": "repair"})])
    technician = Principal("technician", "Technician", (RoleAssignment("it_technician", "/org/it"),))
    with pytest.raises(ApiError) as denied:
        access.authorize_task(None, technician, workflow, task)
    assert denied.value.code == "FORBIDDEN_SOD"


def test_personal_marker_inside_conditional_schema_is_still_masked():
    schema = {"properties": {"kind": {"type": "string"}},
              "if": {"properties": {"kind": {"const": "a"}}},
              "then": {"properties": {"phone": {"type": "string", "x-personal-data": True}}},
              "else": {"properties": {"email": {"type": "string", "x-personal-data": True}}}}
    workflow = instance({"report-schema.json": json.dumps(schema).encode()})

    masked = mask_personal_data(workflow, {"kind": "a", "phone": "0901234567", "email": "a@b.vn"})

    assert masked == {"kind": "a"}


def test_escalation_reads_arithmetic_outputs_like_the_dmn_engine_does():
    dmn = b'''<definitions><decisionTable>
      <output name="approval_required"/><output name="approver_role"/>
      <output name="approval_scope"/><output name="approval_limit_vnd"/>
      <rule><outputEntry><text>True</text></outputEntry><outputEntry><text>"local"</text></outputEntry><outputEntry><text>"faculty"</text></outputEntry><outputEntry><text>5 * 1000000</text></outputEntry></rule>
      <rule><outputEntry><text>True</text></outputEntry><outputEntry><text>"higher"</text></outputEntry><outputEntry><text>"school"</text></outputEntry><outputEntry><text>20 * 1000000</text></outputEntry></rule>
    </decisionTable></definitions>'''
    workflow = instance({"rules.dmn": dmn})
    event = SimpleNamespace(actor_roles=[{"role": "local", "unit": "/org/faculty"}])
    data = {"approver_role": "local", "approval_scope": "faculty", "owner_faculty": "/org/faculty"}

    escalate(workflow, data, [event])

    assert (data["approver_role"], data["approval_limit_vnd"]) == ("higher", 20_000_000)
