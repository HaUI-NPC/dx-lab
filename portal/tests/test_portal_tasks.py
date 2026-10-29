# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

"""Kiểm tra giao diện hộp việc và dữ liệu báo giá."""

import httpx
from fastapi.testclient import TestClient

from dxlab_portal.pages.forms.spec import build_form
from dxlab_portal.pages.forms.validate import validate_form
from dxlab_portal.pages.my_tasks import _value, describe_fields, describe_history
from portal_fakes import FakeCore, FakeKeycloak, login, prefab_text


def test_mang_bao_gia_duoc_gui_voi_kieu_json():
    schema = {"type": "object", "properties": {"quotes": {"type": "array", "items": {"type": "object"}}}}
    spec = build_form(schema, None)
    data, errors = validate_form(spec, {"quotes": '[{"supplier_name":"Công ty A","quote_amount_vnd":100}]'})
    assert errors == {}
    assert data == {"quotes": [{"supplier_name": "Công ty A", "quote_amount_vnd": 100}]}
    assert validate_form(spec, {"quotes": "không phải JSON"})[1]["quotes"]


def test_can_cu_gia_dinh_duoc_danh_nhan():
    assert "giả định" in _value("GĐ-PC-01/2026")


def test_hop_viec_va_lich_su_tu_core(client: TestClient, keycloak: FakeKeycloak, core: FakeCore) -> None:
    task = {"task_id": "task-1", "workflow_id": "wf-1", "step_name": "Chờ duyệt", "overdue": True}
    core.routes[("GET", "/api/tasks")] = lambda _: httpx.Response(200, json={"items": [task], "total": 1})
    core.routes[("GET", "/api/tasks/task-1")] = lambda _: httpx.Response(
        200, json={**task, "form": {"schema": {"type": "object", "properties": {}}, "uischema": {}}}
    )
    core.routes[("GET", "/api/workflows/wf-1")] = lambda _: httpx.Response(
        200, json={"workflow_id": "wf-1", "data": {"asset_id": "AST-1", "tech_role": "it_technician"},
                   "field_titles": {"asset_id": "Mã thiết bị"},
                   "history": [{"actor": "tl.giang", "action": "task.complete", "step_id": "awaiting_approval",
                                "at": "2026-10-30T03:53:00Z",
                                "details": {"step_name": "Chờ duyệt", "authority_basis": "GĐ-PC-01/2026"}}]}
    )
    login(client, keycloak)
    text = prefab_text(client.get("/?tab=tasks&task_id=task-1").text)
    assert "Chờ duyệt" in text and "Quá hạn" in text
    assert "Mã thiết bị: AST-1" in text and "giả định" in text
    assert "tech_role" not in text and "it_technician" not in text


def test_chi_tiet_chi_hien_truong_co_tieu_de_va_dinh_dang_de_doc():
    data = {"estimated_cost_vnd": 12000000, "safety_hazard": False, "quotes": [{"supplier_name": "A", "quote_amount_vnd": 5000}],
            "tech_unit": "/haui/tt-cntt"}
    titles = {"estimated_cost_vnd": "Chi phí dự kiến", "safety_hazard": "Nguy hiểm an toàn", "quotes": "Báo giá"}
    assert describe_fields(data, titles) == [
        ("Chi phí dự kiến", "12.000.000 đ"), ("Nguy hiểm an toàn", "Không"), ("Báo giá", "A · 5.000 đ")]


def test_lich_su_moi_su_kien_mot_dong_co_hinh_thuc_ky_va_can_cu_gia_dinh():
    line, = describe_history([{"actor": "pgd.minh", "action": "repair.approve", "step_id": "awaiting_approval",
                               "at": "2026-10-30T03:53:00Z",
                               "details": {"step_name": "Chờ duyệt", "signing_type": "kt",
                                           "authority_basis": "GĐ-PCBGĐ-2026"}}])
    assert line == "30/10/2026 10:53 · pgd.minh · Duyệt: Chờ duyệt · ký KT. · căn cứ GĐ-PCBGĐ-2026 (giả định)"
