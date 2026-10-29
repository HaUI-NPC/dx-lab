# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

"""Tab và trang "Trạng thái hệ thống": mỗi dịch vụ xanh/đỏ kèm thời gian phản hồi.

Trình duyệt gọi ``GET /ui/status`` khi mở trang, mỗi ``REFRESH_MS`` mili giây và khi bấm "Kiểm tra lại";
việc thăm dò do máy chủ portal làm (``status_probe.py``), nên trang này không cần đăng nhập.
"""

from __future__ import annotations

from prefab_ui.actions import Fetch, SetInterval, SetState, ShowToast
from prefab_ui.app import PrefabApp
from prefab_ui.components import (
    H1,
    Badge,
    Button,
    Card,
    CardContent,
    CardDescription,
    CardHeader,
    CardTitle,
    Column,
    Dot,
    ForEach,
    Link,
    Muted,
    Row,
    Text,
)
from prefab_ui.components.control_flow import If
from prefab_ui.rx import RESULT

STATUS_URL = "/ui/status"
REFRESH_MS = 15000

EMPTY_STATUS = {"checked_at": "", "overall": "Đang kiểm tra…", "has_error": False, "services": []}


def state() -> dict[str, object]:
    return {"status": EMPTY_STATUS}


def _refresh() -> Fetch:
    return Fetch.get(
        STATUS_URL,
        on_success=SetState("status", RESULT),
        on_error=ShowToast("Không lấy được trạng thái hệ thống: {{ $error }}", variant="error"),
    )


def render() -> None:
    with Card(on_mount=[_refresh(), SetInterval(REFRESH_MS, on_tick=_refresh())]):
        with CardHeader():
            CardTitle("Trạng thái hệ thống")
            CardDescription("Kiểm tra từ máy chủ portal; tự làm mới mỗi 15 giây.")
        with CardContent():
            with Column(gap=4):
                with Row(gap=3, align="center"):
                    with If("status.has_error"):
                        Badge("Có lỗi", variant="destructive")
                    Text("{{ status.overall }}", bold=True)
                with ForEach("status.services") as service:
                    with Row(
                        gap=3, align="center", justify="between", css_class="border-b border-border py-2"
                    ):
                        with Row(gap=2, align="center"):
                            Dot(variant=service.variant)
                            with Column(gap=0):
                                Text(service.name, bold=True)
                                Muted(service.detail)
                        with Row(gap=3, align="center"):
                            Muted(service.latency)
                            Badge(service.label, variant=service.variant)
                with Row(gap=3, align="center"):
                    Button("Kiểm tra lại", variant="outline", on_click=_refresh())
                    Muted("Lần kiểm tra gần nhất: {{ status.checked_at }}")


def build_page() -> PrefabApp:
    """Trang ``/status`` độc lập, không cần đăng nhập (dùng để xem khi Keycloak hỏng)."""
    with PrefabApp(title="Trạng thái hệ thống – DX-Lab", css_class="max-w-3xl mx-auto", state=state()) as app:
        with Column(gap=4):
            H1("DX-Lab")
            render()
            Link("Về trang chính", href="/", css_class="text-sm underline underline-offset-4")
    return app
