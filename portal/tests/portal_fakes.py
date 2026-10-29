# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

"""Keycloak và core giả lập qua ``httpx.MockTransport``; portal chạy thật phía trước.

Tên module riêng (không phải ``conftest``) để không đụng test của ``core`` khi chạy cả workspace."""

from __future__ import annotations

import base64
import hashlib
import json
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlsplit

import httpx
import pytest
from dxlab_portal.config import Settings
from fastapi.testclient import TestClient
from joserfc import jwt
from joserfc.jwk import RSAKey

ISSUER = "http://localhost:8180/realms/dxlab"
INTERNAL = "http://keycloak:8080/realms/dxlab"
PUBLIC_URL = "http://localhost:8001"
CLIENT_SECRET = "bi-mat-cua-client-portal"
GROUPS = ["/haui/sict/khmt/lab-a1-305/lab_manager"]


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


class FakeKeycloak:
    """Máy chủ OIDC tối thiểu: discovery, JWKS, token (authorization_code + refresh_token)."""

    def __init__(self, *, issuer: str = ISSUER, expires_in: int = 300) -> None:
        self.issuer = issuer
        self.expires_in = expires_in
        self.key = RSAKey.generate_key(2048, parameters={"kid": "test-key", "use": "sig"})
        self.requests: list[httpx.Request] = []
        self.token_forms: list[dict[str, str]] = []
        self.codes: dict[str, dict[str, str]] = {}
        self.issued = 0
        self.reject_refresh = False

    def authorize_request(self, location: str) -> dict[str, str]:
        """Ghi nhận yêu cầu /authorize từ URL chuyển hướng của portal, trả về một ``code`` hợp lệ."""
        query = {k: v[0] for k, v in parse_qs(urlsplit(location).query).items()}
        code = f"code-{len(self.codes) + 1}"
        self.codes[code] = query
        return {"code": code, "state": query["state"]}

    def _tokens(self, nonce: str | None, *, with_id_token: bool = True) -> dict[str, Any]:
        self.issued += 1
        now = int(time.time())
        base = {
            "iss": self.issuer,
            "sub": "u-giang",
            "preferred_username": "tl.giang",
            "name": "Hoàng Thu Giang",
            "groups": GROUPS,
            "aud": ["dxlab-portal", "dxlab-core"],
            "exp": now + self.expires_in,
            "iat": now,
        }
        header = {"alg": "RS256", "kid": "test-key"}
        token: dict[str, Any] = {
            "access_token": jwt.encode(header, {**base, "typ": "Bearer", "jti": f"a{self.issued}"}, self.key),
            "refresh_token": f"refresh-{self.issued}",
            "token_type": "Bearer",
            "expires_in": self.expires_in,
        }
        if with_id_token:
            id_claims = {**base, "aud": "dxlab-portal", "azp": "dxlab-portal"}
            if nonce:
                id_claims["nonce"] = nonce
            token["id_token"] = jwt.encode(header, id_claims, self.key)
        return token

    def handler(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        path = request.url.path
        if path.endswith("/.well-known/openid-configuration"):
            return httpx.Response(
                200,
                json={
                    "issuer": self.issuer,
                    "authorization_endpoint": f"{ISSUER}/protocol/openid-connect/auth",
                    "end_session_endpoint": f"{ISSUER}/protocol/openid-connect/logout",
                    "token_endpoint": f"{INTERNAL}/protocol/openid-connect/token",
                    "jwks_uri": f"{INTERNAL}/protocol/openid-connect/certs",
                    "id_token_signing_alg_values_supported": ["RS256"],
                },
            )
        if path.endswith("/certs"):
            return httpx.Response(200, json={"keys": [self.key.as_dict(private=False)]})
        if path.endswith("/token"):
            form = {k: v[0] for k, v in parse_qs(request.content.decode()).items()}
            auth = request.headers.get("authorization")
            if auth:  # client_secret_basic
                user, _, secret = base64.b64decode(auth.split()[1]).decode().partition(":")
                form.setdefault("client_id", user)
                form.setdefault("client_secret", secret)
            self.token_forms.append(form)
            if form.get("client_secret") != CLIENT_SECRET:
                return httpx.Response(401, json={"error": "unauthorized_client"})
            if form["grant_type"] == "authorization_code":
                original = self.codes.get(form.get("code", ""))
                if original is None:
                    return httpx.Response(400, json={"error": "invalid_grant"})
                challenge = _b64(hashlib.sha256(form["code_verifier"].encode()).digest())
                if challenge != original["code_challenge"]:
                    return httpx.Response(400, json={"error": "invalid_grant", "error_description": "PKCE"})
                return httpx.Response(200, json=self._tokens(original.get("nonce")))
            if form["grant_type"] == "refresh_token":
                if self.reject_refresh or not form.get("refresh_token", "").startswith("refresh-"):
                    return httpx.Response(400, json={"error": "invalid_grant"})
                return httpx.Response(200, json=self._tokens(None))
        return httpx.Response(404)


class FakeCore:
    """Core giả lập: ghi lại các lời gọi, trả theo bảng ``routes``."""

    def __init__(self) -> None:
        self.requests: list[httpx.Request] = []
        self.routes: dict[tuple[str, str], Callable[[httpx.Request], httpx.Response]] = {}

    def handler(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        route = self.routes.get((request.method, request.url.path))
        if route is None:
            return httpx.Response(
                404,
                json={
                    "error": {
                        "code": "NOT_FOUND",
                        "message": "Không có tài nguyên.",
                        "details": {},
                        "request_id": "r-404",
                    }
                },
            )
        return route(request)


def make_settings(**overrides: Any) -> Settings:
    values: dict[str, Any] = {
        "DXLAB_PORTAL_PUBLIC_URL": PUBLIC_URL,
        "DXLAB_PORTAL_CLIENT_SECRET": CLIENT_SECRET,
        "DXLAB_PORTAL_SESSION_SECRET": "khoa-ky-cookie-phien-cho-test-0123456789",
        "DXLAB_OIDC_ISSUER": ISSUER,
        "DXLAB_OIDC_INTERNAL_URL": INTERNAL,
        "DXLAB_API_URL": "http://apisix:9080/api",
    }
    values.update(overrides)
    return Settings(**values)  # type: ignore[arg-type]


def login(client: TestClient, keycloak: FakeKeycloak, next_path: str = "/") -> httpx.Response:
    """Đi hết luồng đăng nhập; trả về phản hồi của /auth/callback."""
    start = client.get("/auth/login", params={"next": next_path})
    assert start.status_code == 302, start.text
    params = keycloak.authorize_request(start.headers["location"])
    return client.get("/auth/callback", params=params)


def prefab_wire(html: str) -> dict[str, Any]:
    """Tách JSON mô tả giao diện (wire format Prefab) nhúng trong trang."""
    # Khối JS của renderer cũng chứa chuỗi này, nên lấy lần xuất hiện cuối cùng (thẻ thật ở cuối trang).
    marker = '<script id="prefab:initial-data" type="application/json">'
    start = html.rindex(marker) + len(marker)
    wire: dict[str, Any] = json.loads(html[start : html.index("</script>", start)].replace(r"<\/", "</"))
    return wire


def markup_outside_renderer(html: str) -> str:
    """HTML bỏ khối JS nội tuyến của renderer.

    Vite escape `</script>` trong JS, nên `</script>` đầu tiên là thẻ đóng thật.
    """
    first_script = html.index("<script")
    return html[:first_script] + html[html.index("</script>", first_script) + len("</script>") :]


def prefab_strings(node: Any) -> list[str]:
    """Mọi chuỗi trong cây giao diện, theo thứ tự gặp."""
    if isinstance(node, str):
        return [node]
    if isinstance(node, list):
        return [s for item in node for s in prefab_strings(item)]
    if isinstance(node, dict):
        return [s for value in node.values() for s in prefab_strings(value)]
    return []


def prefab_text(html: str) -> str:
    return "\n".join(prefab_strings(prefab_wire(html)["view"]))


REPO_ROOT = Path(__file__).resolve().parents[2]


def load_app_json(app_id: str, filename: str) -> dict[str, Any]:
    """Đọc tệp schema thật của gói ứng dụng ở ``apps/<app_id>/`` (APP-02).

    Chưa có trên nhánh (APP-02 chưa vào main) thì bỏ qua test cần tệp đó.
    """
    path = REPO_ROOT / "apps" / app_id / filename
    if not path.exists():
        pytest.skip(f"{path.relative_to(REPO_ROOT)} chưa có trên nhánh này (APP-02 chưa vào main)")
    data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    return data


VALID_REPORT: dict[str, Any] = {
    "reporter_name": "Hoàng Thu Giang",
    "reporter_id": "GV0305",
    "reporter_phone": "0912345678",
    "reporter_email": "giang@example.vn",
    "room_id": "lab-a1-305",
    "asset_id": "AST-PROJ-305-01",
    "asset_category": "projector",
    "issue_title": "Máy chiếu không lên hình",
    "issue_description": "Bật máy chiếu thì đèn báo nhấp nháy đỏ, không có hình.",
    "urgency": "high",
    "data_processing_consent": True,
}
