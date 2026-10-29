# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

"""Dựng mô hình form từ JSON Schema và uischema.

Schema và uischema do ứng dụng (Tầng 3) định nghĩa, core phục vụ qua ``/api/definitions/{app_id}/start-form``
hoặc ``/api/tasks/{task_id}``. Mô-đun này chỉ đọc chúng: không biết ứng dụng cụ thể nào.

Phần JSON Schema được hỗ trợ: ``string`` (kèm ``enum``/``oneOf``, ``format`` email và date, ``minLength``,
``maxLength``, ``pattern``), ``integer``, ``number`` (``minimum``, ``maximum``), ``boolean`` (kèm ``const``),
``required``, ``title``, ``description``, ``default``. Phần uischema được hỗ trợ (kiểu JSON Forms):
``VerticalLayout``, ``HorizontalLayout``, ``Group``, ``Control`` với ``scope``, ``label``, ``options.multi``,
``options.rows``, ``options.format`` (``radio``). Kiểu khác (mảng, đối tượng lồng) hiện thông báo, không gửi.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

Kind = Literal["text", "textarea", "email", "date", "number", "integer", "select", "radio", "checkbox"]

SCOPE_PREFIX = "#/properties/"
DEFAULT_TEXTAREA_ROWS = 4


@dataclass(frozen=True)
class Option:
    value: str
    label: str


@dataclass(frozen=True)
class FormField:
    """Một trường nhập liệu đã được xác định kiểu điều khiển."""

    name: str
    kind: Kind
    # Nhãn hiển thị: ``label`` của uischema, không có thì ``title`` của schema.
    label: str
    # Tên trường dùng trong thông báo lỗi: ``title`` của schema, không có thì nhãn hiển thị.
    title: str
    description: str | None
    required: bool
    schema: dict[str, Any]
    options: list[Option] = field(default_factory=list)
    rows: int | None = None
    # Giá trị ban đầu: chuỗi cho ô nhập, bool cho ô đánh dấu, ``Option.value`` cho lựa chọn.
    initial: Any = ""


@dataclass(frozen=True)
class Unsupported:
    """Trường có kiểu chưa nhập được trên portal: hiện thông báo, không gửi."""

    name: str
    label: str
    description: str | None
    required: bool


@dataclass(frozen=True)
class Layout:
    """Nút bố cục: ``vertical`` xếp dọc, ``horizontal`` xếp ngang, ``group`` là khối có tiêu đề."""

    type: Literal["vertical", "horizontal", "group"]
    children: list[Node]
    label: str | None = None


Node = FormField | Unsupported | Layout


@dataclass(frozen=True)
class FormSpec:
    title: str | None
    description: str | None
    root: Layout
    # Trường không hiện trên form nhưng schema cho giá trị mặc định; luôn được gửi kèm.
    hidden_defaults: dict[str, Any]
    # Mọi trường nhập được, theo thứ tự hiển thị.
    fields: list[FormField]


def _enum_options(prop: dict[str, Any]) -> list[Option]:
    """Nhãn của lựa chọn: ``oneOf`` [{const, title}], rồi ``enumNames``, không có thì chính giá trị."""
    one_of = prop.get("oneOf")
    if isinstance(one_of, list) and one_of and all(isinstance(o, dict) and "const" in o for o in one_of):
        return [Option(str(o["const"]), str(o.get("title", o["const"]))) for o in one_of]
    values = prop.get("enum") or []
    names = prop.get("enumNames")
    if isinstance(names, list) and len(names) == len(values):
        return [Option(str(v), str(n)) for v, n in zip(values, names, strict=True)]
    return [Option(str(v), str(v)) for v in values]


def _kind(prop: dict[str, Any], ui_options: dict[str, Any]) -> Kind | None:
    type_ = prop.get("type")
    if type_ not in ("string", "integer", "number", "boolean"):
        return None
    if type_ == "boolean":
        return "checkbox"
    if prop.get("enum") or prop.get("oneOf"):
        return "radio" if ui_options.get("format") == "radio" else "select"
    if type_ in ("integer", "number"):
        return type_  # type: ignore[return-value]
    if ui_options.get("multi") or ui_options.get("format") == "textarea":
        return "textarea"
    return {"email": "email", "date": "date"}.get(prop.get("format", ""), "text")  # type: ignore[return-value]


def _initial(kind: Kind, prop: dict[str, Any]) -> Any:
    default = prop.get("default")
    if kind == "checkbox":
        # Ô đồng thuận không bao giờ tick sẵn (AUTHZ §8): chỉ tick sẵn khi schema đặt mặc định true
        # cho ô không bị ép ``const``.
        return default is True and "const" not in prop
    return "" if default is None else str(default)


class _Builder:
    def __init__(self, schema: dict[str, Any]) -> None:
        props = schema.get("properties")
        self.props: dict[str, Any] = props if isinstance(props, dict) else {}
        required = schema.get("required")
        self.required: set[str] = set(required) if isinstance(required, list) else set()
        self.used: set[str] = set()
        self.fields: list[FormField] = []

    def control(self, name: str, ui: dict[str, Any] | None = None) -> Node | None:
        prop = self.props.get(name)
        if not isinstance(prop, dict) or name in self.used:
            return None
        self.used.add(name)
        ui = ui or {}
        options = ui.get("options") if isinstance(ui.get("options"), dict) else {}
        title = str(prop.get("title") or name)
        label = str(ui.get("label") or title)
        description = prop.get("description")
        description = str(description) if description else None
        kind = _kind(prop, options)
        if kind is None:
            return Unsupported(name, label, description, name in self.required)
        rows = options.get("rows") if isinstance(options.get("rows"), int) else None
        form_field = FormField(
            name=name,
            kind=kind,
            label=label,
            title=title,
            description=description,
            required=name in self.required,
            schema=prop,
            options=_enum_options(prop) if kind in ("select", "radio") else [],
            rows=(rows or DEFAULT_TEXTAREA_ROWS) if kind == "textarea" else None,
            initial=_initial(kind, prop),
        )
        self.fields.append(form_field)
        return form_field

    def element(self, ui: Any) -> Node | None:
        if not isinstance(ui, dict):
            return None
        type_ = ui.get("type")
        if type_ == "Control":
            scope = str(ui.get("scope", ""))
            if not scope.startswith(SCOPE_PREFIX):
                return None
            return self.control(scope.removeprefix(SCOPE_PREFIX), ui)
        layout = {"VerticalLayout": "vertical", "HorizontalLayout": "horizontal", "Group": "group"}.get(
            str(type_)
        )
        if layout is None:
            return None
        children = [n for n in (self.element(e) for e in ui.get("elements", [])) if n is not None]
        label = str(ui["label"]) if layout == "group" and ui.get("label") else None
        return Layout(layout, children, label)  # type: ignore[arg-type]


def build_form(schema: dict[str, Any], uischema: dict[str, Any] | None) -> FormSpec:
    """Dựng ``FormSpec`` từ schema và uischema (uischema trống thì xếp dọc theo thứ tự trong schema)."""
    builder = _Builder(schema)
    root: Layout | None = None
    if uischema:
        node = builder.element(uischema)
        root = node if isinstance(node, Layout) else Layout("vertical", [node] if node else [])
    if root is None:
        root = Layout("vertical", [])
    hidden: dict[str, Any] = {}
    leftovers: list[Node] = []
    for name, prop in builder.props.items():
        if name in builder.used or not isinstance(prop, dict):
            continue
        if name in builder.required or not uischema:
            # Trường bắt buộc mà uischema không nhắc tới vẫn phải nhập được; không uischema thì hiện hết.
            node = builder.control(name)
            if node is not None:
                leftovers.append(node)
        elif "default" in prop:
            hidden[name] = prop["default"]
    if leftovers:
        root = Layout(root.type, [*root.children, *leftovers], root.label)
    description = schema.get("description")
    return FormSpec(
        title=str(schema["title"]) if schema.get("title") else None,
        description=str(description) if description else None,
        root=root,
        hidden_defaults=hidden,
        fields=builder.fields,
    )
