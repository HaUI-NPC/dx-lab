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


class Keys:
    """Khóa trạng thái Prefab của một form. ``ns`` tách các form cùng nằm trên một trang
    (ví dụ form báo hỏng và form hoàn thành bước) để chúng không ghi đè trạng thái của nhau."""

    def __init__(self, ns: str) -> None:
        self.ns = ns
        self.errors = f"{ns}_errors"
        self.outcome = f"{ns}_outcome"
        self.submitting = f"{ns}_submitting"

    def field(self, name: str) -> str:
        """Khóa của một trường (chỉ gồm chữ, số, gạch dưới)."""
        return f"{self.ns}_f_" + _NON_IDENT.sub("_", name)


def initial_state(spec: FormSpec, ns: str) -> dict[str, Any]:
    """Trạng thái ban đầu của form: giá trị mặc định, chưa có lỗi, chưa gửi."""
    keys = Keys(ns)
    state: dict[str, Any] = {keys.field(f.name): f.initial for f in spec.fields}
    state[keys.errors] = {f.name: "" for f in spec.fields}
    state[keys.outcome] = EMPTY_OUTCOME
    state[keys.submitting] = False
    return state


def _label(text: str, required: bool) -> None:
    Label(f"{text} *" if required else text)


def _control(f: FormField, keys: Keys) -> None:
    key = keys.field(f.name)
    if f.kind == "array":
        Muted("Nhập danh sách JSON; ví dụ: [{\"supplier_name\":\"Nhà cung cấp\", \"quote_amount_vnd\":1000000, \"quote_reference\":\"BG-01\"}].")
        Textarea(name=key, value=f.initial, rows=5)
        return
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


def _field(f: FormField, keys: Keys) -> None:
    # `errors.<tên>` khác rỗng thì trường chuyển sang trạng thái lỗi và hiện thông báo ngay dưới ô nhập.
    with Field(invalid=Rx(f"!!{keys.errors}.{f.name}")):
        with Column(gap=2):
            _label(f.label, f.required)
            if f.description and f.kind != "checkbox":
                Muted(f.description)
            _control(f, keys)
            with If(f"{keys.errors}.{f.name}"):
                FieldError(f"{{{{ {keys.errors}.{f.name} }}}}")


def _unsupported(node: Unsupported) -> None:
    with Column(gap=2):
        _label(node.label, node.required)
        if node.description:
            Muted(node.description)
        Muted("Trường này chưa nhập được trên portal; hãy dùng API hoặc CLI.")


def _node(node: Node, keys: Keys) -> None:
    if isinstance(node, FormField):
        _field(node, keys)
    elif isinstance(node, Unsupported):
        _unsupported(node)
    else:
        _layout(node, keys)


def _layout(layout: Layout, keys: Keys) -> None:
    if layout.type == "horizontal" and layout.children:
        with Grid(columns={"default": 1, "md": len(layout.children)}, gap=4):
            for child in layout.children:
                with Column(gap=4):
                    _node(child, keys)
    elif layout.type == "group":
        with Card():
            if layout.label:
                with CardHeader():
                    CardTitle(layout.label)
            with CardContent():
                with Column(gap=4):
                    for child in layout.children:
                        _node(child, keys)
    else:
        with Column(gap=4):
            for child in layout.children:
                _node(child, keys)


def _outcome_alerts(success_title: str, keys: Keys) -> None:
    o = keys.outcome
    with If(f"{o}.error"):
        with Alert(variant="destructive"):
            AlertTitle("Không gửi được")
            AlertDescription(f"{{{{ {o}.error.message }}}}")
            Muted(f"Mã lỗi: {{{{ {o}.error.code }}}} · Mã yêu cầu: {{{{ {o}.error.request_id }}}}")
    with If(f"{o}.message"):
        with Alert(variant="warning"):
            AlertTitle("Cần sửa lại")
            AlertDescription(f"{{{{ {o}.message }}}}")
    with If(f"{o}.ok"):
        with Alert(variant="success"):
            AlertTitle(success_title)
            AlertDescription(
                f"Mã phiếu: {{{{ {o}.workflow.workflow_id }}}} · Trạng thái: {{{{ {o}.workflow.status_name }}}}"
            )


def render_form(
    spec: FormSpec,
    *,
    ns: str,
    submit_url: str,
    submit_label: str,
    success_title: str,
    again_label: str,
    again_href: str,
) -> None:
    """Dựng form trong ngữ cảnh Prefab hiện tại. ``ns`` là tiền tố trạng thái (xem ``Keys``);
    ``submit_url`` nhận ``{"values": {...}}`` và trả về phong bì
    ``{"ok", "errors", "message", "error", "workflow"}`` (xem ``routes.py``)."""
    keys = Keys(ns)
    submit = Fetch.post(
        submit_url,
        body={"values": {f.name: "{{ " + keys.field(f.name) + " }}" for f in spec.fields}},
        on_success=[
            SetState(keys.submitting, False),
            SetState(keys.errors, RESULT.errors),
            SetState(keys.outcome, RESULT),
        ],
        on_error=[
            SetState(keys.submitting, False),
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
        _layout(spec.root, keys)
        Muted("Các trường có dấu * là bắt buộc.")
        _outcome_alerts(success_title, keys)
        with Row(gap=3, align="center"):
            Button(
                submit_label,
                disabled=Rx(f"{keys.submitting} || {keys.outcome}.ok"),
                on_click=[SetState(keys.submitting, True), SetState(keys.outcome, EMPTY_OUTCOME), submit],
            )
            with If(f"{keys.outcome}.ok"):
                Link(again_label, href=again_href, css_class="text-sm underline underline-offset-4")
