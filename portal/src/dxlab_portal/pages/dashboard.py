# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

"""Tab "Dashboard": số liệu tổng hợp từ ``GET /api/stats`` (không có tên người, AUTHZ §8).

Hợp đồng dữ liệu::

    {"by_status": [{"status", "status_name", "count"}], "by_unit": [{"unit", "count"}],
     "overdue": n, "cost": {"approved_total", "actual_total"}}
"""

from __future__ import annotations

from typing import Any

from prefab_ui.components import (
    Card,
    CardContent,
    CardHeader,
    CardTitle,
    Column,
    DataTable,
    DataTableColumn,
    Grid,
    Metric,
    Muted,
)
from prefab_ui.components.charts import BarChart, ChartSeries

from dxlab_portal.bff.core_client import CoreResult
from dxlab_portal.pages.context import PageContext
from dxlab_portal.pages.core_error import render_core_error


async def load(ctx: PageContext) -> CoreResult:
    return await ctx.core.call("GET", "/stats", token=ctx.access_token)


def format_vnd(amount: Any) -> str:
    """Số tiền nguyên (đồng) theo kiểu Việt Nam: ``3.500.000 ₫``; không có số thì ``—``.

    Trước ``₫`` là dấu cách không ngắt dòng để số và ký hiệu không bị tách ra hai dòng.
    """
    if isinstance(amount, bool) or not isinstance(amount, int | float):
        return "—"
    return f"{int(amount):,}".replace(",", ".") + "\u00a0₫"


def _rows(stats: dict[str, Any], key: str) -> list[dict[str, Any]]:
    value = stats.get(key)
    return [row for row in value if isinstance(row, dict)] if isinstance(value, list) else []


def render(result: CoreResult) -> None:
    if not result.ok or not isinstance(result.json, dict):
        render_core_error("Chưa tải được số liệu dashboard", result)
        return
    stats = result.json
    by_status = _rows(stats, "by_status")
    by_unit = _rows(stats, "by_unit")
    cost = stats.get("cost") if isinstance(stats.get("cost"), dict) else {}
    total = sum(int(r.get("count", 0)) for r in by_status)
    overdue = stats.get("overdue")
    with Column(gap=4):
        with Grid(columns={"default": 1, "md": 2, "lg": 4}, gap=4):
            for label, value in (
                ("Tổng số phiếu", str(total)),
                ("Phiếu quá hạn", str(overdue) if isinstance(overdue, int) else "—"),
                ("Chi phí đã duyệt", format_vnd(cost.get("approved_total"))),
                ("Chi phí thực tế", format_vnd(cost.get("actual_total"))),
            ):
                with Card(css_class="p-6"):
                    Metric(label=label, value=value)
        with Card():
            with CardHeader():
                CardTitle("Số phiếu theo trạng thái")
            with CardContent():
                if by_status:
                    BarChart(
                        data=[
                            {
                                "trang_thai": r.get("status_name") or r.get("status"),
                                "so_phieu": r.get("count", 0),
                            }
                            for r in by_status
                        ],
                        series=[ChartSeries(data_key="so_phieu", label="Số phiếu")],
                        x_axis="trang_thai",
                        height=260,
                        show_legend=False,
                    )
                else:
                    Muted("Chưa có phiếu nào.")
        with Card():
            with CardHeader():
                CardTitle("Số phiếu theo đơn vị")
            with CardContent():
                if by_unit:
                    DataTable(
                        columns=[
                            DataTableColumn(key="unit", header="Đơn vị", sortable=True),
                            DataTableColumn(key="count", header="Số phiếu", sortable=True, align="right"),
                        ],
                        rows=[{"unit": r.get("unit", ""), "count": r.get("count", 0)} for r in by_unit],
                    )
                else:
                    Muted("Chưa có số liệu theo đơn vị.")
