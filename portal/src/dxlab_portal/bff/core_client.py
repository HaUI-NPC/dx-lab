# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

"""Gọi Core API qua APISIX (``DXLAB_API_URL``), luôn kèm token của chính người dùng."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import httpx

from dxlab_portal.bff.probe import ProbeResult, timed_get

log = logging.getLogger("dxlab_portal.core")

# Header không chuyển tiếp: do hop-by-hop, hoặc httpx/ASGI tự quản.
_HOP_BY_HOP = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailers",
    "transfer-encoding",
    "upgrade",
    "content-length",
    "content-encoding",
    "host",
}


def strip_hop_by_hop(headers: httpx.Headers | dict[str, str]) -> dict[str, str]:
    return {k: v for k, v in headers.items() if k.lower() not in _HOP_BY_HOP}


@dataclass(frozen=True)
class CoreResult:
    """Kết quả một lời gọi core: HTTP status và JSON (hoặc ``None`` nếu không phải JSON, khi đó ``text`` giữ thân gốc)."""

    status: int
    json: Any
    request_id: str | None = None
    text: str | None = None

    @property
    def ok(self) -> bool:
        return 200 <= self.status < 300

    @property
    def error(self) -> dict[str, Any] | None:
        """Phần ``error`` theo định dạng lỗi chung của core, nếu có."""
        if isinstance(self.json, dict) and isinstance(self.json.get("error"), dict):
            return self.json["error"]  # type: ignore[no-any-return]
        return None

    def error_message(self) -> str:
        """Thông điệp lỗi hiển thị cho người dùng, giữ nguyên ``message`` của core."""
        error = self.error
        if error and error.get("message"):
            return str(error["message"])
        return f"Core trả mã {self.status} không theo định dạng lỗi chung."


class CoreClient:
    """Máy khách HTTP dùng chung cho proxy ``/api`` và các trang render phía server."""

    def __init__(
        self,
        base_url: str,
        *,
        transport: httpx.AsyncBaseTransport | None = None,
        timeout: float = 15.0,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._transport = transport
        self._http = httpx.AsyncClient(transport=transport, timeout=timeout)

    def url_for(self, path: str) -> str:
        return f"{self._base_url}/{path.lstrip('/')}"

    async def probe(self, path: str) -> ProbeResult:
        """Thăm dò một đường dẫn không cần token, đo thời gian phản hồi."""
        return await timed_get(self.url_for(path), self._transport)

    async def aclose(self) -> None:
        await self._http.aclose()

    async def forward(
        self,
        method: str,
        path: str,
        *,
        token: str | None,
        params: Any = None,
        content: bytes | None = None,
        headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        """Gửi nguyên một lời gọi tới core; ném ``httpx.HTTPError`` khi không tới được."""
        out_headers = dict(headers or {})
        if token:
            out_headers["Authorization"] = f"Bearer {token}"
        request = self._http.build_request(
            method, self.url_for(path), params=params, content=content, headers=out_headers
        )
        return await self._http.send(request)

    async def call(
        self,
        method: str,
        path: str,
        *,
        token: str | None,
        params: Any = None,
        json: Any = None,
    ) -> CoreResult:
        """Gọi core và trả ``CoreResult``; không tới được core thì status 502 theo định dạng lỗi chung."""
        try:
            request = self._http.build_request(
                method,
                self.url_for(path),
                params=params,
                json=json,
                headers={"Authorization": f"Bearer {token}"} if token else None,
            )
            response = await self._http.send(request)
        except httpx.HTTPError as exc:
            log.warning("core_unreachable path=%s err=%s", path, type(exc).__name__)
            return CoreResult(
                status=502,
                json={
                    "error": {
                        "code": "INTERNAL",
                        "message": "Không kết nối được Core API qua cổng API. Thử lại sau ít phút.",
                        "details": {},
                        "request_id": None,
                    }
                },
            )
        try:
            body = response.json() if response.content else None
        except ValueError:
            body = None
        text = response.text if body is None and response.content else None
        return CoreResult(response.status_code, body, response.headers.get("x-request-id"), text)
