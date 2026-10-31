# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

"""Khung trang: tiêu đề, người đăng nhập và các tab."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

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

from dxlab_portal.pages import dashboard, diagram, lookup, my_tasks, report, status
from dxlab_portal.pages.context import PageContext


@dataclass(frozen=True)
class TabDef:
    """Một tab. Tab cần dữ liệu từ core khai báo ``load`` (chạy song song trước khi dựng trang);
    ``render`` nhận kết quả của ``load``. ``state`` (tùy chọn) cho trạng thái Prefab ban đầu của tab."""

    id: str
    title: str
    render: Callable[..., None]
    load: Callable[[PageContext], Awaitable[Any]] | None = None
    state: Callable[[Any], dict[str, Any]] | None = None


# Thứ tự ở đây là thứ tự hiển thị.
TABS: list[TabDef] = [
    TabDef("tasks", "Việc của tôi", my_tasks.render, my_tasks.load, my_tasks.state),
    TabDef("report", "Báo hỏng", report.render, report.load, report.state),
    TabDef("lookup", "Tra cứu", lookup.render, state=lookup.state),
    TabDef("dashboard", "Dashboard", dashboard.render, dashboard.load),
    TabDef("diagram", "Sơ đồ quy trình", diagram.render, diagram.load),
    TabDef("status", "Trạng thái hệ thống", status.render, state=lambda _: status.state()),
]
DEFAULT_TAB = TABS[0].id


async def load_tabs(ctx: PageContext) -> dict[str, Any]:
    """Chạy song song ``load`` của các tab."""
    loaders = [t for t in TABS if t.load is not None]
    results = await asyncio.gather(*(t.load(ctx) for t in loaders))  # type: ignore[misc]
    return {t.id: r for t, r in zip(loaders, results, strict=True)}


def build_page(ctx: PageContext, data: dict[str, Any]) -> PrefabApp:
    """Dựng trang chính cho người đã đăng nhập; ``data`` là kết quả của ``load_tabs``."""
    active = ctx.tab if ctx.tab in {t.id for t in TABS} else DEFAULT_TAB
    state: dict[str, Any] = {}
    for tab in TABS:
        if tab.state is not None:
            state.update(tab.state(data.get(tab.id)))
    with PrefabApp(title="DX-Lab", css_class="max-w-5xl mx-auto", state=state or None) as app:
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
                for tab in TABS:
                    with Tab(tab.title, value=tab.id):
                        tab.render(data[tab.id]) if tab.load else tab.render()
    return app


def render_prefab_html(app: PrefabApp) -> str:
    """HTML đầy đủ với renderer Prefab đóng gói sẵn trong ``prefab-ui``: không CDN, không Node."""
    html = app.html(renderer_mode="bundled")
    return html.replace('<html lang="en">', '<html lang="vi">', 1)


def render_html(ctx: PageContext, data: dict[str, Any]) -> str:
    return render_prefab_html(build_page(ctx, data))
