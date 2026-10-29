# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

"""Sinh component Prefab từ ``FormSpec``.

Trạng thái phía trình duyệt: ``f_<tên trường>`` giữ giá trị đang nhập, ``errors`` là
``{tên trường: thông báo}`` do portal trả về sau khi kiểm tra, ``outcome`` là kết quả lần gửi gần nhất,
``submitting`` chặn bấm đúp.
Việc kiểm tra nằm ở máy chủ portal (``routes.py``), nên thông báo lỗi chỉ có một nguồn.
"""

from __future__ import annotations

import re
from typing import Any

from prefab_ui.actions import Fetch, SetState, ShowToast
from prefab_ui.components import (
    Alert,
    AlertDescription,
    AlertTitle,
    Button,
    Card,
    CardContent,
    CardHeader,
    CardTitle,
    Checkbox,
    Column,
    Field,
    FieldError,
    Grid,
    Input,
    Label,
    Link,
    Muted,
    Radio,
    RadioGroup,
    Row,
    Select,
    SelectOption,
    Textarea,
)
from prefab_ui.components.control_flow import If
from prefab_ui.rx import RESULT, Rx

from dxlab_portal.pages.forms.spec import FormField, FormSpec, Layout, Node, Unsupported

_NON_IDENT = re.compile(r"\W")
EMPTY_OUTCOME: dict[str, Any] = {"ok": False, "message": "", "error": None, "workflow": None}


def state_key(name: str) -> str:
    """Khóa trạng thái Prefab của một trường (chỉ gồm chữ, số, gạch dưới)."""
    return "f_" + _NON_IDENT.sub("_", name)


def initial_state(spec: FormSpec) -> dict[str, Any]:
    """Trạng thái ban đầu của form: giá trị mặc định, chưa có lỗi, chưa gửi."""
    state: dict[str, Any] = {state_key(f.name): f.initial for f in spec.fields}
    state["errors"] = {f.name: "" for f in spec.fields}
    state["outcome"] = EMPTY_OUTCOME
    state["submitting"] = False
    return state


def _label(text: str, required: bool) -> None:
    Label(f"{text} *" if required else text)


def _control(f: FormField) -> None:
    key = state_key(f.name)
    if f.kind == "textarea":
        Textarea(name=key, value=f.initial, rows=f.rows)
    elif f.kind == "select":
        with Select(name=key, value=f.initial or None, placeholder="Chọn…"):
            for option in f.options:
                SelectOption(value=option.value, label=option.label)
    elif f.kind == "radio":
        with RadioGroup(name=key, value=f.initial or None):
            for option in f.options:
                Radio(option=option.value, label=option.label)
    elif f.kind == "checkbox":
        # Mô tả của trường là câu xác nhận người dùng đọc rồi đánh dấu.
        Checkbox(name=key, value=bool(f.initial), label=f.description or f.label)
    elif f.kind in ("integer", "number"):
        step = 1 if f.kind == "integer" else None
        Input(
            name=key,
            value=f.initial,
            input_type="number",
            step=step,
            min=f.schema.get("minimum"),
            max=f.schema.get("maximum"),
        )
    else:
        Input(name=key, value=f.initial, input_type=f.kind if f.kind in ("email", "date") else "text")


def _field(f: FormField) -> None:
    # `errors.<tên>` khác rỗng thì trường chuyển sang trạng thái lỗi và hiện thông báo ngay dưới ô nhập.
    with Field(invalid=Rx(f"!!errors.{f.name}")):
        with Column(gap=2):
            _label(f.label, f.required)
            if f.description and f.kind != "checkbox":
                Muted(f.description)
            _control(f)
            with If(f"errors.{f.name}"):
                FieldError(f"{{{{ errors.{f.name} }}}}")


def _unsupported(node: Unsupported) -> None:
    with Column(gap=2):
        _label(node.label, node.required)
        if node.description:
            Muted(node.description)
        Muted("Trường này chưa nhập được trên portal; hãy dùng API hoặc CLI.")


def _node(node: Node) -> None:
    if isinstance(node, FormField):
        _field(node)
    elif isinstance(node, Unsupported):
        _unsupported(node)
    else:
        _layout(node)


def _layout(layout: Layout) -> None:
    if layout.type == "horizontal" and layout.children:
        with Grid(columns={"default": 1, "md": len(layout.children)}, gap=4):
            for child in layout.children:
                with Column(gap=4):
                    _node(child)
    elif layout.type == "group":
        with Card():
            if layout.label:
                with CardHeader():
                    CardTitle(layout.label)
            with CardContent():
                with Column(gap=4):
                    for child in layout.children:
                        _node(child)
    else:
        with Column(gap=4):
            for child in layout.children:
                _node(child)


def _outcome_alerts(success_title: str) -> None:
    with If("outcome.error"):
        with Alert(variant="destructive"):
            AlertTitle("Không gửi được")
            AlertDescription("{{ outcome.error.message }}")
            Muted("Mã lỗi: {{ outcome.error.code }} · Mã yêu cầu: {{ outcome.error.request_id }}")
    with If("outcome.message"):
        with Alert(variant="warning"):
            AlertTitle("Cần sửa lại")
            AlertDescription("{{ outcome.message }}")
    with If("outcome.ok"):
        with Alert(variant="success"):
            AlertTitle(success_title)
            AlertDescription(
                "Mã phiếu: {{ outcome.workflow.workflow_id }}"
                " · Trạng thái: {{ outcome.workflow.status_name }}"
            )


def render_form(
    spec: FormSpec,
    *,
    submit_url: str,
    submit_label: str,
    success_title: str,
    again_label: str,
    again_href: str,
) -> None:
    """Dựng form trong ngữ cảnh Prefab hiện tại. ``submit_url`` nhận ``{"values": {...}}`` và trả về
    phong bì ``{"ok", "errors", "message", "error", "workflow"}`` (xem ``routes.py``)."""
    submit = Fetch.post(
        submit_url,
        body={"values": {f.name: "{{ " + state_key(f.name) + " }}" for f in spec.fields}},
        on_success=[
            SetState("submitting", False),
            SetState("errors", RESULT.errors),
            SetState("outcome", RESULT),
        ],
        on_error=[
            SetState("submitting", False),
            ShowToast(
                "Không gửi được: {{ $error }}. Nếu phiên đăng nhập đã hết hạn, hãy tải lại trang.",
                variant="error",
            ),
        ],
    )
    with Column(gap=4):
        if spec.title:
            Label(spec.title)
        if spec.description:
            Muted(spec.description)
        _layout(spec.root)
        Muted("Các trường có dấu * là bắt buộc.")
        _outcome_alerts(success_title)
        with Row(gap=3, align="center"):
            Button(
                submit_label,
                disabled=Rx("submitting || outcome.ok"),
                on_click=[SetState("submitting", True), SetState("outcome", EMPTY_OUTCOME), submit],
            )
            with If("outcome.ok"):
                Link(again_label, href=again_href, css_class="text-sm underline underline-offset-4")
