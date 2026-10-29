# SPDX-FileCopyrightText: 2026 DX-Lab contributors
# SPDX-License-Identifier: Apache-2.0

"""Công cụ MCP; mọi quyết định phân quyền đều thuộc API core qua gateway."""

import json
import os
import stat
import time
from pathlib import Path
from typing import Any
from urllib.parse import quote

import httpx
from fastmcp import Context, FastMCP
from mcp.types import ToolAnnotations

mcp = FastMCP("DX-Lab")


def _token() -> str:
    path = Path(os.environ.get("DXLAB_TOKEN_FILE", "~/.config/dxlab/token.json")).expanduser()
    try:
        with path.open(encoding="utf-8") as file:
            if stat.S_IMODE(os.fstat(file.fileno()).st_mode) & 0o077:
                raise ValueError("Tệp token phải chỉ cho phép chủ sở hữu truy cập (0600).")
            token = json.load(file)
        if not isinstance(token, dict) or not isinstance(token.get("access_token"), str) or not token["access_token"]:
            raise ValueError("Tệp token không chứa access_token hợp lệ.")
        if float(token["expires_at"]) <= time.time() + 30:
            raise ValueError("Token đã hết hạn hoặc sắp hết hạn; chạy dxlab login để đăng nhập lại.")
        return token["access_token"]
    except (OSError, KeyError, TypeError, json.JSONDecodeError) as exc:
        raise ValueError("Không đọc được token; hãy chạy dxlab login.") from exc


async def _request(method: str, path: str, *, data: dict[str, Any] | None = None,
                   params: dict[str, Any] | None = None) -> Any:
    url = os.environ.get("DXLAB_API_URL", "http://localhost:9080/api").rstrip("/")
    async with httpx.AsyncClient(timeout=30.0, follow_redirects=False) as client:
        response = await client.request(method, url + path, headers={"Authorization": f"Bearer {_token()}"},
                                        json=data, params=params)
    if response.is_error:
        try:
            error = response.json()
        except ValueError:
            error = {"message": response.text[:500]}
        raise ValueError(f"Gateway trả lỗi HTTP {response.status_code}: {json.dumps(error, ensure_ascii=False)}")
    return response.json()


async def _confirm(ctx: Context, message: str) -> None:
    result = await ctx.elicit(message, response_type=bool)
    if result.action != "accept" or result.data is not True:
        raise ValueError("Thao tác đã bị hủy; không có dữ liệu nào được gửi.")


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False, openWorldHint=True))
async def bao_hong(data: dict[str, Any], ctx: Context) -> Any:
    """Tạo phiếu lab-repair với dữ liệu theo form; luôn hỏi người dùng trước khi gửi."""
    await _confirm(ctx, "Xác nhận gửi phiếu báo hỏng với dữ liệu sau?\n" + json.dumps(data, ensure_ascii=False))
    return await _request("POST", "/workflows", data={"app_id": "lab-repair", "data": data})


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=True))
async def viec_cua_toi() -> Any:
    """Xem hộp việc của người đang đăng nhập."""
    return await _request("GET", "/tasks")


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=True))
async def tra_cuu_phieu(workflow_id: str) -> Any:
    """Xem chi tiết và lịch sử phiếu theo mã workflow."""
    return await _request("GET", "/workflows/" + quote(workflow_id, safe=""))


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=True))
async def tim_huong_dan(query: str) -> Any:
    """Tìm hướng dẫn cùng trích dẫn nguồn, theo quyền của người dùng."""
    return await _request("GET", "/search", params={"q": query})


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=True, openWorldHint=True))
async def hoan_thanh_viec(task_id: str, data: dict[str, Any], ctx: Context) -> Any:
    """Hoàn thành một bước sau khi người dùng xác nhận; core kiểm tra quyền và không kiêm nhiệm."""
    await _confirm(ctx, f"Xác nhận hoàn thành việc {task_id} với dữ liệu sau?\n" + json.dumps(data, ensure_ascii=False))
    return await _request("POST", "/tasks/" + quote(task_id, safe="") + "/complete", data={"data": data})


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
