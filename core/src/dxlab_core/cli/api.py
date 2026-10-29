# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

"""Gọi Core API qua APISIX bằng token của người dùng; đổi lỗi HTTP thành `CliError` dễ đọc."""

from typing import Any

import httpx

from dxlab_core.cli.context import CliError, Context
from dxlab_core.cli.tokens import get_access_token


def api_request(ctx: Context, method: str, path: str, **kwargs: Any) -> httpx.Response:
    """Gọi `{DXLAB_API_URL}{path}` kèm Bearer token; trả phản hồi 2xx, còn lại ném `CliError`."""
    url = f"{ctx.settings.api_url}{path}"
    headers = {"Authorization": f"Bearer {get_access_token(ctx)}", "Accept": "application/json"}
    try:
        response = ctx.client.request(method, url, headers=headers, **kwargs)
    except httpx.HTTPError:
        raise CliError(f"Không kết nối được tới {url}. Kiểm tra stack đã chạy và DXLAB_API_URL.") from None
    if response.is_success:
        return response
    raise api_error(response)


def api_error(response: httpx.Response) -> CliError:
    """Đọc định dạng lỗi chung (CONTRIBUTING.md, "Định dạng lỗi"); `details.errors` in từng dòng."""
    try:
        error = response.json()["error"]
        message = str(error["message"])
    except (ValueError, KeyError, TypeError):
        return CliError(f"Máy chủ trả HTTP {response.status_code} không đúng định dạng lỗi của DX-Lab.")
    code = error.get("code")
    lines = [_format_item(item) for item in (error.get("details") or {}).get("errors") or []]
    if response.status_code == 401:
        lines.append("Chạy `dxlab login` để đăng nhập lại.")
    return CliError(f"{message} [{code}]" if code else message, lines)


def _format_item(item: Any) -> str:
    if not isinstance(item, dict):
        return f"- {item}"
    where = item.get("file") or item.get("path") or ""
    element = item.get("element")
    if where and element:
        where = f"{where} ({element})"
    message = item.get("message", "")
    return f"- {where}: {message}" if where else f"- {message}"
