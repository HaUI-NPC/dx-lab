# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

"""Tab "Báo hỏng": form sinh từ ``GET /api/definitions/lab-repair/start-form``."""

from __future__ import annotations

from typing import Any

from prefab_ui.components import (
    Alert,
    AlertDescription,
    AlertTitle,
    Card,
    CardContent,
    CardHeader,
    CardTitle,
    Muted,
)

from dxlab_portal.bff.core_client import CoreResult
from dxlab_portal.pages.context import PageContext
from dxlab_portal.pages.forms.render import initial_state, render_form
from dxlab_portal.pages.forms.spec import FormSpec, build_form

APP_ID = "lab-repair"
SUBMIT_URL = f"/ui/forms/start/{APP_ID}"


async def load(ctx: PageContext) -> CoreResult:
    """Lấy form khởi tạo từ core; lỗi của core được giữ nguyên để hiện cho người dùng, không dựng form giả."""
    return await ctx.core.call("GET", f"/definitions/{APP_ID}/start-form", token=ctx.access_token)


def _spec(result: CoreResult) -> FormSpec | None:
    if not result.ok or not isinstance(result.json, dict):
        return None
    return build_form(result.json.get("schema") or {}, result.json.get("uischema"))


def state(result: CoreResult) -> dict[str, Any]:
    spec = _spec(result)
    return initial_state(spec) if spec else {}


def render(result: CoreResult) -> None:
    spec = _spec(result)
    with Card():
        with CardHeader():
            CardTitle("Báo hỏng thiết bị")
        with CardContent():
            if spec is None:
                with Alert(variant="destructive"):
                    AlertTitle("Chưa tải được form báo hỏng")
                    AlertDescription(result.error_message())
                    error = result.error or {}
                    code = error.get("code", result.status)
                    request_id = error.get("request_id") or result.request_id or "—"
                    Muted(f"Mã lỗi: {code} · Mã yêu cầu: {request_id}")
                return
            render_form(
                spec,
                submit_url=SUBMIT_URL,
                submit_label="Gửi phiếu báo hỏng",
                success_title="Đã gửi phiếu báo hỏng",
                again_label="Báo hỏng thiết bị khác",
                again_href="/?tab=report",
            )
