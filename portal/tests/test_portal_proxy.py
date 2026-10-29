# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

"""Proxy ``/api/{path}``: gắn token của người dùng, truyền nguyên lỗi của core."""

from __future__ import annotations

import json

import httpx
from dxlab_portal.bff.oidc import decode_jwt_payload
from fastapi.testclient import TestClient
from portal_fakes import PUBLIC_URL, FakeCore, FakeKeycloak, login


def test_chua_dang_nhap_thi_api_tra_401_dung_dinh_dang_loi_va_khong_goi_core(
    client: TestClient, core: FakeCore
) -> None:
    response = client.get("/api/tasks")
    assert response.status_code == 401
    error = response.json()["error"]
    assert error["code"] == "UNAUTHENTICATED"
    assert "đăng nhập" in error["message"]
    assert error["request_id"]
    assert core.requests == []


def test_proxy_gan_token_cua_nguoi_dang_nhap_va_giu_nguyen_duong_dan(
    client: TestClient, keycloak: FakeKeycloak, core: FakeCore
) -> None:
    core.routes[("GET", "/api/tasks")] = lambda request: httpx.Response(
        200, json={"items": [{"task_id": "t1"}], "total": 1}, headers={"X-Request-Id": "abc"}
    )
    login(client, keycloak)
    client.headers["authorization"] = "Bearer do-trinh-duyet-tu-gui"

    response = client.get("/api/tasks", params={"limit": "5", "offset": "10"})

    assert response.status_code == 200
    assert response.json() == {"items": [{"task_id": "t1"}], "total": 1}
    upstream = core.requests[-1]
    assert upstream.url.path == "/api/tasks"  # không viết lại đường dẫn
    assert dict(upstream.url.params) == {"limit": "5", "offset": "10"}
    bearer = upstream.headers["authorization"].removeprefix("Bearer ")
    assert decode_jwt_payload(bearer)["preferred_username"] == "tl.giang"  # token của người dùng
    assert "do-trinh-duyet-tu-gui" not in upstream.headers["authorization"]
    assert "cookie" not in upstream.headers  # cookie phiên không rời khỏi portal


def test_proxy_chuyen_body_json_cua_post(client: TestClient, keycloak: FakeKeycloak, core: FakeCore) -> None:
    seen: dict[str, object] = {}

    def create(request: httpx.Request) -> httpx.Response:
        seen["body"] = json.loads(request.content)
        seen["content_type"] = request.headers["content-type"]
        return httpx.Response(201, json={"workflow_id": "w1", "status": "report"})

    core.routes[("POST", "/api/workflows")] = create
    login(client, keycloak)

    response = client.post(
        "/api/workflows", json={"app_id": "lab-repair", "data": {"issue_title": "Máy chiếu mờ"}}
    )

    assert response.status_code == 201
    assert response.json()["workflow_id"] == "w1"
    assert seen["body"] == {"app_id": "lab-repair", "data": {"issue_title": "Máy chiếu mờ"}}
    assert seen["content_type"].startswith("application/json")  # type: ignore[union-attr]


def test_proxy_truyen_nguyen_loi_json_cua_core(
    client: TestClient, keycloak: FakeKeycloak, core: FakeCore
) -> None:
    loi = {
        "error": {
            "code": "VALIDATION_FAILED",
            "message": "Dữ liệu không hợp lệ.",
            "details": {"errors": [{"path": "issue_title", "message": "Quá ngắn"}]},
            "request_id": "8d0b6c1e",
        }
    }
    core.routes[("POST", "/api/workflows")] = lambda request: httpx.Response(
        422, json=loi, headers={"X-Request-Id": "8d0b6c1e"}
    )
    login(client, keycloak)

    response = client.post("/api/workflows", json={"app_id": "lab-repair", "data": {}})

    assert response.status_code == 422
    assert response.json() == loi
    assert response.headers["x-request-id"] == "8d0b6c1e"


def test_proxy_truyen_loi_403_cua_core(client: TestClient, keycloak: FakeKeycloak, core: FakeCore) -> None:
    core.routes[("GET", "/api/audit")] = lambda request: httpx.Response(
        403,
        json={
            "error": {
                "code": "FORBIDDEN_ROLE",
                "message": "Vai trò không đủ quyền.",
                "details": {"layer": 1},
                "request_id": "r1",
            }
        },
    )
    login(client, keycloak)
    response = client.get("/api/audit")
    assert response.status_code == 403
    assert response.json()["error"]["details"] == {"layer": 1}


def test_core_khong_toi_duoc_thi_bao_502_dung_dinh_dang_loi(
    keycloak: FakeKeycloak,
) -> None:
    from dxlab_portal.app import create_app
    from portal_fakes import make_settings

    def down(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("từ chối kết nối", request=request)

    app = create_app(
        make_settings(),
        oidc_transport=httpx.MockTransport(keycloak.handler),
        core_transport=httpx.MockTransport(down),
    )
    client = TestClient(app, base_url=PUBLIC_URL, follow_redirects=False)
    login(client, keycloak)
    response = client.get("/api/tasks")
    assert response.status_code == 502
    assert response.json()["error"]["code"] == "INTERNAL"


def test_yeu_cau_ghi_tu_trang_khac_bi_chan(
    client: TestClient, keycloak: FakeKeycloak, core: FakeCore
) -> None:
    login(client, keycloak)
    response = client.post(
        "/api/workflows",
        json={"app_id": "lab-repair", "data": {}},
        headers={"Origin": "http://trang-doc-hai.example"},
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN_ORIGIN"
    assert core.requests == []


def test_healthz_khong_can_dang_nhap(client: TestClient) -> None:
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
