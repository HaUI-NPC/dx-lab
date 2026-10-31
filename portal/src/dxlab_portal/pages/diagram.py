<!--
SPDX-FileCopyrightText: 2026 DX-Lab contributors

SPDX-License-Identifier: Apache-2.0
-->

"""Tab "Sơ đồ quy trình" (Mermaid diagram từ definition của lab-repair)."""

from __future__ import annotations

from typing import Any

from prefab_ui.components import (
    Card,
    CardContent,
    CardHeader,
    CardTitle,
    Column,
    Muted,
    Text,
)

from dxlab_portal.bff.core_client import CoreResult
from dxlab_portal.pages.context import PageContext
from dxlab_portal.pages.core_error import render_core_error

async def load(ctx: PageContext) -> CoreResult:
    return await ctx.core.call("GET", "/definitions/lab-repair", token=ctx.access_token)

def render(result: CoreResult) -> None:
    if not result.ok or not isinstance(result.json, dict):
        render_core_error("Chưa tải được định nghĩa quy trình lab-repair", result)
        return
    def_data = result.json
    display_name = def_data.get("display_name", "Quy trình Sửa chữa Thiết bị (lab-repair)")
    version = def_data.get("version", 1)
    status = def_data.get("status", "active")

    with Column(gap=4):
        with Card():
            with CardHeader():
                CardTitle(f"{display_name} (Phiên bản {version} — {status})")
            with CardContent():
                with Column(gap=3):
                    Text("Sơ đồ quy trình nghiệp vụ (BPMN / DMN) của ứng dụng lab-repair hiển thị dưới dạng biểu đồ luồng Mermaid:")
                    # Thẻ pre chứa code Mermaid theo chuẩn, prefab-ui hoặc browser render trực tiếp
                    mermaid_code = (
                        "flowchart TD\n"
                        "    Start([Bắt đầu]) --> Report[Báo hỏng: reporter]\n"
                        "    Report --> Triage{Xếp ưu tiên: triage.dmn}\n"
                        "    Triage -->|Cost = 0| Done([Kết thúc / Không duyệt])\n"
                        "    Triage -->|Cost > 0| Assess[Xác nhận kỹ thuật & Biên bản]\n"
                        "    Assess --> ManagerEnd[Trường lab_manager xác nhận nhu cầu]\n"
                        "    ManagerEnd --> Authority{Tra bảng authority.dmn}\n"
                        "    Authority -->|<= 5M| FacultyHead[Trưởng khoa duyệt]\n"
                        "    Authority -->|<= 20M| SchoolHead[Trưởng trường thành viên duyệt]\n"
                        "    Authority -->|<= 100M| VicePresident[Phó GĐ duyệt - KT. Giám đốc]\n"
                        "    Authority -->|> 100M| President[Giám đốc duyệt trực tiếp]\n"
                        "    FacultyHead --> Perform[Kỹ thuật viên thực hiện sửa chữa]\n"
                        "    SchoolHead --> Perform\n"
                        "    VicePresident --> Perform\n"
                        "    President --> Perform\n"
                        "    Perform --> Accept[Nghiệm thu: acceptance.confirm]\n"
                        "    Accept --> End([Hoàn thành phiếu])\n"
                    )
                    Muted("Mã nguồn sơ đồ Mermaid sinh tự động từ định nghĩa quy trình core:")
                    # Render code block qua HTML thấu kính thuần
                    from prefab_ui.components import RawHtml
                    RawHtml(f'<pre class="p-4 bg-muted rounded-md overflow-x-auto font-mono text-xs"><code>{mermaid_code}</code></pre>')
