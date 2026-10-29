# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

"""Trang Báo hỏng: form lấy từ core, kiểm tra tiếng Việt, gửi ``POST /api/workflows``."""

from __future__ import annotations

import json
from typing import Any

import httpx
from dxlab_portal.bff.oidc import decode_jwt_payload
from fastapi.testclient import TestClient
from portal_fakes import VALID_REPORT, FakeCore, FakeKeycloak, load_app_json, login, prefab_text, prefab_wire

SUBMIT = "/ui/forms/start/lab-repair"
CREATED = {
    "workflow_id": "b6c3a2f0-1111-4222-8333-444455556666",
    "app_id": "lab-repair",
    "version": "1",
    "status": "pending_assessment",
    "status_name": "Chờ đánh giá",
    "created_at": "2026-10-30T00:30:00Z",
    "due_at": "2026-11-02T00:30:00Z",
}


def serve_start_form(core: FakeCore) -> None:
    form = {
        "app_id": "lab-repair",
        "version": "1",
        "step_id": "report",
        "step_name": "Báo hỏng",
        "schema": load_app_json("lab-repair", "report-schema.json"),
        "uischema": load_app_json("lab-repair", "report-uischema.json"),
    }
    core.routes[("GET", "/api/definitions/lab-repair/start-form")] = lambda request: httpx.Response(
        200, json=form
    )


def workflow_posts(core: FakeCore) -> list[httpx.Request]:
    return [r for r in core.requests if r.method == "POST" and r.url.path == "/api/workflows"]


def test_trang_bao_hong_sinh_form_tu_schema_cua_core(
    client: TestClient, keycloak: FakeKeycloak, core: FakeCore
) -> None:
    serve_start_form(core)
    login(client, keycloak)
    html = client.get("/?tab=report").text
    text = prefab_text(html)
    for label in ("Họ và tên *", "Phòng thực hành *", "Mô tả chi tiết sự cố *", "Gửi phiếu báo hỏng"):
        assert label in text
    state = prefab_wire(html)["state"]
    # AUTHZ §8: ô xác nhận thông báo xử lý dữ liệu không tick sẵn.
    assert state["f_data_processing_consent"] is False
    assert state["f_urgency"] == "normal"
    assert all(v == "" for v in state["errors"].values())


def test_core_chua_co_route_thi_hien_dung_loi_cua_core_khong_dung_form_gia(
    client: TestClient, keycloak: FakeKeycloak
) -> None:
    login(client, keycloak)  # FakeCore không có route start-form nên trả 404 theo định dạng lỗi chung
    html = client.get("/?tab=report").text
    text = prefab_text(html)
    assert "Chưa tải được form báo hỏng" in text
    assert "Không có tài nguyên." in text  # nguyên message của core
    assert "NOT_FOUND" in text and "r-404" in text
    assert "Gửi phiếu báo hỏng" not in text
    assert "f_reporter_name" not in prefab_wire(html).get("state", {})


def test_gui_thieu_truong_tra_loi_tieng_viet_dung_truong_va_khong_goi_core_tao_phieu(
    client: TestClient, keycloak: FakeKeycloak, core: FakeCore
) -> None:
    serve_start_form(core)
    login(client, keycloak)

    response = client.post(
        SUBMIT, json={"values": {**VALID_REPORT, "reporter_name": "", "issue_title": "ab"}}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is False
    assert body["errors"]["reporter_name"] == "Vui lòng nhập họ và tên người báo hỏng."
    assert body["errors"]["issue_title"] == "Tiêu đề tóm tắt sự cố cần có ít nhất 5 ký tự (hiện có 2)."
    assert body["errors"]["reporter_id"] == ""  # trường hợp lệ có thông báo rỗng
    assert body["message"] == "Vui lòng kiểm tra lại 2 trường được đánh dấu đỏ."
    assert workflow_posts(core) == []


def test_chua_dong_y_xu_ly_du_lieu_thi_khong_gui_duoc(
    client: TestClient, keycloak: FakeKeycloak, core: FakeCore
) -> None:
    serve_start_form(core)
    login(client, keycloak)
    response = client.post(SUBMIT, json={"values": {**VALID_REPORT, "data_processing_consent": False}})
    assert response.json()["errors"]["data_processing_consent"].startswith("Bạn cần đánh dấu ô")
    assert workflow_posts(core) == []


def test_gui_hop_le_tao_phieu_qua_core_bang_token_cua_nguoi_dung(
    client: TestClient, keycloak: FakeKeycloak, core: FakeCore
) -> None:
    serve_start_form(core)
    seen: dict[str, Any] = {}

    def create(request: httpx.Request) -> httpx.Response:
        seen["body"] = json.loads(request.content)
        seen["auth"] = request.headers["authorization"]
        return httpx.Response(201, json=CREATED)

    core.routes[("POST", "/api/workflows")] = create
    login(client, keycloak)

    response = client.post(SUBMIT, json={"values": {**VALID_REPORT, "reporter_phone": " 0912345678 "}})

    body = response.json()
    assert body["ok"] is True and body["workflow"] == CREATED
    assert all(message == "" for message in body["errors"].values())
    assert seen["body"]["app_id"] == "lab-repair"
    data = seen["body"]["data"]
    assert data["reporter_phone"] == "0912345678"  # đã cắt khoảng trắng
    assert data["data_processing_consent"] is True
    assert data["consent_notice_version"] == "v1.0"  # giá trị mặc định của trường không hiện trên form
    assert decode_jwt_payload(seen["auth"].removeprefix("Bearer "))["preferred_username"] == "tl.giang"


def test_core_tu_choi_422_thi_loi_gan_ve_dung_truong(
    client: TestClient, keycloak: FakeKeycloak, core: FakeCore
) -> None:
    serve_start_form(core)
    core.routes[("POST", "/api/workflows")] = lambda request: httpx.Response(
        422,
        json={
            "error": {
                "code": "VALIDATION_FAILED",
                "message": "Dữ liệu không hợp lệ.",
                "details": {
                    "errors": [
                        {"path": "data.asset_id", "message": "Tài sản không tồn tại."},
                        {"path": "data.khong_co_tren_form", "message": "Trường lạ."},
                    ]
                },
                "request_id": "r-422",
            }
        },
    )
    login(client, keycloak)

    body = client.post(SUBMIT, json={"values": VALID_REPORT}).json()

    assert body["ok"] is False
    assert body["errors"]["asset_id"] == "Tài sản không tồn tại."
    assert "data.khong_co_tren_form: Trường lạ." in body["message"]


def test_core_tu_choi_403_thi_giu_nguyen_ma_loi_va_request_id(
    client: TestClient, keycloak: FakeKeycloak, core: FakeCore
) -> None:
    serve_start_form(core)
    core.routes[("POST", "/api/workflows")] = lambda request: httpx.Response(
        403,
        json={
            "error": {
                "code": "FORBIDDEN_SCOPE",
                "message": "Phiếu thuộc phòng ngoài phạm vi đơn vị của bạn.",
                "details": {"layer": 2},
                "request_id": "r-403",
            }
        },
    )
    login(client, keycloak)

    body = client.post(SUBMIT, json={"values": VALID_REPORT}).json()

    assert body["ok"] is False
    assert body["error"] == {
        "code": "FORBIDDEN_SCOPE",
        "message": "Phiếu thuộc phòng ngoài phạm vi đơn vị của bạn.",
        "request_id": "r-403",
        "status": 403,
    }


def test_core_khong_co_form_thi_gui_tra_loi_cua_core(
    client: TestClient, keycloak: FakeKeycloak, core: FakeCore
) -> None:
    login(client, keycloak)
    body = client.post(SUBMIT, json={"values": VALID_REPORT}).json()
    assert body["ok"] is False and body["error"]["code"] == "NOT_FOUND" and body["error"]["status"] == 404
    assert workflow_posts(core) == []


def test_chua_dang_nhap_thi_khong_gui_duoc(client: TestClient, core: FakeCore) -> None:
    response = client.post(SUBMIT, json={"values": VALID_REPORT})
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHENTICATED"
    assert core.requests == []
