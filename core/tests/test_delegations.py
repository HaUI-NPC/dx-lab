# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

"""Ủy quyền TUQ. (docs/AUTHZ.md mục 9, kịch bản 7 của mục 12)."""
import json
from datetime import UTC, datetime, timedelta

from sqlalchemy import update

from test_workflows import activate, approval_package

from dxlab_core.delegations.models import Delegation

TK_HAI = ("tk.hai", ["/haui/sict/khmt/faculty_head"])
PTK_HOA = ("ptk.hoa", ["/haui/sict/khmt/faculty_deputy"])
HT_KHANH = ("ht.khanh", ["/haui/sict/school_head"])
KTV_CUONG = ("ktv.cuong", ["/haui/tt-cntt/it_technician"])
NUMBER = "GĐ-UQ-07/2026"


def tuq_package():
    """`report → bảng thẩm quyền (≤ 5 triệu: trưởng khoa; còn lại: hiệu trưởng) → duyệt`, form duyệt có hình thức ký."""
    files = approval_package()
    files["approve-schema.json"] = json.dumps({"type": "object", "properties": {
        "ok": {"type": "boolean"}, "signing_type": {"type": "string"},
        "delegation_number": {"type": "string"}, "approved_amount_vnd": {"type": "integer"}}}).encode()
    return files


def delegate(client, headers_for, who=PTK_HOA, days=7, **overrides):
    now = datetime.now(UTC)
    body = {"delegate": who[0], "role": "faculty_head", "number": NUMBER,
            "starts_at": (now - timedelta(minutes=1)).isoformat(),
            "ends_at": (now - timedelta(minutes=1) + timedelta(days=days)).isoformat()} | overrides
    return client.post("/api/delegations", headers=headers_for(*TK_HAI), json=body)


def report(client, headers_for, cost):
    created = client.post("/api/workflows", headers=headers_for("sv.an"), json={"app_id": "mini", "data": {"cost": cost}})
    assert created.status_code == 201, created.text
    return created.json()["workflow_id"]


def queue(client, headers, workflow_id):
    return [t["task_id"] for t in client.get("/api/tasks", headers=headers).json()["items"]
            if t["workflow_id"] == workflow_id]


def approve(client, headers, task_id, **data):
    return client.post(f"/api/tasks/{task_id}/complete", headers=headers, json={"data": {"ok": True, **data}})


def test_deputy_approves_within_delegators_limit_as_tuq(client, headers_for):
    activate(client, headers_for, tuq_package())
    created = delegate(client, headers_for)
    assert created.status_code == 201, created.text
    assert (created.json()["delegator"], created.json()["unit"], created.json()["status"]) == (
        "tk.hai", "/haui/sict/khmt", "active")
    workflow_id = report(client, headers_for, 3_500_000)
    hoa = headers_for(*PTK_HOA)
    [task_id] = queue(client, hoa, workflow_id)

    assert approve(client, hoa, task_id, signing_type="direct").json()["error"]["code"] == "FORBIDDEN_AUTHORITY"
    assert approve(client, hoa, task_id, signing_type="tuq", delegation_number="GĐ-UQ-99").status_code == 403
    done = approve(client, hoa, task_id, signing_type="tuq", delegation_number=NUMBER, approved_amount_vnd=3_500_000)

    assert done.status_code == 200, done.text
    detail = client.get(f"/api/workflows/{workflow_id}", headers=headers_for("sv.an")).json()
    approval = detail["history"][-1]
    assert (approval["action"], approval["actor"]) == ("repair.approve", "ptk.hoa")
    assert {k: approval["details"][k] for k in ("signing_type", "delegator", "delegated_role", "delegation_number")} == {
        "signing_type": "tuq", "delegator": "tk.hai", "delegated_role": "faculty_head", "delegation_number": NUMBER}
    assert detail["data"]["signing_type"] == "tuq"


def test_delegation_does_not_reach_approvals_above_the_delegators_limit(client, headers_for):
    activate(client, headers_for, tuq_package())
    assert delegate(client, headers_for).status_code == 201
    workflow_id = report(client, headers_for, 12_000_000)
    hoa = headers_for(*PTK_HOA)
    [task_id] = queue(client, headers_for(*HT_KHANH), workflow_id)

    assert queue(client, hoa, workflow_id) == []
    denied = approve(client, hoa, task_id, signing_type="tuq", delegation_number=NUMBER)
    assert (denied.status_code, denied.json()["error"]["code"]) == (403, "FORBIDDEN_AUTHORITY")


def test_expired_or_revoked_delegation_no_longer_allows_approval(app, client, headers_for):
    activate(client, headers_for, tuq_package())
    hoa = headers_for(*PTK_HOA)
    expired = delegate(client, headers_for).json()
    workflow_id = report(client, headers_for, 3_500_000)
    [task_id] = queue(client, hoa, workflow_id)
    with app.state.sessionmaker.begin() as session:
        session.execute(update(Delegation).where(Delegation.id == expired["id"])
                        .values(ends_at=datetime.now(UTC) - timedelta(seconds=1)))

    assert queue(client, hoa, workflow_id) == []
    assert approve(client, hoa, task_id, signing_type="tuq", delegation_number=NUMBER).status_code == 403

    revoked = delegate(client, headers_for).json()
    assert queue(client, hoa, workflow_id) == [task_id]
    assert client.post(f"/api/delegations/{revoked['id']}/revoke", headers=hoa).status_code == 403
    gone = client.post(f"/api/delegations/{revoked['id']}/revoke", headers=headers_for(*TK_HAI))
    assert (gone.status_code, gone.json()["status"]) == (200, "revoked")
    assert client.post(f"/api/delegations/{revoked['id']}/revoke", headers=headers_for(*TK_HAI)).status_code == 409
    assert approve(client, hoa, task_id, signing_type="tuq", delegation_number=NUMBER).status_code == 403


def test_delegate_must_belong_to_the_delegators_unit(client, headers_for):
    activate(client, headers_for, tuq_package())
    assert delegate(client, headers_for, who=KTV_CUONG).status_code == 201
    workflow_id = report(client, headers_for, 3_500_000)
    [task_id] = queue(client, headers_for(*TK_HAI), workflow_id)

    denied = approve(client, headers_for(*KTV_CUONG), task_id, signing_type="tuq", delegation_number=NUMBER)

    assert (denied.status_code, denied.json()["error"]["code"]) == (403, "FORBIDDEN_AUTHORITY")


def test_only_role_holders_delegate_for_at_most_thirty_days(client, headers_for):
    assert delegate(client, headers_for, days=30).status_code == 201
    too_long = delegate(client, headers_for, days=31)
    assert too_long.status_code == 422
    assert [e["path"] for e in too_long.json()["error"]["details"]["errors"]] == ["ends_at"]
    assert delegate(client, headers_for, number="   ").status_code == 422

    redelegated = client.post("/api/delegations", headers=headers_for(*PTK_HOA), json={
        "delegate": "gv.binh", "role": "faculty_head", "number": NUMBER,
        "starts_at": datetime.now(UTC).isoformat(), "ends_at": (datetime.now(UTC) + timedelta(days=1)).isoformat()})
    assert (redelegated.status_code, redelegated.json()["error"]["code"]) == (403, "FORBIDDEN_ROLE")


def test_listing_shows_only_delegations_given_or_received(client, headers_for):
    assert delegate(client, headers_for).status_code == 201

    for who, total in ((TK_HAI, 1), (PTK_HOA, 1), (HT_KHANH, 0)):
        listing = client.get("/api/delegations", headers=headers_for(*who)).json()
        assert listing["total"] == total
