# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

"""14 kịch bản kiểm chứng của docs/AUTHZ.md mục 12, chạy trên gói ứng dụng thật `apps/lab-repair`.

Mỗi test dựng đúng tình huống của kịch bản bằng API công khai (tạo phiếu, hộp việc, hoàn thành bước) với tài khoản demo
của mục 11 và chỉ kiểm điều người dùng quan sát được: ai thấy việc, ai duyệt được, mã lỗi trả về, dữ liệu phiếu và audit.

Kịch bản 7 (ủy quyền TUQ.) đã có đủ ba test trong `test_delegations.py`, không viết lại ở đây:
  - test_deputy_approves_within_delegators_limit_as_tuq
  - test_delegation_does_not_reach_approvals_above_the_delegators_limit
  - test_expired_or_revoked_delegation_no_longer_allows_approval
"""
from pathlib import Path

import pytest
from sample_data import ROOMS, ROOMS_LICENSE, ROOMS_SOURCE
from test_definitions import PGD_MINH, QT_SON

APP = Path(__file__).resolve().parents[2] / "apps" / "lab-repair"

SV_AN = ("sv.an", [])
KTV_CUONG = ("ktv.cuong", ["/haui/tt-cntt/it_technician"])
TL_GIANG = ("tl.giang", ["/haui/sict/khmt/lab-a1-305/lab_manager"])
TK_HAI = ("tk.hai", ["/haui/sict/khmt/faculty_head"])
HT_KHANH = ("ht.khanh", ["/haui/sict/school_head"])
TK_LONG = ("tk.long", ["/haui/truong-dien-dien-tu/khoa-dien/faculty_head"])
GD_NAM = ("gd.nam", ["/haui/ban-giam-doc/president"])
CSVC_LAN = ("csvc.lan", ["/haui/ban-csvc/facility_officer", "/haui/ban-csvc/rule_admin"])
ADMIN_DX = ("admin.dx", ["/haui/tt-cntt/system_admin"])


def package() -> dict[str, bytes]:
    return {path.relative_to(APP).as_posix(): path.read_bytes()
            for path in sorted(APP.rglob("*")) if path.is_file() and "eval" not in path.relative_to(APP).parts}


def upload_and_activate(client, headers_for, files, *, uploader=QT_SON) -> None:
    parts = [("files", (path, content, "application/octet-stream")) for path, content in files.items()]
    uploaded = client.post("/api/definitions/lab-repair/versions", headers=headers_for(*uploader), files=parts)
    assert uploaded.status_code == 201, uploaded.text
    activated = client.post(f"/api/definitions/lab-repair/versions/{uploaded.json()['version']}/activate",
                            headers=headers_for(*PGD_MINH))
    assert activated.status_code == 200, activated.text


@pytest.fixture
def lab_repair(client, headers_for):
    """Ứng dụng báo hỏng đang áp dụng phiên bản 1 và danh mục phòng đã nạp."""
    upload_and_activate(client, headers_for, package())
    for room in ROOMS:
        stored = client.put(f"/api/records/lab-repair/room/{room['id']}", headers=headers_for(*CSVC_LAN),
                            json={"data": room, "source": ROOMS_SOURCE, "license": ROOMS_LICENSE,
                                  "source_ref": f"rooms.json#{room['id']}"})
        assert stored.status_code == 201, stored.text


def report(client, headers_for, reporter=SV_AN, **overrides) -> str:
    data = {"reporter_name": "Nguyễn Văn An", "reporter_id": "2021602001", "reporter_phone": "0901234567",
            "reporter_email": "an@example.com", "room_id": "lab-a1-305", "asset_id": "pc-a1-305-12",
            "asset_category": "projector", "issue_title": "Máy chiếu không lên hình",
            "issue_description": "Máy chiếu bật đèn nhưng không có tín hiệu hình.", "urgency": "normal",
            "impact": "partial_session", "safety_hazard": False, "data_processing_consent": True} | overrides
    created = client.post("/api/workflows", headers=headers_for(*reporter), json={"app_id": "lab-repair", "data": data})
    assert created.status_code == 201, created.text
    return created.json()["workflow_id"]


def inbox(client, headers_for, who, workflow_id) -> list[dict]:
    items = client.get("/api/tasks", headers=headers_for(*who)).json()["items"]
    return [t for t in items if t["workflow_id"] == workflow_id]


def complete(client, headers_for, who, workflow_id, step_id, data):
    [task] = [t for t in inbox(client, headers_for, who, workflow_id) if t["step_id"] == step_id]
    return client.post(f"/api/tasks/{task['task_id']}/complete", headers=headers_for(*who), json={"data": data})


def done(response) -> dict:
    assert response.status_code == 200, response.text
    return response.json()


def assess(client, headers_for, workflow_id, *, result="needs_cost", cost=0, quotes=0, action="repair"):
    return complete(client, headers_for, KTV_CUONG, workflow_id, "pending_assessment", {
        "technician_name": "Lê Văn Cường", "inspection_date": "2026-10-20", "fault_cause": "Hỏng bóng đèn máy chiếu",
        "assessment_result": result, "quote_count": quotes, "action_type": action, "estimated_cost_vnd": cost,
        "technician_recommendation": "Đề nghị thay bóng đèn mới"})


def endorse(client, headers_for, workflow_id):
    return complete(client, headers_for, TL_GIANG, workflow_id, "awaiting_endorsement", {
        "lab_manager_name": "Đặng Thị Giang", "confirm_date": "2026-10-21", "need_confirmed": True,
        "urgency_level": "normal", "manager_comment": "Cần sửa để phục vụ lịch dạy"})


def approval_form(role, amount, signing="direct", decision="approved") -> dict:
    return {"approver_name": "Người duyệt", "approver_role": role, "signing_type": signing, "decision": decision,
            "approved_amount_vnd": amount, "approval_date": "2026-10-22", "approval_comment": "Đồng ý theo hạn mức"}


def repair(client, headers_for, workflow_id, actual_cost):
    return complete(client, headers_for, KTV_CUONG, workflow_id, "repairing", {
        "technician_name": "Lê Văn Cường", "repair_date": "2026-10-23", "work_performed": "Thay bóng đèn máy chiếu",
        "actual_cost_vnd": actual_cost, "repair_status": "completed", "technical_notes": "Đã chạy thử ổn định"})


def awaiting_approval(client, headers_for, cost, quotes=1, reporter=SV_AN) -> str:
    """Phiếu đã kiểm tra và được trưởng phòng xác nhận nhu cầu, đang chờ người duyệt theo bảng thẩm quyền."""
    workflow_id = report(client, headers_for, reporter)
    done(assess(client, headers_for, workflow_id, cost=cost, quotes=quotes))
    done(endorse(client, headers_for, workflow_id))
    return workflow_id


def view(client, headers_for, who, workflow_id) -> dict:
    shown = client.get(f"/api/workflows/{workflow_id}", headers=headers_for(*who))
    assert shown.status_code == 200, shown.text
    return shown.json()


def test_1_projector_report_goes_to_it_center_queue(client, headers_for, lab_repair):
    workflow_id = report(client, headers_for)

    [task] = inbox(client, headers_for, KTV_CUONG, workflow_id)
    assert (task["step_id"], task["lane"]) == ("pending_assessment", "technician")
    facility_technician = ("ktv.csvc", ["/haui/ban-csvc/facility_technician"])
    assert inbox(client, headers_for, facility_technician, workflow_id) == []
    data = view(client, headers_for, SV_AN, workflow_id)["data"]
    assert (data["tech_unit"], data["tech_role"]) == ("/haui/tt-cntt", "it_technician")


def test_2_cost_3_5m_waits_for_lab_manager_then_faculty_head(client, headers_for, lab_repair):
    workflow_id = report(client, headers_for)
    done(assess(client, headers_for, workflow_id, cost=3_500_000, quotes=1))

    assert [t["step_id"] for t in inbox(client, headers_for, TL_GIANG, workflow_id)] == ["awaiting_endorsement"]
    assert inbox(client, headers_for, TK_HAI, workflow_id) == []
    done(endorse(client, headers_for, workflow_id))

    assert inbox(client, headers_for, TL_GIANG, workflow_id) == []
    [task] = inbox(client, headers_for, TK_HAI, workflow_id)
    assert task["step_id"] == "awaiting_approval"
    assert inbox(client, headers_for, HT_KHANH, workflow_id) == []
    data = view(client, headers_for, SV_AN, workflow_id)["data"]
    assert (data["approver_role"], data["approval_limit_vnd"]) == ("faculty_head", 5_000_000)
    approved = done(complete(client, headers_for, TK_HAI, workflow_id, "awaiting_approval",
                             approval_form("faculty_head", 3_500_000)))
    assert approved["status"] == "repairing"


def test_3_cost_12m_goes_to_school_head(client, headers_for, lab_repair):
    workflow_id = awaiting_approval(client, headers_for, cost=12_000_000)

    assert inbox(client, headers_for, TK_HAI, workflow_id) == []
    [task] = inbox(client, headers_for, HT_KHANH, workflow_id)
    assert task["step_id"] == "awaiting_approval"
    approved = done(complete(client, headers_for, HT_KHANH, workflow_id, "awaiting_approval",
                             approval_form("school_head", 12_000_000)))
    assert approved["status"] == "repairing"
    data = view(client, headers_for, SV_AN, workflow_id)["data"]
    assert (data["approver_role"], data["approval_limit_vnd"]) == ("school_head", 20_000_000)


def test_4_cost_60m_needs_three_quotes_then_vice_president_signs_kt(client, headers_for, lab_repair):
    workflow_id = report(client, headers_for)

    # Thiếu báo giá: phiếu quay lại bước kiểm tra, không có ai được duyệt.
    done(assess(client, headers_for, workflow_id, cost=60_000_000, quotes=2))
    assert [t["step_id"] for t in inbox(client, headers_for, KTV_CUONG, workflow_id)] == ["pending_assessment"]
    assert inbox(client, headers_for, TL_GIANG, workflow_id) == []
    assert view(client, headers_for, SV_AN, workflow_id)["status"] == "pending_assessment"

    done(assess(client, headers_for, workflow_id, cost=60_000_000, quotes=3))
    done(endorse(client, headers_for, workflow_id))
    minh = ("pgd.minh", ["/haui/ban-giam-doc/vice_president", "/haui/ban-giam-doc/process_owner"])
    [task] = inbox(client, headers_for, minh, workflow_id)
    assert task["step_id"] == "awaiting_approval"
    approved = done(complete(client, headers_for, minh, workflow_id, "awaiting_approval",
                             approval_form("vice_president", 60_000_000, signing="kt")))
    assert approved["status"] == "repairing"
    [approval] = [e for e in view(client, headers_for, SV_AN, workflow_id)["history"] if e["action"] == "repair.approve"]
    assert approval["actor"] == "pgd.minh"
    assert approval["details"]["signing_type"] == "kt"


def test_5_cost_150m_goes_to_president(client, headers_for, lab_repair):
    workflow_id = awaiting_approval(client, headers_for, cost=150_000_000, quotes=3)

    assert inbox(client, headers_for, HT_KHANH, workflow_id) == []
    [task] = inbox(client, headers_for, GD_NAM, workflow_id)
    assert task["step_id"] == "awaiting_approval"
    approved = done(complete(client, headers_for, GD_NAM, workflow_id, "awaiting_approval",
                             approval_form("president", 150_000_000)))
    assert approved["status"] == "repairing"


def test_6_faculty_head_of_another_faculty_is_rejected_at_scope_layer(client, headers_for, lab_repair):
    workflow_id = awaiting_approval(client, headers_for, cost=3_500_000)
    [task] = inbox(client, headers_for, TK_HAI, workflow_id)

    assert inbox(client, headers_for, TK_LONG, workflow_id) == []
    denied = client.post(f"/api/tasks/{task['task_id']}/complete", headers=headers_for(*TK_LONG),
                         json={"data": approval_form("faculty_head", 3_500_000)})

    assert denied.status_code == 403
    error = denied.json()["error"]
    assert (error["code"], error["details"]["layer"]) == ("FORBIDDEN_SCOPE", 2)
    assert view(client, headers_for, SV_AN, workflow_id)["status"] == "awaiting_approval"


def test_8_reporter_who_is_the_approver_is_escalated_to_school_head(client, headers_for, lab_repair):
    workflow_id = awaiting_approval(client, headers_for, cost=3_500_000, reporter=TK_HAI)

    assert inbox(client, headers_for, TK_HAI, workflow_id) == []
    [task] = inbox(client, headers_for, HT_KHANH, workflow_id)
    assert task["step_id"] == "awaiting_approval"
    data = view(client, headers_for, TK_HAI, workflow_id)["data"]
    assert (data["approver_role"], data["approval_limit_vnd"]) == ("school_head", 20_000_000)
    approved = done(complete(client, headers_for, HT_KHANH, workflow_id, "awaiting_approval",
                             approval_form("school_head", 3_500_000)))
    assert approved["status"] == "repairing"


def test_9_technician_who_repaired_cannot_accept_own_work(client, headers_for, lab_repair):
    workflow_id = awaiting_approval(client, headers_for, cost=3_500_000)
    done(complete(client, headers_for, TK_HAI, workflow_id, "awaiting_approval", approval_form("faculty_head", 3_500_000)))
    done(repair(client, headers_for, workflow_id, actual_cost=3_500_000))
    [task] = inbox(client, headers_for, TL_GIANG, workflow_id)
    assert task["step_id"] == "awaiting_acceptance"

    denied = client.post(f"/api/tasks/{task['task_id']}/complete", headers=headers_for(*KTV_CUONG), json={"data": {
        "acceptor_name": "Lê Văn Cường", "acceptor_role": "lab_manager", "acceptance_date": "2026-10-24",
        "operational_status": "normal", "acceptance_result": "accepted", "acceptance_notes": "Tự nghiệm thu",
        "handover_signed": True}})

    assert denied.status_code == 403
    error = denied.json()["error"]
    assert (error["code"], error["details"]["layer"]) == ("FORBIDDEN_SOD", 4)
    assert view(client, headers_for, SV_AN, workflow_id)["status"] == "awaiting_acceptance"


def test_10_actual_cost_over_ten_percent_requires_reapproval_by_same_faculty_head(client, headers_for, lab_repair):
    workflow_id = awaiting_approval(client, headers_for, cost=3_500_000)
    done(complete(client, headers_for, TK_HAI, workflow_id, "awaiting_approval", approval_form("faculty_head", 3_500_000)))

    after_repair = done(repair(client, headers_for, workflow_id, actual_cost=4_000_000))

    assert after_repair["status"] == "awaiting_approval"
    assert inbox(client, headers_for, TL_GIANG, workflow_id) == []
    assert inbox(client, headers_for, HT_KHANH, workflow_id) == []
    [task] = inbox(client, headers_for, TK_HAI, workflow_id)
    assert task["step_id"] == "awaiting_approval"
    data = view(client, headers_for, SV_AN, workflow_id)["data"]
    assert (data["approver_role"], data["cost_recheck_reason"]) == ("faculty_head", "VUOT_10_PHAN_TRAM")
    reapproved = done(complete(client, headers_for, TK_HAI, workflow_id, "awaiting_approval",
                               approval_form("faculty_head", 4_000_000)))
    assert reapproved["status"] == "awaiting_acceptance"


def test_11_reporter_phone_is_hidden_from_school_head_but_shown_to_assigned_technician(client, headers_for, lab_repair):
    workflow_id = report(client, headers_for)

    assert "reporter_phone" not in view(client, headers_for, HT_KHANH, workflow_id)["data"]
    assert view(client, headers_for, KTV_CUONG, workflow_id)["data"]["reporter_phone"] == "0901234567"
    assert view(client, headers_for, TL_GIANG, workflow_id)["data"]["reporter_phone"] == "0901234567"


def test_12_unrepairable_asset_is_handed_off_to_facilities_office(client, headers_for, lab_repair):
    workflow_id = report(client, headers_for)
    done(assess(client, headers_for, workflow_id, result="not_repairable", cost=0))

    [task] = inbox(client, headers_for, TL_GIANG, workflow_id)
    assert task["step_id"] == "awaiting_handoff"
    handed = done(complete(client, headers_for, TL_GIANG, workflow_id, "awaiting_handoff", {
        "handoff_type": "procurement_replace", "handoff_reason": "Máy chiếu hỏng bo mạch, không sửa được"}))

    assert (handed["status"], handed["status_name"]) == ("handed_off", "Đã chuyển Ban CSVC")
    assert inbox(client, headers_for, TL_GIANG, workflow_id) == []


def test_13_new_authority_version_applies_only_to_new_requests(client, headers_for, lab_repair):
    old_workflow = awaiting_approval(client, headers_for, cost=8_000_000)
    assert [t["step_id"] for t in inbox(client, headers_for, HT_KHANH, old_workflow)] == ["awaiting_approval"]

    # csvc.lan (rule_admin) nâng hạn mức trưởng khoa từ 5 lên 10 triệu; pgd.minh duyệt phiên bản.
    files = package()
    dmn = files["authority.dmn"].decode()
    assert dmn.count("&lt;= 5000000") == 1 and dmn.count("<text>5000000</text>") == 1
    files["authority.dmn"] = dmn.replace("&lt;= 5000000", "&lt;= 10000000").replace(
        "<text>5000000</text>", "<text>10000000</text>").encode()
    upload_and_activate(client, headers_for, files, uploader=CSVC_LAN)

    new_workflow = awaiting_approval(client, headers_for, cost=8_000_000)
    [task] = inbox(client, headers_for, TK_HAI, new_workflow)
    assert task["step_id"] == "awaiting_approval"
    assert inbox(client, headers_for, HT_KHANH, new_workflow) == []
    assert view(client, headers_for, SV_AN, new_workflow)["version"] == 2
    approved = done(complete(client, headers_for, TK_HAI, new_workflow, "awaiting_approval",
                             approval_form("faculty_head", 8_000_000)))
    assert approved["status"] == "repairing"

    assert view(client, headers_for, SV_AN, old_workflow)["version"] == 1
    assert inbox(client, headers_for, TK_HAI, old_workflow) == []
    assert [t["step_id"] for t in inbox(client, headers_for, HT_KHANH, old_workflow)] == ["awaiting_approval"]


def test_14_system_admin_cannot_approve_any_request(client, headers_for, lab_repair):
    workflow_id = awaiting_approval(client, headers_for, cost=3_500_000)
    [task] = inbox(client, headers_for, TK_HAI, workflow_id)

    assert client.get("/api/tasks", headers=headers_for(*ADMIN_DX)).status_code == 403
    denied = client.post(f"/api/tasks/{task['task_id']}/complete", headers=headers_for(*ADMIN_DX),
                         json={"data": approval_form("faculty_head", 3_500_000)})

    assert denied.status_code == 403
    error = denied.json()["error"]
    assert (error["code"], error["details"]["rule"]) == ("FORBIDDEN_ROLE", "SoD-4")
    assert view(client, headers_for, SV_AN, workflow_id)["status"] == "awaiting_approval"
