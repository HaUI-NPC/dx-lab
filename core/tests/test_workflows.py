# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

"""Phiếu giữ nguyên luật khi phiên bản mới được duyệt; form không cho giả mạo output luật."""
import json
import uuid
from test_definitions import PGD_MINH, QT_SON, package, upload


def activate(client, headers_for, files):
    result = upload(client, headers_for(*QT_SON), files)
    assert result.status_code == 201, result.text
    version = result.json()["version"]
    result = client.post(f"/api/definitions/mini/versions/{version}/activate", headers=headers_for(*PGD_MINH))
    assert result.status_code == 200, result.text


def test_existing_instance_keeps_serialized_definition(client, headers_for):
    activate(client, headers_for, package(threshold="2000000"))
    reporter = headers_for("sv.an")
    old = client.post("/api/workflows", headers=reporter, json={"app_id": "mini", "data": {"cost": 3500000}})
    assert old.status_code == 201, old.text
    activate(client, headers_for, package(threshold="5000000"))
    new = client.post("/api/workflows", headers=reporter, json={"app_id": "mini", "data": {"cost": 3500000}})
    assert new.status_code == 201, new.text
    persisted = client.get(f"/api/workflows/{old.json()['workflow_id']}", headers=reporter)
    assert (persisted.json()["version"], persisted.json()["status"], persisted.json()["data"]["level"]) == (1, "approve", "high")
    assert (new.json()["version"], new.json()["status"]) == (2, "done")


def test_cannot_inject_server_outputs_or_read_another_report(client, headers_for):
    activate(client, headers_for, package())
    reporter = headers_for("sv.an")
    injected = client.post("/api/workflows", headers=reporter,
                           json={"app_id": "mini", "data": {"cost": 3500000, "level": "low"}})
    assert injected.status_code == 422
    created = client.post("/api/workflows", headers=reporter, json={"app_id": "mini", "data": {"cost": 3500000}})
    denied = client.get(f"/api/workflows/{created.json()['workflow_id']}", headers=headers_for("gv.binh"))
    assert denied.status_code == 403
    assert denied.json()["error"]["code"] == "FORBIDDEN_SCOPE"


def task_package(exclude_reporter=False):
    files = package()
    files["mini.bpmn"] = files["mini.bpmn"].replace(b'name="approver"', b'name="it_technician"')
    if exclude_reporter:
        files["mini.bpmn"] = files["mini.bpmn"].replace(
            b'<spiffworkflow:property name="formJsonSchemaFilename" value="approve-schema.json" />',
            b'<spiffworkflow:property name="formJsonSchemaFilename" value="approve-schema.json" />'
            b'<spiffworkflow:property name="dxlabExcludeActorsOf" value="report" />')
    metadata = json.loads(files["process_model.json"])
    metadata["data_defaults"] = {"room_unit": "/haui/tt-cntt"}
    files["process_model.json"] = json.dumps(metadata).encode()
    return files


def test_queue_scope_validation_transition_and_duplicate_completion(client, headers_for):
    activate(client, headers_for, task_package())
    created = client.post("/api/workflows", headers=headers_for("sv.an"),
                          json={"app_id": "mini", "data": {"cost": 3500000}}).json()
    technician = headers_for("ktv.cuong", ["/haui/tt-cntt/it_technician"])
    outsider = headers_for("other", ["/haui/sict/it_technician"])
    assert client.get("/api/tasks", headers=outsider).json() == {"items": [], "total": 0}
    queue = client.get("/api/tasks", headers=technician).json()
    task_id = queue["items"][0]["task_id"]
    assert queue["total"] == 1
    wrong_scope = client.post(f"/api/tasks/{task_id}/complete", headers=outsider, json={"data": {"ok": True}})
    assert wrong_scope.status_code == 403
    assert wrong_scope.json()["error"]["code"] == "FORBIDDEN_SCOPE"
    invalid = client.post(f"/api/tasks/{task_id}/complete", headers=technician, json={"data": {"level": "low"}})
    assert invalid.status_code == 422
    completed = client.post(f"/api/tasks/{task_id}/complete", headers=technician, json={"data": {"ok": True}})
    assert completed.status_code == 200, completed.text
    assert completed.json()["status"] == "approved"
    repeated = client.post(f"/api/tasks/{task_id}/complete", headers=technician, json={"data": {"ok": True}})
    assert repeated.status_code == 409
    assert client.get("/api/tasks", headers=technician).json()["total"] == 0
    history = client.get(f"/api/workflows/{created['workflow_id']}", headers=headers_for("sv.an")).json()["history"]
    assert [(e["action"], e["actor"]) for e in history] == [("report.create", "sv.an"), ("task.complete", "ktv.cuong")]


def test_actor_exclusion_applies_to_direct_completion_not_only_queue(client, headers_for):
    activate(client, headers_for, task_package(exclude_reporter=True))
    technician = headers_for("ktv.cuong", ["/haui/tt-cntt/it_technician"])
    created = client.post("/api/workflows", headers=technician,
                          json={"app_id": "mini", "data": {"cost": 3500000}})
    assert created.status_code == 201
    assert client.get("/api/tasks", headers=technician).json()["total"] == 0
    another = headers_for("ktv.other", ["/haui/tt-cntt/it_technician"])
    task_id = client.get("/api/tasks", headers=another).json()["items"][0]["task_id"]
    denied = client.post(f"/api/tasks/{task_id}/complete", headers=technician, json={"data": {"ok": True}})
    assert denied.status_code == 403
    assert denied.json()["error"]["code"] == "FORBIDDEN_SOD"


def test_restore_keeps_task_data_when_json_object_order_is_lost(client, headers_for, app):
    # JSONB của PostgreSQL xếp lại khóa theo chữ cái; Spiff cần thứ tự cha trước con để dựng lại dữ liệu.
    from dxlab_core.workflows import service

    activate(client, headers_for, task_package())
    created = client.post("/api/workflows", headers=headers_for("sv.an"),
                          json={"app_id": "mini", "data": {"cost": 3500000}}).json()
    with app.state.sessionmaker() as session:
        instance = service.find(session, uuid.UUID(created["workflow_id"]))
        tasks = instance.engine_state["tasks"]
        instance.engine_state = {**instance.engine_state, "tasks": dict(reversed(list(tasks.items())))}
        restored = service.restore(instance)
        (task,) = service.ready_tasks(restored)
        assert (task.data["cost"], task.data["level"]) == (3500000, "high")


def test_detail_titles_form_fields_but_not_rule_outputs(client, headers_for):
    activate(client, headers_for, task_package())
    created = client.post("/api/workflows", headers=headers_for("sv.an"),
                          json={"app_id": "mini", "data": {"cost": 3500000}}).json()

    detail = client.get(f"/api/workflows/{created['workflow_id']}", headers=headers_for("sv.an")).json()

    assert detail["data"]["level"] == "high"
    assert detail["field_titles"] == {"cost": "Chi phí"}


def test_only_approver_steps_record_authority_basis_and_signing_type(client, headers_for, app):
    from dxlab_core.audit.service import events_for

    files = task_package()
    metadata = json.loads(files["process_model.json"])
    metadata["data_defaults"] |= {"authority_basis": "GĐ-X", "signing_type": "direct"}
    files["process_model.json"] = json.dumps(metadata).encode()
    activate(client, headers_for, files)
    created = client.post("/api/workflows", headers=headers_for("sv.an"),
                          json={"app_id": "mini", "data": {"cost": 3500000}}).json()
    technician = headers_for("ktv.cuong", ["/haui/tt-cntt/it_technician"])
    task_id = client.get("/api/tasks", headers=technician).json()["items"][0]["task_id"]
    assert client.post(f"/api/tasks/{task_id}/complete", headers=technician, json={"data": {"ok": True}}).status_code == 200

    with app.state.sessionmaker() as session:
        (event,) = [e for e in events_for(session, "workflow", created["workflow_id"]) if e.action == "task.complete"]
    assert "authority_basis" not in event.details and "signing_type" not in event.details


def test_form_errors_point_at_the_field_and_are_vietnamese(client, headers_for):
    activate(client, headers_for, task_package())
    reporter = headers_for("sv.an")

    missing = client.post("/api/workflows", headers=reporter, json={"app_id": "mini", "data": {}})
    wrong_type = client.post("/api/workflows", headers=reporter, json={"app_id": "mini", "data": {"cost": "nhiều"}})

    assert missing.status_code == wrong_type.status_code == 422
    assert missing.json()["error"]["details"]["errors"] == [{"path": "cost", "message": "Thiếu trường bắt buộc."}]
    assert wrong_type.json()["error"]["details"]["errors"] == [{"path": "cost", "message": "Sai kiểu dữ liệu."}]


AUTHORITY_DMN = """<?xml version="1.0" encoding="UTF-8"?>
<definitions xmlns="https://www.omg.org/spec/DMN/20191111/MODEL/" id="d" name="authority" namespace="dxlab">
  <decision id="triage" name="Thẩm quyền">
    <decisionTable id="t" hitPolicy="FIRST">
      <input id="i1" label="Chi phí"><inputExpression id="ie1" typeRef="integer"><text>cost</text></inputExpression></input>
      <output id="o1" name="approval_required" typeRef="boolean" />
      <output id="o2" name="approver_role" typeRef="string" />
      <output id="o3" name="approval_scope" typeRef="string" />
      <output id="o4" name="approval_limit_vnd" typeRef="integer" />
      <rule id="r1"><inputEntry id="a1"><text>&lt;= 5000000</text></inputEntry>
        <outputEntry id="b1"><text>True</text></outputEntry><outputEntry id="b2"><text>"faculty_head"</text></outputEntry>
        <outputEntry id="b3"><text>"faculty"</text></outputEntry><outputEntry id="b4"><text>5 * 1000000</text></outputEntry></rule>
      <rule id="r2"><inputEntry id="a2"><text>-</text></inputEntry>
        <outputEntry id="c1"><text>True</text></outputEntry><outputEntry id="c2"><text>"school_head"</text></outputEntry>
        <outputEntry id="c3"><text>"school"</text></outputEntry><outputEntry id="c4"><text>20 * 1000000</text></outputEntry></rule>
    </decisionTable>
  </decision>
</definitions>
"""


def approval_package():
    """`report → bảng thẩm quyền → duyệt`: bước duyệt xuất hiện ngay sau khi tạo phiếu, không qua bước trung gian."""
    files = package()
    files["mini.bpmn"] = files["mini.bpmn"].replace(b'name="approver"', b'name="approver"').replace(
        b'<spiffworkflow:property name="formJsonSchemaFilename" value="approve-schema.json" />',
        b'<spiffworkflow:property name="formJsonSchemaFilename" value="approve-schema.json" />'
        b'<spiffworkflow:property name="dxlabExcludeActorsOf" value="report" />')
    files["triage.dmn"] = AUTHORITY_DMN.encode()
    files["mini.bpmn"] = files["mini.bpmn"].replace(b'level == "high"', b"approval_required == True")
    metadata = json.loads(files["process_model.json"])
    metadata["data_defaults"] = {"owner_faculty": "/haui/sict/khmt", "owner_school": "/haui/sict"}
    files["process_model.json"] = json.dumps(metadata).encode()
    return files


def test_creator_holding_the_approving_role_is_escalated_at_creation(client, headers_for):
    activate(client, headers_for, approval_package())
    head = ("tk.hai", ["/haui/sict/khmt/faculty_head"])
    school = ("ht.khanh", ["/haui/sict/school_head"])

    created = client.post("/api/workflows", headers=headers_for(*head), json={"app_id": "mini", "data": {"cost": 3500000}})

    assert created.status_code == 201, created.text
    assert client.get("/api/tasks", headers=headers_for(*head)).json()["total"] == 0
    queue = client.get("/api/tasks", headers=headers_for(*school)).json()
    assert [t["workflow_id"] for t in queue["items"]] == [created.json()["workflow_id"]]
    data = client.get(f"/api/workflows/{created.json()['workflow_id']}", headers=headers_for(*head)).json()["data"]
    assert (data["approver_role"], data["approval_limit_vnd"]) == ("school_head", 20_000_000)
