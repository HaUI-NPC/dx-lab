# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

"""Kiểm tra dữ liệu form theo JSON Schema, báo lỗi tiếng Việt theo từng trường.

Portal kiểm trước để người dùng sửa ngay; core vẫn kiểm lại và quyết định (ARCHITECTURE §3, luật 4).
Giá trị từ trình duyệt thường là chuỗi, nên số và ngày được chuyển kiểu trước khi so ràng buộc.
"""

from __future__ import annotations

import datetime
import json
import re
from typing import Any

from dxlab_portal.pages.forms.spec import FormField, FormSpec

_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_INTEGER = re.compile(r"^[+-]?\d+$")
_NUMBER = re.compile(r"^[+-]?\d+(?:[.,]\d+)?$")


def _lower_first(text: str) -> str:
    """Hạ chữ đầu để chèn giữa câu, trừ khi là viết tắt (ví dụ "SĐT", "ID")."""
    if len(text) > 1 and text[1].isupper():
        return text
    return text[:1].lower() + text[1:]


def _number(value: float | int) -> str:
    """Số kiểu Việt Nam: dấu chấm ngăn cách hàng nghìn."""
    if isinstance(value, float) and not value.is_integer():
        return str(value).replace(".", ",")
    return f"{int(value):,}".replace(",", ".")


def _coerce(form_field: FormField, raw: Any) -> tuple[Any, str | None]:
    """Chuyển giá trị thô về kiểu của schema. Trả ``(giá trị, lỗi)``; giá trị ``None`` nghĩa là để trống."""
    title = form_field.title
    if form_field.kind == "checkbox":
        if isinstance(raw, bool):
            return raw, None
        return (str(raw).lower() == "true"), None
    if raw is None or (isinstance(raw, str) and not raw.strip()):
        return None, None
    if form_field.kind == "array":
        try:
            value = json.loads(raw) if isinstance(raw, str) else raw
        except (ValueError, TypeError):
            return None, f"{title} phải là danh sách JSON hợp lệ."
        if not isinstance(value, list):
            return None, f"{title} phải là danh sách."
        return value, None
    text = str(raw).strip()
    if form_field.kind == "integer":
        if not _INTEGER.match(text):
            return None, f"{title} phải là số nguyên."
        return int(text), None
    if form_field.kind == "number":
        if not _NUMBER.match(text):
            return None, f"{title} phải là một số."
        return float(text.replace(",", ".")), None
    if form_field.schema.get("type") in ("integer", "number") and form_field.kind in ("select", "radio"):
        try:
            return (int(text) if form_field.schema["type"] == "integer" else float(text)), None
        except ValueError:
            return None, f"Giá trị của {_lower_first(title)} không nằm trong danh sách lựa chọn."
    return text, None


def _missing_message(form_field: FormField) -> str:
    name = _lower_first(form_field.title)
    if form_field.kind in ("select", "radio"):
        return f"Vui lòng chọn {name}."
    return f"Vui lòng nhập {name}."


def _check(form_field: FormField, value: Any) -> str | None:
    """Kiểm ràng buộc của schema cho một giá trị đã chuyển kiểu; trả thông báo lỗi đầu tiên."""
    schema = form_field.schema
    title = form_field.title
    if form_field.kind == "array":
        if len(value) < schema.get("minItems", 0):
            return f"{title} chưa có đủ mục."
        if "maxItems" in schema and len(value) > schema["maxItems"]:
            return f"{title} có quá nhiều mục."
        return None
    if form_field.kind in ("select", "radio"):
        allowed = {o.value for o in form_field.options}
        if str(value) not in allowed:
            return f"Giá trị của {_lower_first(title)} không nằm trong danh sách lựa chọn."
        return None
    if isinstance(value, str):
        length = len(value)
        min_length = schema.get("minLength")
        if isinstance(min_length, int) and length < min_length:
            return f"{title} cần có ít nhất {min_length} ký tự (hiện có {length})."
        max_length = schema.get("maxLength")
        if isinstance(max_length, int) and length > max_length:
            return f"{title} chỉ được tối đa {max_length} ký tự (hiện có {length})."
        pattern = schema.get("pattern")
        if isinstance(pattern, str) and not re.search(pattern, value):
            return f"{title} chưa đúng định dạng."
        if form_field.kind == "email" and not _EMAIL.match(value):
            return f"{title} chưa hợp lệ, cần có dạng ten@ten-mien."
        if form_field.kind == "date":
            try:
                datetime.date.fromisoformat(value)
            except ValueError:
                return f"{title} chưa phải ngày hợp lệ."
    else:
        minimum = schema.get("minimum")
        if isinstance(minimum, int | float) and value < minimum:
            return f"{title} phải từ {_number(minimum)} trở lên."
        maximum = schema.get("maximum")
        if isinstance(maximum, int | float) and value > maximum:
            return f"{title} không được vượt quá {_number(maximum)}."
        exclusive_min = schema.get("exclusiveMinimum")
        if isinstance(exclusive_min, int | float) and value <= exclusive_min:
            return f"{title} phải lớn hơn {_number(exclusive_min)}."
        exclusive_max = schema.get("exclusiveMaximum")
        if isinstance(exclusive_max, int | float) and value >= exclusive_max:
            return f"{title} phải nhỏ hơn {_number(exclusive_max)}."
    return None


def validate_form(spec: FormSpec, raw: dict[str, Any]) -> tuple[dict[str, Any], dict[str, str]]:
    """Kiểm ``raw`` theo ``spec``. Trả ``(data, errors)``: ``data`` đã chuyển kiểu và gộp giá trị ẩn mặc định,
    ``errors`` là ``{tên trường: thông báo}`` chỉ gồm trường lỗi."""
    data: dict[str, Any] = dict(spec.hidden_defaults)
    errors: dict[str, str] = {}
    for form_field in spec.fields:
        value, error = _coerce(form_field, raw.get(form_field.name))
        if error is None:
            if form_field.kind == "checkbox":
                # Theo JSON Schema, ô đánh dấu chỉ bị ép tick khi có ``const`` (ví dụ ô đồng thuận).
                if "const" in form_field.schema and value != form_field.schema["const"]:
                    if form_field.required:
                        error = f"Bạn cần đánh dấu ô “{form_field.title}” để tiếp tục."
                    else:
                        value = None
            elif value is None:
                if form_field.required:
                    error = _missing_message(form_field)
            else:
                error = _check(form_field, value)
        if error is not None:
            errors[form_field.name] = error
        elif value is not None:
            data[form_field.name] = value
    return data, errors
