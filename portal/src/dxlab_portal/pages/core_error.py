# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

"""Hiện lỗi của core nguyên văn (``message``, ``code``, ``request_id``), không dựng dữ liệu thay thế."""

from __future__ import annotations

from prefab_ui.components import Alert, AlertDescription, AlertTitle, Muted

from dxlab_portal.bff.core_client import CoreResult


def render_core_error(title: str, result: CoreResult) -> None:
    error = result.error or {}
    code = error.get("code", result.status)
    request_id = error.get("request_id") or result.request_id or "—"
    with Alert(variant="destructive"):
        AlertTitle(title)
        AlertDescription(result.error_message())
        Muted(f"Mã lỗi: {code} · Mã yêu cầu: {request_id}")
