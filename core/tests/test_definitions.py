# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

"""`/api/definitions`: 4 cửa kiểm soát (docs/ARCHITECTURE.md mục 7, docs/AUTHZ.md mục 4)."""

import json
from collections.abc import Callable

import pytest
from fastapi.testclient import TestClient

from dxlab_core.cli import main as dxlab
from dxlab_core.definitions.validator import validate_package

Headers = Callable[..., dict[str, str]]

QT_SON = ("qt.son", ["/haui/tt-cntt/process_admin"])
CSVC_LAN = ("csvc.lan", ["/haui/ban-csvc/facility_officer", "/haui/ban-csvc/rule_admin"])
PGD_MINH = ("pgd.minh", ["/haui/ban-giam-doc/vice_president", "/haui/ban-giam-doc/process_owner"])

BPMN = """<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"
    xmlns:spiffworkflow="http://spiffworkflow.org/bpmn/schema/1.0/core" id="defs" targetNamespace="dxlab">
  <bpmn:process id="mini" isExecutable="true">
    <bpmn:laneSet id="ls">
      <bpmn:lane id="lane_reporter" name="reporter"><bpmn:flowNodeRef>start</bpmn:flowNodeRef><bpmn:flowNodeRef>report</bpmn:flowNodeRef></bpmn:lane>
      <bpmn:lane id="lane_system" name="system"><bpmn:flowNodeRef>triage</bpmn:flowNodeRef><bpmn:flowNodeRef>gw</bpmn:flowNodeRef><bpmn:flowNodeRef>done</bpmn:flowNodeRef></bpmn:lane>
      <bpmn:lane id="lane_approver" name="approver"><bpmn:flowNodeRef>approve</bpmn:flowNodeRef><bpmn:flowNodeRef>approved</bpmn:flowNodeRef></bpmn:lane>
    </bpmn:laneSet>
    <bpmn:startEvent id="start"><bpmn:outgoing>f1</bpmn:outgoing></bpmn:startEvent>
    <bpmn:userTask id="report" name="Báo hỏng">
      <bpmn:extensionElements><spiffworkflow:properties>
        <spiffworkflow:property name="formJsonSchemaFilename" value="report-schema.json" />
        <spiffworkflow:property name="formUiSchemaFilename" value="report-uischema.json" />
      </spiffworkflow:properties></bpmn:extensionElements>
      <bpmn:incoming>f1</bpmn:incoming><bpmn:outgoing>f2</bpmn:outgoing>
    </bpmn:userTask>
    <bpmn:businessRuleTask id="triage" name="Xếp ưu tiên">
      <bpmn:extensionElements><spiffworkflow:calledDecisionId>triage</spiffworkflow:calledDecisionId></bpmn:extensionElements>
      <bpmn:incoming>f2</bpmn:incoming><bpmn:outgoing>f3</bpmn:outgoing>
    </bpmn:businessRuleTask>
    <bpmn:exclusiveGateway id="gw" default="f_low"><bpmn:incoming>f3</bpmn:incoming><bpmn:outgoing>f_high</bpmn:outgoing><bpmn:outgoing>f_low</bpmn:outgoing></bpmn:exclusiveGateway>
    <bpmn:userTask id="approve" name="Duyệt">
      <bpmn:extensionElements><spiffworkflow:properties>
        <spiffworkflow:property name="formJsonSchemaFilename" value="approve-schema.json" />
      </spiffworkflow:properties></bpmn:extensionElements>
      <bpmn:incoming>f_high</bpmn:incoming><bpmn:outgoing>f5</bpmn:outgoing>
    </bpmn:userTask>
    <bpmn:endEvent id="approved"><bpmn:incoming>f5</bpmn:incoming></bpmn:endEvent>
    <bpmn:endEvent id="done"><bpmn:incoming>f_low</bpmn:incoming></bpmn:endEvent>
    <bpmn:sequenceFlow id="f1" sourceRef="start" targetRef="report" />
    <bpmn:sequenceFlow id="f2" sourceRef="report" targetRef="triage" />
    <bpmn:sequenceFlow id="f3" sourceRef="triage" targetRef="gw" />
    <bpmn:sequenceFlow id="f_high" sourceRef="gw" targetRef="approve">
      <bpmn:conditionExpression>{condition}</bpmn:conditionExpression>
    </bpmn:sequenceFlow>
    <bpmn:sequenceFlow id="f_low" sourceRef="gw" targetRef="done" />
    <bpmn:sequenceFlow id="f5" sourceRef="approve" targetRef="approved" />
  </bpmn:process>
</bpmn:definitions>
"""

DMN = """<?xml version="1.0" encoding="UTF-8"?>
<definitions xmlns="https://www.omg.org/spec/DMN/20191111/MODEL/" id="d" name="triage" namespace="dxlab">
  <decision id="triage" name="Xếp ưu tiên">
    <decisionTable id="t" hitPolicy="FIRST">
      <input id="i1" label="Chi phí"><inputExpression id="ie1" typeRef="integer"><text>cost</text></inputExpression></input>
      <output id="o1" name="{output}" typeRef="string" />
      <rule id="r1"><inputEntry id="a1"><text>&gt; {threshold}</text></inputEntry><outputEntry id="b1"><text>"high"</text></outputEntry></rule>
      <rule id="r2"><inputEntry id="a2"><text>-</text></inputEntry><outputEntry id="b2"><text>"low"</text></outputEntry></rule>
    </decisionTable>
  </decision>
</definitions>
"""


def package(
    *, condition: str = 'level == "high"', threshold: str = "2000000", output: str = "level"
) -> dict[str, bytes]:
    report = {"type": "object", "required": ["cost"], "properties": {"cost": {"type": "integer", "title": "Chi phí"}}}
    approve = {"type": "object", "properties": {"ok": {"type": "boolean"}}}
    return {
        "process_model.json": json.dumps(
            {"display_name": "Ứng dụng thử", "primary_file_name": "mini.bpmn", "primary_process_id": "mini"}
        ).encode(),
        "mini.bpmn": BPMN.replace("{condition}", condition).encode(),
        "triage.dmn": DMN.replace("{threshold}", threshold).replace("{output}", output).encode(),
        "report-schema.json": json.dumps(report).encode(),
        "report-uischema.json": b'{"ui:order": ["cost"]}',
        "approve-schema.json": json.dumps(approve).encode(),
        "eval/accuracy.py": b"print('bo qua khi nap')",
    }


def upload(client: TestClient, headers: dict[str, str], files: dict[str, bytes], app_id: str = "mini"):
    parts = [("files", (path, content, "application/octet-stream")) for path, content in files.items()]
    return client.post(f"/api/definitions/{app_id}/versions", headers=headers, files=parts)


def test_valid_package_passes_validator() -> None:
    assert validate_package(package()) == []


@pytest.mark.parametrize(
    "condition",
    ["__import__('os').system('echo PWNED')", "open('/etc/passwd').read() != ''", "level.upper() == 'HIGH'"],
    ids=["os-system", "mo-tep", "goi-phuong-thuc"],
)
def test_code_in_gateway_condition_rejected(condition: str) -> None:
    issues = validate_package(package(condition=condition))

    assert [(i.element, "không được phép" in i.message) for i in issues] == [("f_high", True)]


def test_script_task_rejected() -> None:
    files = package()
    files["mini.bpmn"] = files["mini.bpmn"].replace(
        b'<bpmn:endEvent id="done">',
        b'<bpmn:scriptTask id="evil"><bpmn:script>import os</bpmn:script></bpmn:scriptTask><bpmn:endEvent id="done">',
    )

    messages = [i.message for i in validate_package(files)]

    assert "Phần tử bpmn:scriptTask không được phép." in messages


def test_code_in_dmn_cell_rejected() -> None:
    issues = validate_package(package(threshold="__import__('os').getpid()"))

    assert len(issues) == 1 and issues[0].file == "triage.dmn"


def test_dmn_arithmetic_allowed() -> None:
    assert validate_package(package(threshold="2000000 * 1.1")) == []


def test_user_task_without_lane_rejected() -> None:
    files = package()
    files["mini.bpmn"] = files["mini.bpmn"].replace(b"<bpmn:flowNodeRef>approve</bpmn:flowNodeRef>", b"")

    assert [i.message for i in validate_package(files)] == ["Bước người dùng phải nằm trong một lane."]


def test_missing_form_rejected() -> None:
    files = package()
    del files["approve-schema.json"]

    assert [str(i) for i in validate_package(files)] == ["mini.bpmn [approve]: Form approve-schema.json không có trong gói."]


def test_new_version_must_keep_dmn_output_columns() -> None:
    issues = validate_package(package(output="priority"), previous=package())

    assert [i.element for i in issues] == ["triage"]


def test_publish_activate_and_versions(client: TestClient, headers_for: Headers) -> None:
    created = upload(client, headers_for(*QT_SON), package())

    assert created.status_code == 201, created.text
    assert created.json()["version"] == 1
    assert created.json()["status"] == "pending_approval"
    assert "eval/accuracy.py" not in [f["path"] for f in created.json()["files"]]
    assert client.get("/api/definitions/mini/start-form", headers=headers_for(*QT_SON)).status_code == 404

    activated = client.post("/api/definitions/mini/versions/1/activate", headers=headers_for(*PGD_MINH))

    assert activated.status_code == 200
    assert activated.json()["status"] == "active"
    form = client.get("/api/definitions/mini/start-form", headers=headers_for("sv.an")).json()
    assert (form["version"], form["step_id"], form["step_name"]) == (1, "report", "Báo hỏng")
    assert form["schema"]["required"] == ["cost"]
    assert form["uischema"] == {"ui:order": ["cost"]}
    apps = client.get("/api/definitions", headers=headers_for("sv.an")).json()
    assert apps == {"items": [{"app_id": "mini", "display_name": "Ứng dụng thử", "version": 1, "status": "active"}],
                    "total": 1}


def test_rule_admin_may_only_change_dmn(client: TestClient, headers_for: Headers) -> None:
    upload(client, headers_for(*QT_SON), package())
    client.post("/api/definitions/mini/versions/1/activate", headers=headers_for(*PGD_MINH))

    bpmn_change = upload(client, headers_for(*CSVC_LAN), package(condition='level != "low"'))
    dmn_change = upload(client, headers_for(*CSVC_LAN), package(threshold="5000000"))

    assert bpmn_change.status_code == 403
    assert bpmn_change.json()["error"]["details"]["changed_kinds"] == ["bpmn"]
    assert dmn_change.status_code == 201
    assert dmn_change.json()["version"] == 2


def test_new_version_applies_only_after_owner_approval(client: TestClient, headers_for: Headers) -> None:
    upload(client, headers_for(*QT_SON), package())
    client.post("/api/definitions/mini/versions/1/activate", headers=headers_for(*PGD_MINH))
    upload(client, headers_for(*CSVC_LAN), package(threshold="5000000"))

    before = client.get("/api/definitions/mini/start-form", headers=headers_for("sv.an")).json()["version"]
    client.post("/api/definitions/mini/versions/2/activate", headers=headers_for(*PGD_MINH))
    after = client.get("/api/definitions/mini/start-form", headers=headers_for("sv.an")).json()["version"]
    versions = client.get("/api/definitions/mini/versions", headers=headers_for("sv.an")).json()["items"]

    assert (before, after) == (1, 2)
    assert [(v["version"], v["status"]) for v in versions] == [(2, "active"), (1, "superseded")]


def test_publisher_cannot_activate_own_version(client: TestClient, headers_for: Headers) -> None:
    both_roles = headers_for("qt.son", ["/haui/tt-cntt/process_admin", "/haui/ban-giam-doc/process_owner"])
    upload(client, both_roles, package())

    response = client.post("/api/definitions/mini/versions/1/activate", headers=both_roles)

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN_SOD"
    assert response.json()["error"]["details"] == {"layer": 4, "rule": "SoD-5"}


def test_rejected_package_lists_errors_and_creates_nothing(client: TestClient, headers_for: Headers) -> None:
    response = upload(client, headers_for(*QT_SON), package(condition="__import__('os').system('id')"))

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "DEFINITION_REJECTED"
    assert response.json()["error"]["details"]["errors"][0]["element"] == "f_high"
    assert client.get("/api/definitions/mini/versions", headers=headers_for(*QT_SON)).json()["total"] == 0


def test_reporter_cannot_publish_and_admin_cannot_activate(client: TestClient, headers_for: Headers) -> None:
    assert upload(client, headers_for("sv.an"), package()).status_code == 403
    upload(client, headers_for(*QT_SON), package())
    admin = client.post("/api/definitions/mini/versions/1/activate", headers=headers_for("admin.dx", ["/haui/tt-cntt/system_admin"]))

    assert admin.status_code == 403
    assert admin.json()["error"]["details"]["rule"] == "SoD-4"


def test_publish_and_activate_are_audited(app, client: TestClient, headers_for: Headers) -> None:
    from dxlab_core.audit.service import events_for

    upload(client, headers_for(*QT_SON), package())
    client.post("/api/definitions/mini/versions/1/activate", headers=headers_for(*PGD_MINH))
    with app.state.sessionmaker() as session:
        history = [(e.actor, e.action, e.details["version"]) for e in events_for(session, "definition", "mini")]

    assert history == [("qt.son", "definition.publish", 1), ("pgd.minh", "definition.activate", 1)]


def test_cli_validate_reports_each_app(tmp_path, capsys: pytest.CaptureFixture[str]) -> None:
    for name, files in {"good": package(), "bad": package(condition="__import__('os')")}.items():
        for path, content in files.items():
            target = tmp_path / name / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)

    code = dxlab(["validate", str(tmp_path)])

    out = capsys.readouterr().out
    assert code == 1
    assert "✓ good: hợp lệ" in out
    assert "✗ bad: 1 lỗi" in out
