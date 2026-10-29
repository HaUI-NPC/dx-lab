# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

"""Khung trang: tiêu đề, người đăng nhập và các tab."""

from __future__ import annotations

from collections.abc import Callable

from prefab_ui.app import PrefabApp
from prefab_ui.components import (
    H1,
    Badge,
    Column,
    Link,
    Muted,
    Row,
    Tab,
    Tabs,
    Text,
)

from dxlab_portal.pages import dashboard, lookup, my_tasks, report, status
from dxlab_portal.pages.context import PageContext

# (mã tab, tiêu đề tiếng Việt, hàm dựng nội dung). Thứ tự ở đây là thứ tự hiển thị.
TABS: list[tuple[str, str, Callable[[], None]]] = [
    ("tasks", "Việc của tôi", my_tasks.render),
    ("report", "Báo hỏng", report.render),
    ("lookup", "Tra cứu", lookup.render),
    ("dashboard", "Dashboard", dashboard.render),
    ("status", "Trạng thái hệ thống", status.render),
]
DEFAULT_TAB = TABS[0][0]


def build_page(ctx: PageContext) -> PrefabApp:
    """Dựng trang chính cho người đã đăng nhập."""
    tab_ids = {tab_id for tab_id, _, _ in TABS}
    active = ctx.tab if ctx.tab in tab_ids else DEFAULT_TAB
    with PrefabApp(title="DX-Lab", css_class="max-w-5xl mx-auto") as app:
        with Column(gap=6):
            with Row(gap=4, align="center", justify="between"):
                H1("DX-Lab")
                with Row(gap=3, align="center"):
                    with Column(gap=1, align="end"):
                        Text(ctx.user.name, bold=True)
                        Muted(f"@{ctx.user.username}")
                    with Row(gap=1, align="center"):
                        for label in ctx.user.role_labels:
                            Badge(label, variant="secondary")
                    Link(
                        "Đăng xuất",
                        href="/auth/logout",
                        css_class="text-sm whitespace-nowrap underline underline-offset-4",
                    )
            with Tabs(value=active):
                for tab_id, title, render in TABS:
                    with Tab(title, value=tab_id):
                        render()
    return app


def render_html(ctx: PageContext) -> str:
    """HTML đầy đủ với renderer Prefab đóng gói sẵn trong gói ``prefab-ui``: không CDN, không Node."""
    html = build_page(ctx).html(renderer_mode="bundled")
    return html.replace('<html lang="en">', '<html lang="vi">', 1)
