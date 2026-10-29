# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

import json
from types import SimpleNamespace

from dxlab_core.workflows.authority import actor_has_authority, next_authority
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
