# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

"""Đăng nhập OIDC, cookie phiên và gia hạn token."""

from __future__ import annotations

import re
from urllib.parse import parse_qs, urlsplit

import httpx
import pytest
from dxlab_portal.app import create_app
from dxlab_portal.bff.oidc import decode_jwt_payload
from fastapi.testclient import TestClient
from portal_fakes import (
    CLIENT_SECRET,
    ISSUER,
    PUBLIC_URL,
    FakeCore,
    FakeKeycloak,
    login,
    make_settings,
    markup_outside_renderer,
    prefab_text,
)


def test_chua_dang_nhap_thi_chuyen_huong_toi_dang_nhap(client: TestClient) -> None:
    response = client.get("/")
    assert response.status_code == 302
    assert response.headers["location"] == "/auth/login?next=%2F"


def test_login_chuyen_toi_keycloak_voi_pkce_s256(client: TestClient) -> None:
    response = client.get("/auth/login")
    assert response.status_code == 302
    location = urlsplit(response.headers["location"])
    assert f"{location.scheme}://{location.netloc}{location.path}" == f"{ISSUER}/protocol/openid-connect/auth"
    query = {k: v[0] for k, v in parse_qs(location.query).items()}
    assert query["response_type"] == "code"
    assert query["client_id"] == "dxlab-portal"
    assert query["redirect_uri"] == f"{PUBLIC_URL}/auth/callback"
    assert query["code_challenge_method"] == "S256"
    assert query["code_challenge"] and query["state"] and query["nonce"]
    assert "client_secret" not in query


def test_dang_nhap_day_du_cookie_phien_httponly_va_khong_chua_token(
    client: TestClient, keycloak: FakeKeycloak
) -> None:
    response = login(client, keycloak)
    assert response.status_code == 303
    assert response.headers["location"] == "/"

    cookies = [c for c in response.headers.get_list("set-cookie") if c.startswith("dxlab_session=")]
    assert len(cookies) == 1
    attrs = cookies[0].lower()
    assert "httponly" in attrs and "samesite=lax" in attrs and "path=/" in attrs
    cookie_value = cookies[0].split(";")[0].split("=", 1)[1]
    # Cookie chỉ chứa mã phiên đã ký, không phải token OIDC.
    assert "eyJ" not in cookie_value
    assert "refresh-" not in cookie_value

    # Đổi code lấy token dùng đúng secret của client; Keycloak giả đã kiểm code_verifier khớp code_challenge.
    assert keycloak.token_forms[0]["grant_type"] == "authorization_code"
    assert keycloak.token_forms[0]["client_secret"] == CLIENT_SECRET


def test_trang_chinh_hien_ten_va_vai_tro_tu_claim_groups(client: TestClient, keycloak: FakeKeycloak) -> None:
    login(client, keycloak)
    page = client.get("/")
    assert page.status_code == 200
    text = prefab_text(page.text)
    assert "Hoàng Thu Giang" in text
    assert "lab_manager · /haui/sict/khmt/lab-a1-305" in text
    assert "/auth/logout" in text
    for tab in ("Việc của tôi", "Báo hỏng", "Tra cứu", "Dashboard", "Trạng thái hệ thống"):
        assert tab in text
    assert "default-src 'self'" in page.headers["content-security-policy"]


def test_trang_chinh_khong_tai_tai_nguyen_ngoai(client: TestClient, keycloak: FakeKeycloak) -> None:
    login(client, keycloak)
    markup = markup_outside_renderer(client.get("/").text)
    # Renderer Prefab đóng gói sẵn: không có thẻ script/link/img nạp tài nguyên từ URL ngoài.
    assert not re.search(r"<(?:script|link|img|iframe)\b[^>]*\s(?:src|href)=", markup)
    assert "jsdelivr" not in markup


def test_vai_tro_lay_tu_api_me_khi_core_tra_loi(
    client: TestClient, keycloak: FakeKeycloak, core: FakeCore
) -> None:
    core.routes[("GET", "/api/me")] = lambda request: httpx.Response(
        200,
        json={
            "username": "tl.giang",
            "name": "Hoàng Thu Giang",
            "roles": [
                {"role": "lab_manager", "unit": "/haui/sict/khmt/lab-a1-305"},
                {"role": "reporter", "unit": None},
            ],
            "units": ["/haui/sict/khmt/lab-a1-305"],
        },
    )
    login(client, keycloak)
    page = client.get("/")
    assert "reporter" in prefab_text(page.text)
    assert core.requests[0].headers["authorization"].startswith("Bearer ")


def test_callback_voi_state_la_bi_tu_choi_va_khong_tao_phien(
    client: TestClient, keycloak: FakeKeycloak
) -> None:
    client.get("/auth/login")
    response = client.get("/auth/callback", params={"code": "code-gia", "state": "state-gia"})
    assert response.status_code == 400
    assert "dxlab_session" not in response.headers.get("set-cookie", "")
    assert client.get("/").status_code == 302


def test_callback_khong_co_cookie_tam_bi_tu_choi(client: TestClient, keycloak: FakeKeycloak) -> None:
    start = client.get("/auth/login")
    params = keycloak.authorize_request(start.headers["location"])
    client.cookies.clear()  # trình duyệt khác với trình duyệt đã bắt đầu đăng nhập (login CSRF)
    response = client.get("/auth/callback", params=params)
    assert response.status_code == 400
    assert not any(c.name == "dxlab_session" for c in client.cookies.jar)


def test_cookie_phien_gia_mao_bi_coi_la_chua_dang_nhap(client: TestClient, keycloak: FakeKeycloak) -> None:
    login(client, keycloak)
    client.cookies.clear()
    client.cookies.set("dxlab_session", "khong-hop-le")
    assert client.get("/").status_code == 302
    assert client.get("/api/tasks").status_code == 401


def test_issuer_khac_cau_hinh_thi_tu_choi_dang_nhap(core: FakeCore) -> None:
    sai = FakeKeycloak(issuer="http://evil.example/realms/dxlab")
    app = create_app(
        make_settings(),
        oidc_transport=httpx.MockTransport(sai.handler),
        core_transport=httpx.MockTransport(core.handler),
    )
    client = TestClient(app, base_url=PUBLIC_URL, follow_redirects=False)
    response = client.get("/auth/login")
    assert response.status_code == 502
    assert "issuer" in response.text


def test_keycloak_khong_lien_lac_duoc_thi_bao_loi_tieng_viet(core: FakeCore) -> None:
    def down(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("không kết nối được", request=request)

    app = create_app(
        make_settings(),
        oidc_transport=httpx.MockTransport(down),
        core_transport=httpx.MockTransport(core.handler),
    )
    client = TestClient(app, base_url=PUBLIC_URL, follow_redirects=False)
    response = client.get("/auth/login")
    assert response.status_code == 502
    assert "Keycloak" in response.text


def test_token_het_han_thi_tu_gia_han_bang_refresh_token(core: FakeCore) -> None:
    keycloak = FakeKeycloak(expires_in=10)  # nhỏ hơn biên gia hạn, nên mỗi yêu cầu đều phải gia hạn
    app = create_app(
        make_settings(),
        oidc_transport=httpx.MockTransport(keycloak.handler),
        core_transport=httpx.MockTransport(core.handler),
    )
    client = TestClient(app, base_url=PUBLIC_URL, follow_redirects=False)
    core.routes[("GET", "/api/tasks")] = lambda request: httpx.Response(200, json={"items": [], "total": 0})
    login(client, keycloak)

    assert client.get("/api/tasks").status_code == 200
    refresh_calls = [f for f in keycloak.token_forms if f["grant_type"] == "refresh_token"]
    assert refresh_calls and refresh_calls[0]["refresh_token"] == "refresh-1"
    # Core nhận access token mới (lần phát thứ 2), không phải token lúc đăng nhập (lần phát thứ 1).
    bearer = core.requests[-1].headers["authorization"].removeprefix("Bearer ")
    assert decode_jwt_payload(bearer)["jti"] == "a2"


def test_gia_han_that_bai_thi_phien_bi_huy(core: FakeCore) -> None:
    keycloak = FakeKeycloak(expires_in=10)
    app = create_app(
        make_settings(),
        oidc_transport=httpx.MockTransport(keycloak.handler),
        core_transport=httpx.MockTransport(core.handler),
    )
    client = TestClient(app, base_url=PUBLIC_URL, follow_redirects=False)
    login(client, keycloak)
    keycloak.reject_refresh = True

    response = client.get("/api/tasks")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHENTICATED"
    assert core.requests == []  # không gọi core bằng token đã hết hạn
    assert client.get("/").status_code == 302


def test_dang_xuat_huy_phien_va_chuyen_toi_keycloak_logout(
    client: TestClient, keycloak: FakeKeycloak
) -> None:
    login(client, keycloak)
    response = client.get("/auth/logout")
    assert response.status_code == 303
    location = urlsplit(response.headers["location"])
    assert location.path == "/realms/dxlab/protocol/openid-connect/logout"
    query = parse_qs(location.query)
    assert query["post_logout_redirect_uri"] == [f"{PUBLIC_URL}/auth/logged-out"]
    assert query["id_token_hint"][0].startswith("eyJ")
    # Cookie bị xóa và phiên phía server không còn dùng được nữa.
    assert client.get("/api/tasks").status_code == 401
    assert client.get("/").status_code == 302


@pytest.mark.parametrize("target", ["//evil.example", "https://evil.example", "/\\evil.example"])
def test_next_ngoai_trang_thi_ve_trang_chu(client: TestClient, keycloak: FakeKeycloak, target: str) -> None:
    response = login(client, keycloak, next_path=target)
    assert response.headers["location"] == "/"
