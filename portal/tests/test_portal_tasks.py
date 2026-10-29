# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

"""Kiểm tra giao diện hộp việc và dữ liệu báo giá."""

import httpx
from fastapi.testclient import TestClient

from dxlab_portal.pages.forms.spec import build_form
from dxlab_portal.pages.forms.validate import validate_form
from dxlab_portal.pages.my_tasks import _value
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
        200, json={"workflow_id": "wf-1", "data": {"asset_id": "AST-1"},
                   "history": [{"action": "duyệt", "details": {"basis": "GĐ-PC-01/2026"}}]}
    )
    login(client, keycloak)
    text = prefab_text(client.get("/?tab=tasks&task_id=task-1").text)
    assert "Chờ duyệt" in text and "Quá hạn" in text
    assert "AST-1" in text and "giả định" in text
