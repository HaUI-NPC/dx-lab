# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

"""Proxy ``/api/{path}`` → ``DXLAB_API_URL`` kèm ``Authorization: Bearer`` của người đăng nhập."""

from __future__ import annotations

import logging
import uuid
from urllib.parse import urlsplit

import httpx
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, Response

from dxlab_portal.bff.core_client import strip_hop_by_hop
from dxlab_portal.bff.state import current_session, portal_state

log = logging.getLogger("dxlab_portal.proxy")
router = APIRouter(include_in_schema=False)

_SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}
# Chỉ chuyển tiếp các header yêu cầu cần thiết cho nghiệp vụ; cookie và Authorization của trình duyệt bị bỏ.
_FORWARD_REQUEST_HEADERS = {"accept", "accept-language", "content-type", "if-match", "x-request-id"}


def error_response(status: int, code: str, message: str) -> JSONResponse:
    """Lỗi do chính portal sinh ra, cùng định dạng lỗi với core (CONTRIBUTING: Định dạng lỗi)."""
    request_id = str(uuid.uuid4())
    return JSONResponse(
        {"error": {"code": code, "message": message, "details": {}, "request_id": request_id}},
        status_code=status,
        headers={"X-Request-Id": request_id},
    )


def _same_origin(request: Request, public_url: str) -> bool:
    """Chặn yêu cầu ghi từ trang khác: nếu có ``Origin`` thì phải trùng địa chỉ công khai của portal."""
    origin = request.headers.get("origin")
    if origin is None:
        return True
    expected = urlsplit(public_url)
    given = urlsplit(origin)
    return (given.scheme, given.netloc) == (expected.scheme, expected.netloc)


@router.api_route("/api/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"], name="api_proxy")
async def api_proxy(path: str, request: Request) -> Response:
    state = portal_state(request)
    if request.method not in _SAFE_METHODS and not _same_origin(request, state.settings.public_url):
        return error_response(
            403, "FORBIDDEN_ORIGIN", "Yêu cầu ghi bị từ chối vì không xuất phát từ trang của portal."
        )
    session = await current_session(request)
    if session is None:
        return error_response(
            401, "UNAUTHENTICATED", "Chưa đăng nhập hoặc phiên đã hết hạn. Vui lòng đăng nhập lại."
        )
    headers = {k: v for k, v in request.headers.items() if k.lower() in _FORWARD_REQUEST_HEADERS}
    body = await request.body()
    try:
        upstream = await state.core.forward(
            request.method,
            path,
            token=session.access_token,
            params=list(request.query_params.multi_items()),
            content=body or None,
            headers=headers,
        )
    except httpx.TimeoutException:
        return error_response(504, "INTERNAL", "Core API không phản hồi kịp. Thử lại sau ít phút.")
    except httpx.HTTPError as exc:
        log.warning("upstream_unreachable path=%s err=%s", path, type(exc).__name__)
        return error_response(502, "INTERNAL", "Không kết nối được Core API qua cổng API.")
    return Response(
        content=upstream.content,
        status_code=upstream.status_code,
        headers={k: v for k, v in strip_hop_by_hop(upstream.headers).items() if k.lower() != "set-cookie"},
    )
