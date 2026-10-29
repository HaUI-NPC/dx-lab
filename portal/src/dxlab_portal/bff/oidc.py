# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

"""Đăng nhập OIDC (authorization code + PKCE S256) bằng Authlib.

Trình duyệt đi tới Keycloak bằng URL công khai (``DXLAB_OIDC_ISSUER``); portal gọi token, JWKS bằng kênh
nội bộ (``DXLAB_OIDC_INTERNAL_URL``). ``iss`` của id_token phải đúng ``DXLAB_OIDC_ISSUER``.
"""

from __future__ import annotations

import base64
import json
import logging
import time
from typing import Any

import httpx
from authlib.integrations.starlette_client import OAuth
from authlib.integrations.starlette_client.apps import StarletteOAuth2App

from dxlab_portal.bff.probe import ProbeResult, timed_get
from dxlab_portal.config import Settings

log = logging.getLogger("dxlab_portal.oidc")

# Đổi refresh token sớm hơn hạn access token để lời gọi tới core không dùng token vừa hết hạn.
REFRESH_MARGIN_SECONDS = 30


class OidcError(Exception):
    """Lỗi đăng nhập hoặc gia hạn token; ``message`` là tiếng Việt, hiển thị được cho người dùng."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class OidcClient:
    """Bọc client Authlib và các thao tác phiên (gia hạn token, đọc claim)."""

    def __init__(self, settings: Settings, *, transport: httpx.AsyncBaseTransport | None = None):
        self._settings = settings
        self._transport = transport
        client_kwargs: dict[str, Any] = {
            "scope": "openid profile email",
            "code_challenge_method": "S256",
        }
        if transport is not None:
            client_kwargs["transport"] = transport
        self._oauth = OAuth()
        self._oauth.register(
            name="keycloak",
            client_id=settings.client_id,
            client_secret=settings.client_secret.get_secret_value(),
            server_metadata_url=settings.discovery_url,
            client_kwargs=client_kwargs,
        )

    @property
    def app(self) -> StarletteOAuth2App:
        return self._oauth.keycloak  # type: ignore[no-any-return]

    async def metadata(self) -> dict[str, Any]:
        """Nạp discovery và kiểm ``issuer`` khớp ``DXLAB_OIDC_ISSUER``."""
        try:
            metadata = await self.app.load_server_metadata()
        except (httpx.HTTPError, ValueError) as exc:
            log.warning("oidc_discovery_failed url=%s err=%s", self._settings.discovery_url, exc)
            raise OidcError("Không kết nối được máy chủ đăng nhập (Keycloak). Thử lại sau ít phút.") from exc
        issuer = str(metadata.get("issuer", "")).rstrip("/")
        if issuer != self._settings.oidc_issuer:
            log.error("oidc_issuer_mismatch expected=%s got=%s", self._settings.oidc_issuer, issuer)
            raise OidcError(
                "Máy chủ đăng nhập báo issuer khác cấu hình DXLAB_OIDC_ISSUER; từ chối đăng nhập."
            )
        return metadata

    async def probe(self) -> ProbeResult:
        """Thăm dò discovery (kênh nội bộ), không dùng bộ nhớ đệm của Authlib."""
        return await timed_get(self._settings.discovery_url, self._transport)

    async def refresh(self, refresh_token: str) -> dict[str, Any]:
        """Đổi refresh token lấy token mới; ``OidcError`` nếu Keycloak từ chối."""
        metadata = await self.metadata()
        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": self._settings.client_id,
            "client_secret": self._settings.client_secret.get_secret_value(),
        }
        try:
            async with httpx.AsyncClient(transport=self._transport, timeout=10.0) as http:
                response = await http.post(metadata["token_endpoint"], data=data)
        except httpx.HTTPError as exc:
            raise OidcError("Không kết nối được máy chủ đăng nhập để gia hạn phiên.") from exc
        if response.status_code != 200:
            raise OidcError("Phiên đăng nhập đã hết hạn, vui lòng đăng nhập lại.")
        token: dict[str, Any] = response.json()
        token.setdefault("expires_at", time.time() + float(token.get("expires_in", 300)))
        return token


def decode_jwt_payload(token: str | None) -> dict[str, Any]:
    """Đọc payload của JWT **không kiểm chữ ký**; chỉ dùng để hiển thị claim, quyền do core quyết định."""
    if not token or token.count(".") != 2:
        return {}
    payload = token.split(".")[1]
    payload += "=" * (-len(payload) % 4)
    try:
        value = json.loads(base64.urlsafe_b64decode(payload))
    except (ValueError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def merge_claims(userinfo: dict[str, Any] | None, access_token: str | None) -> dict[str, Any]:
    """Gộp claim id_token (đã kiểm chữ ký) với claim hiển thị còn thiếu từ access token."""
    claims = dict(userinfo or {})
    access = decode_jwt_payload(access_token)
    for key in ("groups", "name", "preferred_username"):
        if key not in claims and key in access:
            claims[key] = access[key]
    return claims
