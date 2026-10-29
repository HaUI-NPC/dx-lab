# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

"""Hộp việc và chi tiết phiếu do core cho phép người dùng xem."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any
from urllib.parse import quote
from zoneinfo import ZoneInfo

from prefab_ui.components import Badge, Card, CardContent, CardHeader, CardTitle, Column, Link, Muted, Text

from dxlab_portal.pages.context import PageContext
from dxlab_portal.pages.core_error import render_core_error
from dxlab_portal.pages.forms.render import initial_state, render_form
from dxlab_portal.pages.forms.spec import build_form


def _date(value: Any) -> str:
    if not value:
        return "—"
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).astimezone(ZoneInfo("Asia/Ho_Chi_Minh")).strftime("%d/%m/%Y %H:%M")
    except ValueError:
        return str(value)


async def load(ctx: PageContext) -> dict[str, Any]:
    tasks = await ctx.core.call("GET", "/tasks", token=ctx.access_token)
    task = None
    workflow = None
    workflow_id = ctx.workflow_id
    if ctx.task_id:
        task = await ctx.core.call("GET", f"/tasks/{quote(ctx.task_id, safe='')}", token=ctx.access_token)
        if task.ok and isinstance(task.json, dict):
            workflow_id = str(task.json.get("workflow_id") or "")
    if workflow_id:
        workflow = await ctx.core.call("GET", f"/workflows/{quote(workflow_id, safe='')}", token=ctx.access_token)
    return {"tasks": tasks, "task": task, "workflow": workflow, "task_id": ctx.task_id}


def _spec(data: dict[str, Any]):
    task = data["task"]
    if task is None or not task.ok or not isinstance(task.json, dict):
        return None
    form = task.json.get("form") or {}
    return build_form(form.get("schema") or {}, form.get("uischema"))


def state(data: dict[str, Any]) -> dict[str, Any]:
    spec = _spec(data)
    return initial_state(spec, "task") if spec else {}


def _value(value: Any) -> str:
    if isinstance(value, bool):
        return "Có" if value else "Không"
    if isinstance(value, (dict, list)):
        value = json.dumps(value, ensure_ascii=False)
    text = str(value) if value is not None else "—"
    return text + (" (giả định)" if "GĐ-" in text and "giả định" not in text.lower() else "")


def _field_text(key: str, value: Any) -> str:
    """Một giá trị của phiếu thành chữ người đọc: tiền có dấu chấm, Có/Không, danh sách mỗi mục một đoạn."""
    if isinstance(value, bool) or value is None:
        return _value(value)
    if isinstance(value, int) and key.endswith("_vnd"):
        return f"{value:,}".replace(",", ".") + " đ"
    if isinstance(value, list):
        return "; ".join(_field_text(key, item) for item in value) or "—"
    if isinstance(value, dict):
        return " · ".join(_field_text(k, v) for k, v in value.items())
    return _value(value)


def describe_fields(data: dict[str, Any], titles: dict[str, str]) -> list[tuple[str, str]]:
    """Chỉ các trường có tiêu đề trong form của gói; trường không có tiêu đề là dữ liệu nội bộ của engine."""
    return [(title, _field_text(key, data[key])) for key, title in titles.items() if key in data]


_ACTIONS = {"report.create": "Tạo phiếu", "task.complete": "Hoàn thành bước", "repair.approve": "Duyệt"}
_SIGNING = {"direct": "trực tiếp", "kt": "KT.", "tuq": "TUQ."}


def describe_history(events: list[Any]) -> list[str]:
    """Mỗi sự kiện một dòng: thời điểm · người làm · việc đã làm (kèm hình thức ký và căn cứ nếu có)."""
    lines = []
    for event in events:
        if not isinstance(event, dict):
            continue
        details = event.get("details") or {}
        action = _ACTIONS.get(str(event.get("action")), str(event.get("action") or "—"))
        step = details.get("step_name") or event.get("step_id")
        parts = [_date(event.get("at")), str(event.get("actor") or "—"), f"{action}: {step}" if step else action]
        if details.get("signing_type"):
            parts.append(f"ký {_SIGNING.get(str(details['signing_type']), details['signing_type'])}")
        if details.get("authority_basis"):
            parts.append(f"căn cứ {_value(details['authority_basis'])}")
        lines.append(" · ".join(parts))
    return lines


def render(data: dict[str, Any]) -> None:
    with Column(gap=4):
        with Card():
            with CardHeader():
                CardTitle("Việc của tôi")
            with CardContent():
                result = data["tasks"]
                if not result.ok:
                    render_core_error("Không tải được hộp việc", result)
                else:
                    items = result.json.get("items", []) if isinstance(result.json, dict) else []
                    if not items:
                        Muted("Không có việc đang chờ bạn xử lý.")
                    for item in items:
                        with Column(gap=1):
                            Link(
                                str(item.get("step_name") or item.get("step_id") or "Chi tiết việc"),
                                href=f"/?tab=tasks&task_id={quote(str(item.get('task_id', '')), safe='')}",
                                target="_self",
                            )
                            Muted(
                                f"Phiếu {str(item.get('workflow_id', '—'))[:8]} · {item.get('app_id', '—')} · "
                                f"Hạn: {_date(item.get('due_at'))}"
                            )
                            if item.get("overdue"):
                                Badge("Quá hạn", variant="destructive")
        task = data["task"]
        if task is not None:
            if not task.ok:
                render_core_error("Không tải được việc", task)
            else:
                spec = _spec(data)
                if spec:
                    with Card():
                        with CardHeader():
                            CardTitle(str(task.json.get("step_name") or "Xử lý việc"))
                        with CardContent():
                            render_form(
                                spec, ns="task",
                                submit_url=f"/ui/forms/task/{quote(data['task_id'], safe='')}",
                                submit_label="Hoàn thành", success_title="Đã hoàn thành việc",
                                again_label="Về hộp việc", again_href="/?tab=tasks",
                            )
        workflow = data["workflow"]
        if workflow is not None:
            if not workflow.ok:
                render_core_error("Không tải được phiếu", workflow)
            elif isinstance(workflow.json, dict):
                item = workflow.json
                with Card():
                    with CardHeader():
                        CardTitle("Chi tiết phiếu")
                    with CardContent():
                        Text(
                            f"Trạng thái: {item.get('status_name') or item.get('status', '—')} · "
                            f"Mã phiếu: {str(item.get('workflow_id', '—'))[:8]} · Hạn: {_date(item.get('due_at'))}"
                        )
                        with Column(gap=1):
                            for title, text in describe_fields(item.get("data") or {}, item.get("field_titles") or {}):
                                Text(f"{title}: {text}")
                        Text("Lịch sử", bold=True)
                        with Column(gap=1):
                            for line in describe_history(item.get("history") or []):
                                Text(line)
