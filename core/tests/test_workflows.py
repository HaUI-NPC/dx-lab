# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

"""Phiếu giữ nguyên luật khi phiên bản mới được duyệt; form không cho giả mạo output luật."""
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
