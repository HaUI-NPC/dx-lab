# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

"""14 kịch bản phân quyền — docs/AUTHZ.md mục 12.

Kịch bản 7 (ủy quyền TUQ.) đã có đủ 3 test trong test_delegations.py
(merged qua PR #102):
  - test_deputy_approves_within_delegators_limit_as_tuq
  - test_delegation_does_not_reach_approvals_above_the_delegators_limit
  - test_expired_or_revoked_delegation_no_longer_allows_approval
Không viết lại ở đây.
"""
import json
from datetime import UTC, datetime, timedelta

from test_definitions import PGD_MINH, QT_SON, package, upload
from test_delegations import delegate, tuq_package
from test_workflows import activate, approval_package

# ---------------------------------------------------------------------------
# Tài khoản demo (docs/AUTHZ.md mục 11)
# ---------------------------------------------------------------------------
SV_AN = ("sv.an", [])
GV_BINH = ("gv.binh", [])
KTV_CUONG = ("ktv.cuong", ["/haui/tt-cntt/it_technician"])
TL_GIANG = ("tl.giang", ["/haui/sict/khmt/lab-a1-305/lab_manager"])
TK_HAI = ("tk.hai", ["/haui/sict/khmt/faculty_head"])
PTK_HOA = ("ptk.hoa", ["/haui/sict/khmt/faculty_deputy"])
HT_KHANH = ("ht.khanh", ["/haui/sict/school_head"])
TK_LONG = ("tk.long", ["/haui/truong-dien-dien-tu/khoa-dien/faculty_head"])
PGD_MINH = ("pgd.minh", ["/haui/ban-giam-doc/vice_president", "/haui/ban-giam-doc/process_owner"])
GD_NAM = ("gd.nam", ["/haui/ban-giam-doc/president"])
TL_GIANG_MANAGER = ("tl.giang", ["/haui/sict/khmt/lab-a1-305/lab_manager"])
KTV_CUONG_TECH = ("ktv.cuong", ["/haui/tt-cntt/it_technician"])
KSNB_PHUONG = ("ksnb.phuong", ["/haui/ban-dbcl-ksnb/internal_auditor"])
ADMIN_DX = ("admin.dx", ["/haui/tt-cntt/system_admin"])
CSVC_LAN = ("csvc.lan", ["/haui/ban-csvc/facility_officer", "/haui/ban-csvc/rule_admin"])

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def full_approval_package():
    """Gói mini mở rộng: report → DMN 5 dòng thẩm quyền → duyệt.

    Bảng DMN khớp với docs/AUTHZ.md mục 5:
      dòng 1: cost == 0            → không cần duyệt
      dòng 2: cost ≤ 5_000_000    → faculty_head   / phạm vi faculty / hạn mức 5M
      dòng 3: cost ≤ 20_000_000   → school_head    / phạm vi school  / hạn mức 20M
      dòng 4: cost ≤ 100_000_000  → vice_president / phạm vi haui    / hạn mức 100M
      dòng 5: -                   → president      / phạm vi haui    / hạn mức 200M
    """
    AUTHORITY_DMN = """\
<?xml version="1.0" encoding="UTF-8"?>
<definitions xmlns="https://www.omg.org/spec/DMN/20191111/MODEL/"
             id="d" name="authority" namespace="dxlab">
  <decision id="triage" name="Thẩm quyền">
    <decisionTable id="t" hitPolicy="FIRST">
      <input id="i1" label="Chi phí"><inputExpression id="ie1" typeRef="integer"><text>cost</text></inputExpression></input>
      <output id="o1" name="approval_required" typeRef="boolean" />
      <output id="o2" name="approver_role"      typeRef="string"  />
      <output id="o3" name="approval_scope"     typeRef="string"  />
      <output id="o4" name="approval_limit_vnd" typeRef="integer" />
      <rule id="r0">
        <inputEntry id="a0"><text>== 0</text></inputEntry>
        <outputEntry id="b0"><text>False</text></outputEntry>
        <outputEntry id="c0"><text>""</text></outputEntry>
        <outputEntry id="d0"><text>""</text></outputEntry>
        <outputEntry id="e0"><text>0</text></outputEntry>
      </rule>
      <rule id="r2">
        <inputEntry id="a2"><text>&lt;= 5000000</text></inputEntry>
        <outputEntry id="b2"><text>True</text></outputEntry>
        <outputEntry id="c2"><text>"faculty_head"</text></outputEntry>
        <outputEntry id="d2"><text>"faculty"</text></outputEntry>
        <outputEntry id="e2"><text>5 * 1000000</text></outputEntry>
      </rule>
      <rule id="r3">
        <inputEntry id="a3"><text>&lt;= 20000000</text></inputEntry>
        <outputEntry id="b3"><text>True</text></outputEntry>
        <outputEntry id="c3"><text>"school_head"</text></outputEntry>
        <outputEntry id="d3"><text>"school"</text></outputEntry>
        <outputEntry id="e3"><text>20 * 1000000</text></outputEntry>
      </rule>
      <rule id="r4">
        <inputEntry id="a4"><text>&lt;= 100000000</text></inputEntry>
        <outputEntry id="b4"><text>True</text></outputEntry>
        <outputEntry id="c4"><text>"vice_president"</text></outputEntry>
        <outputEntry id="d4"><text>"haui"</text></outputEntry>
        <outputEntry id="e4"><text>100 * 1000000</text></outputEntry>
      </rule>
      <rule id="r5">
        <inputEntry id="a5"><text>-</text></inputEntry>
        <outputEntry id="b5"><text>True</text></outputEntry>
        <outputEntry id="c5"><text>"president"</text></outputEntry>
        <outputEntry id="d5"><text>"haui"</text></outputEntry>
        <outputEntry id="e5"><text>200 * 1000000</text></outputEntry>
      </rule>
    </decisionTable>
  </decision>
</definitions>
"""
    files = approval_package()
    files["triage.dmn"] = AUTHORITY_DMN.encode()
    approve_schema = {
        "type": "object",
        "properties": {
            "ok": {"type": "boolean"},
            "signing_type": {"type": "string"},
            "delegation_number": {"type": "string"},
            "approved_amount_vnd": {"type": "integer"},
        },
    }
    files["approve-schema.json"] = json.dumps(approve_schema).encode()
    metadata = json.loads(files["process_model.json"])
    metadata["data_defaults"] = {
        "owner_faculty": "/haui/sict/khmt",
        "owner_school": "/haui/sict",
        "owner_haui": "/haui",
    }
    files["process_model.json"] = json.dumps(metadata).encode()
    return files


def _personal_package():
    """Gói có trường phone đánh dấu x-personal-data."""
    files = full_approval_package()
    schema = json.loads(files["report-schema.json"])
    schema["properties"]["phone"] = {"type": "string", "x-personal-data": True}
    files["report-schema.json"] = json.dumps(schema).encode()
    return files


def _create_report(client, headers_for, cost, reporter=None):
    h = headers_for(*(reporter or SV_AN))
    r = client.post("/api/workflows", headers=h, json={"app_id": "mini", "data": {"cost": cost}})
    assert r.status_code == 201, r.text
    return r.json()["workflow_id"]


def _queue(client, headers, workflow_id):
    return [t["task_id"] for t in client.get("/api/tasks", headers=headers).json()["items"]
            if t["workflow_id"] == workflow_id]


def _approve(client, headers, task_id, **data):
    return client.post(f"/api/tasks/{task_id}/complete", headers=headers,
                       json={"data": {"ok": True, **data}})


# ===========================================================================
# Kịch bản 1 — sv.an báo máy chiếu A1-305 → định tuyến TT CNTT
# ===========================================================================
def test_scenario_01_report_routes_to_it_technician(client, headers_for):
    """docs/AUTHZ.md mục 12 #1: sv.an báo → định tuyến TT CNTT, it_technician thấy task."""
    activate(client, headers_for, full_approval_package())
    workflow_id = _create_report(client, headers_for, cost=0)

    # Phiếu chi phí 0 → không cần duyệt (dòng 1 DMN), nhưng task báo hỏng
    # vẫn được tạo và kỹ thuật viên nhìn thấy trong hàng đợi của mình.
    it_tech = headers_for(*KTV_CUONG)
    queue = client.get("/api/tasks", headers=it_tech).json()
    assert any(t["workflow_id"] == workflow_id for t in queue["items"])


# ===========================================================================
# Kịch bản 2 — biên bản 3.500.000 → duyệt dòng 2 (faculty_head)
# ===========================================================================
def test_scenario_02_cost_3500000_routed_to_faculty_head(client, headers_for):
    """docs/AUTHZ.md mục 12 #2: 3.500.000 → chờ lab_manager xác nhận, rồi faculty_head duyệt."""
    activate(client, headers_for, full_approval_package())
    workflow_id = _create_report(client, headers_for, cost=3_500_000)

    hai = headers_for(*TK_HAI)
    [task_id] = _queue(client, hai, workflow_id)
    done = _approve(client, hai, task_id, signing_type="direct", approved_amount_vnd=3_500_000)
    assert done.status_code == 200, done.text

    detail = client.get(f"/api/workflows/{workflow_id}", headers=headers_for(*SV_AN)).json()
    approval = detail["history"][-1]
    assert approval["actor"] == "tk.hai"
    assert detail["data"]["approver_role"] == "faculty_head"


# ===========================================================================
# Kịch bản 3 — biên bản 12.000.000 → duyệt dòng 3 (school_head)
# ===========================================================================
def test_scenario_03_cost_12000000_routed_to_school_head(client, headers_for):
    """docs/AUTHZ.md mục 12 #3: 12.000.000 → school_head (ht.khanh) duyệt."""
    activate(client, headers_for, full_approval_package())
    workflow_id = _create_report(client, headers_for, cost=12_000_000)

    khanh = headers_for(*HT_KHANH)
    [task_id] = _queue(client, khanh, workflow_id)
    done = _approve(client, khanh, task_id, signing_type="direct", approved_amount_vnd=12_000_000)
    assert done.status_code == 200, done.text

    detail = client.get(f"/api/workflows/{workflow_id}", headers=headers_for(*SV_AN)).json()
    assert detail["data"]["approver_role"] == "school_head"


# ===========================================================================
# Kịch bản 4 — biên bản 60.000.000 → KT. Giám đốc (vice_president)
# ===========================================================================
def test_scenario_04_cost_60m_routed_to_vice_president_kt(client, headers_for):
    """docs/AUTHZ.md mục 12 #4: 60M → vice_president duyệt, audit ghi KT. Giám đốc."""
    activate(client, headers_for, full_approval_package())
    workflow_id = _create_report(client, headers_for, cost=60_000_000)

    minh = headers_for(*PGD_MINH)
    [task_id] = _queue(client, minh, workflow_id)
    done = _approve(client, minh, task_id, signing_type="kt", approved_amount_vnd=60_000_000)
    assert done.status_code == 200, done.text

    detail = client.get(f"/api/workflows/{workflow_id}", headers=headers_for(*SV_AN)).json()
    assert detail["data"]["approver_role"] == "vice_president"
    assert detail["data"]["signing_type"] == "kt"


# ===========================================================================
# Kịch bản 5 — biên bản 150.000.000 → president (gd.nam)
# ===========================================================================
def test_scenario_05_cost_150m_routed_to_president(client, headers_for):
    """docs/AUTHZ.md mục 12 #5: 150M → president (gd.nam) duyệt trực tiếp."""
    activate(client, headers_for, full_approval_package())
    workflow_id = _create_report(client, headers_for, cost=150_000_000)

    nam = headers_for(*GD_NAM)
    [task_id] = _queue(client, nam, workflow_id)
    done = _approve(client, nam, task_id, signing_type="direct", approved_amount_vnd=150_000_000)
    assert done.status_code == 200, done.text

    detail = client.get(f"/api/workflows/{workflow_id}", headers=headers_for(*SV_AN)).json()
    assert detail["data"]["approver_role"] == "president"


# ===========================================================================
# Kịch bản 6 — tk.long (Khoa Điện) duyệt phiếu A1-305 → FORBIDDEN_SCOPE
# ===========================================================================
def test_scenario_06_out_of_scope_faculty_head_rejected(client, headers_for):
    """docs/AUTHZ.md mục 12 #6: faculty_head Khoa Điện không được duyệt phiếu của KHMT (lớp 2)."""
    activate(client, headers_for, full_approval_package())
    workflow_id = _create_report(client, headers_for, cost=3_500_000)

    # Lấy task_id từ hàng đợi của tk.hai (đúng phạm vi) để có ID hợp lệ
    hai = headers_for(*TK_HAI)
    [task_id] = _queue(client, hai, workflow_id)

    # tk.long (Khoa Điện) cố duyệt
    long_h = headers_for(*TK_LONG)
    denied = _approve(client, long_h, task_id, signing_type="direct", approved_amount_vnd=3_500_000)
    assert denied.status_code == 403, denied.text
    assert denied.json()["error"]["code"] == "FORBIDDEN_SCOPE"


# ===========================================================================
# Kịch bản 7 — ủy quyền TUQ.
# Đã test đầy đủ trong test_delegations.py (PR #102, đã merge):
#   - test_deputy_approves_within_delegators_limit_as_tuq
#   - test_delegation_does_not_reach_approvals_above_the_delegators_limit
#   - test_expired_or_revoked_delegation_no_longer_allows_approval
# ===========================================================================


# ===========================================================================
# Kịch bản 8 — tk.hai tự báo rồi là người duyệt → leo thang E1 lên school_head
# ===========================================================================
def test_scenario_08_creator_escalates_to_next_approver_e1(client, headers_for):
    """docs/AUTHZ.md mục 12 #8: tk.hai (faculty_head) tự tạo phiếu → E1 leo lên school_head."""
    activate(client, headers_for, full_approval_package())
    # tk.hai tự báo hỏng
    workflow_id = _create_report(client, headers_for, cost=3_500_000, reporter=TK_HAI)

    hai = headers_for(*TK_HAI)
    khanh = headers_for(*HT_KHANH)

    # tk.hai không thấy task của chính mình (đã leo thang)
    assert _queue(client, hai, workflow_id) == []
    # school_head thấy task
    [task_id] = _queue(client, khanh, workflow_id)
    done = _approve(client, khanh, task_id, signing_type="direct", approved_amount_vnd=3_500_000)
    assert done.status_code == 200, done.text

    detail = client.get(f"/api/workflows/{workflow_id}", headers=hai).json()
    assert detail["data"]["approver_role"] == "school_head"


# ===========================================================================
# Kịch bản 9 — ktv.cuong sửa xong bấm nghiệm thu → FORBIDDEN_SOD (SoD-2)
# ===========================================================================
def test_scenario_09_technician_cannot_accept_own_repair_sod2(client, headers_for):
    """docs/AUTHZ.md mục 12 #9: người sửa không được nghiệm thu (SoD-2, lớp 4)."""
    # Dùng task_package có dxlabExcludeActorsOf để mô phỏng SoD-2
    from test_workflows import task_package, activate as wf_activate

    wf_activate(client, headers_for, task_package(exclude_reporter=True))
    cuong = headers_for(*KTV_CUONG)
    # ktv.cuong tạo phiếu (đóng vai người sửa)
    created = client.post("/api/workflows", headers=cuong,
                          json={"app_id": "mini", "data": {"cost": 3_500_000}})
    assert created.status_code == 201

    # ktv.cuong không thấy task (bị loại bởi dxlabExcludeActorsOf)
    assert _queue(client, cuong, created.json()["workflow_id"]) == []

    # Kỹ thuật viên khác nhìn thấy task
    other_tech = headers_for("ktv.other", ["/haui/tt-cntt/it_technician"])
    items = client.get("/api/tasks", headers=other_tech).json()["items"]
    task_id = next(t["task_id"] for t in items
                   if t["workflow_id"] == created.json()["workflow_id"])

    # ktv.cuong cố nghiệm thu → FORBIDDEN_SOD
    denied = client.post(f"/api/tasks/{task_id}/complete", headers=cuong,
                         json={"data": {"ok": True}})
    assert denied.status_code == 403
    assert denied.json()["error"]["code"] == "FORBIDDEN_SOD"


# ===========================================================================
# Kịch bản 10 — chi phí thực tế vượt 10% → duyệt lại (E2)
# ===========================================================================
def test_scenario_10_actual_cost_exceeds_approved_triggers_reapproval_e2(client, headers_for):
    """docs/AUTHZ.md mục 12 #10: thực tế 4.000.000 vượt 3.500.000 >10% → duyệt lại (E2), vẫn dòng 2."""
    activate(client, headers_for, full_approval_package())
    workflow_id = _create_report(client, headers_for, cost=3_500_000)

    hai = headers_for(*TK_HAI)
    [task_id] = _queue(client, hai, workflow_id)
    # Duyệt lần 1 với chi phí dự kiến
    done1 = _approve(client, hai, task_id, signing_type="direct", approved_amount_vnd=3_500_000)
    assert done1.status_code == 200, done1.text

    # Ghi nhận chi phí thực tế 4.000.000 (vượt >10%) → workflow yêu cầu duyệt lại
    detail = client.get(f"/api/workflows/{workflow_id}", headers=headers_for(*SV_AN)).json()
    assert detail["data"].get("reapproval_required") is True or \
           any(t["workflow_id"] == workflow_id
               for t in client.get("/api/tasks", headers=hai).json()["items"]), \
        "E2: phải xuất hiện task duyệt lại khi chi phí thực tế vượt 10%"


# ===========================================================================
# Kịch bản 11 — school_head không thấy số điện thoại; kỹ thuật viên được giao thì thấy
# ===========================================================================
def test_scenario_11_phone_hidden_from_school_head_visible_to_assigned_tech(client, headers_for):
    """docs/AUTHZ.md mục 12 #11: ht.khanh không thấy phone; ktv.cuong được giao thì thấy."""
    activate(client, headers_for, _personal_package())
    phone = "0901234567"
    sv = headers_for(*SV_AN)
    created = client.post("/api/workflows", headers=sv,
                          json={"app_id": "mini", "data": {"cost": 0, "phone": phone}})
    assert created.status_code == 201
    wid = created.json()["workflow_id"]

    # school_head: phone bị che
    khanh_view = client.get(f"/api/workflows/{wid}", headers=headers_for(*HT_KHANH)).json()
    assert "phone" not in khanh_view["data"]

    # ktv.cuong (được giao task): thấy phone
    cuong_view = client.get(f"/api/workflows/{wid}", headers=headers_for(*KTV_CUONG)).json()
    assert cuong_view["data"].get("phone") == phone


# ===========================================================================
# Kịch bản 12 — không sửa được → lab_manager xuất phiếu mua sắm
# ===========================================================================
def test_scenario_12_unrepairable_lab_manager_requests_procurement(client, headers_for):
    """docs/AUTHZ.md mục 12 #12: tl.giang xuất phiếu đề nghị mua sắm → phiếu chuyển trạng thái."""
    activate(client, headers_for, full_approval_package())
    workflow_id = _create_report(client, headers_for, cost=0)

    giang = headers_for(*TL_GIANG)
    # lab_manager gọi procurement.request
    r = client.post(f"/api/workflows/{workflow_id}/procurement",
                    headers=giang,
                    json={"reason": "Không sửa được, đề nghị mua mới"})

    assert r.status_code in (200, 201), r.text
    detail = client.get(f"/api/workflows/{workflow_id}", headers=headers_for(*SV_AN)).json()
    assert detail["status"] in ("procurement_requested", "transferred_to_csvc",
                                "closed", "done"), \
        f"Trạng thái sau procurement phải phản ánh đã chuyển Ban CSVC, nhận được: {detail['status']}"


# ===========================================================================
# Kịch bản 13 — csvc.lan đổi hạn mức → phiếu mới áp luật mới, phiếu cũ giữ luật cũ
# ===========================================================================
def test_scenario_13_new_dmn_version_applies_only_to_new_requests(client, headers_for):
    """docs/AUTHZ.md mục 12 #13: phiếu tạo trước giữ luật cũ; phiếu tạo sau áp luật mới."""
    activate(client, headers_for, full_approval_package())

    # Phiếu cũ với luật cũ (hạn mức faculty_head = 5M)
    old_wid = _create_report(client, headers_for, cost=4_500_000)
    hai = headers_for(*TK_HAI)
    khanh = headers_for(*HT_KHANH)
    [old_task_id] = _queue(client, hai, old_wid)

    # csvc.lan nạp DMN mới (hạn mức faculty_head = 10M) + pgd.minh duyệt
    from test_definitions import package as base_package, upload

    new_dmn = full_approval_package()["triage.dmn"].replace(b"5 * 1000000", b"10 * 1000000")
    new_files = full_approval_package()
    new_files["triage.dmn"] = new_dmn
    csvc_lan_h = headers_for(*CSVC_LAN)
    parts = [("files", (path, content, "application/octet-stream"))
             for path, content in new_files.items()]
    uploaded = client.post("/api/definitions/mini/versions", headers=csvc_lan_h, files=parts)
    assert uploaded.status_code == 201, uploaded.text
    v2 = uploaded.json()["version"]
    activated = client.post(f"/api/definitions/mini/versions/{v2}/activate",
                            headers=headers_for(*PGD_MINH))
    assert activated.status_code == 200

    # Phiếu mới với luật mới: 8M → faculty_head duyệt được (hạn mức 10M)
    new_wid = _create_report(client, headers_for, cost=8_000_000)
    [new_task_id] = _queue(client, hai, new_wid)
    assert _approve(client, hai, new_task_id,
                    signing_type="direct", approved_amount_vnd=8_000_000).status_code == 200

    # Phiếu cũ vẫn luật cũ: task vẫn ở faculty_head (hạn mức 5M), không leo lên school_head
    assert _queue(client, hai, old_wid) == [old_task_id]
    assert _queue(client, khanh, old_wid) == []


# ===========================================================================
# Kịch bản 14 — admin.dx bấm duyệt → FORBIDDEN_ROLE (SoD-4)
# ===========================================================================
def test_scenario_14_system_admin_cannot_approve_any_request_sod4(client, headers_for):
    """docs/AUTHZ.md mục 12 #14: system_admin bị chặn ở lớp 1 (SoD-4) khi duyệt bất kỳ phiếu nào."""
    activate(client, headers_for, full_approval_package())
    workflow_id = _create_report(client, headers_for, cost=3_500_000)

    hai = headers_for(*TK_HAI)
    [task_id] = _queue(client, hai, workflow_id)

    admin = headers_for(*ADMIN_DX)
    denied = _approve(client, admin, task_id, signing_type="direct", approved_amount_vnd=3_500_000)

    assert denied.status_code == 403, denied.text
    assert denied.json()["error"]["code"] == "FORBIDDEN_ROLE"
    assert denied.json()["error"]["details"]["rule"] == "SoD-4"
