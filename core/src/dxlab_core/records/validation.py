# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

"""Kiểm dữ liệu bằng JSON Schema Draft 2020-12 và đổi lỗi sang `{"path", "message"}` tiếng Việt."""

import re
from collections.abc import Iterable
from typing import Any

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError, ValidationError

_TYPE_NAMES = {
    "string": "chuỗi",
    "integer": "số nguyên",
    "number": "số",
    "boolean": "đúng/sai",
    "array": "danh sách",
    "object": "đối tượng",
    "null": "null",
}


def _join(values: Iterable[Any]) -> str:
    return ", ".join(str(value) for value in values)


def _path(prefix: str, parts: Iterable[Any]) -> str:
    return ".".join([prefix, *(str(part) for part in parts)]) if prefix else ".".join(str(part) for part in parts)


def _messages(error: ValidationError) -> list[tuple[Iterable[Any], str]]:
    """Một lỗi jsonschema có thể thành nhiều lỗi (thiếu nhiều trường, thừa nhiều trường)."""
    path = list(error.absolute_path)
    expected = error.validator_value
    match error.validator:
        case "required":
            present = error.instance if isinstance(error.instance, dict) else {}
            return [([*path, name], "Thiếu trường bắt buộc.") for name in expected if name not in present]
        case "additionalProperties" | "unevaluatedProperties":
            schema = error.schema if isinstance(error.schema, dict) else {}
            declared = set(schema.get("properties", {}))
            patterns = list(schema.get("patternProperties", {}))
            extra = [
                name
                for name in error.instance
                if name not in declared and not any(re.search(pattern, name) for pattern in patterns)
            ]
            return [([*path, name], "Trường không được phép.") for name in extra]
        case "type":
            names = expected if isinstance(expected, list) else [expected]
            return [(path, f"Phải là {' hoặc '.join(_TYPE_NAMES.get(name, str(name)) for name in names)}.")]
        case "enum":
            return [(path, f"Giá trị không nằm trong danh sách cho phép: {_join(expected)}.")]
        case "const":
            return [(path, f"Giá trị phải là {expected}.")]
        case "minimum":
            return [(path, f"Giá trị phải từ {expected} trở lên.")]
        case "maximum":
            return [(path, f"Giá trị phải từ {expected} trở xuống.")]
        case "exclusiveMinimum":
            return [(path, f"Giá trị phải lớn hơn {expected}.")]
        case "exclusiveMaximum":
            return [(path, f"Giá trị phải nhỏ hơn {expected}.")]
        case "multipleOf":
            return [(path, f"Giá trị phải là bội của {expected}.")]
        case "minLength":
            return [(path, "Không được để trống." if expected == 1 else f"Chuỗi phải dài ít nhất {expected} ký tự.")]
        case "maxLength":
            return [(path, f"Chuỗi dài tối đa {expected} ký tự.")]
        case "pattern":
            return [(path, "Không đúng định dạng yêu cầu.")]
        case "format":
            return [(path, f"Không đúng định dạng {expected}.")]
        case "minItems":
            return [(path, f"Danh sách phải có ít nhất {expected} phần tử.")]
        case "maxItems":
            return [(path, f"Danh sách có tối đa {expected} phần tử.")]
        case "uniqueItems":
            return [(path, "Các phần tử không được trùng nhau.")]
        case "minProperties":
            return [(path, f"Đối tượng phải có ít nhất {expected} trường.")]
        case "maxProperties":
            return [(path, f"Đối tượng có tối đa {expected} trường.")]
        case "anyOf" | "oneOf":
            return [(path, "Không khớp với bất kỳ dạng nào được phép.")]
        case "not":
            return [(path, "Giá trị không được phép.")]
        case _:
            return [(path, f"Không hợp lệ ({error.validator}).")]


def schema_errors(schema: dict[str, Any]) -> list[dict[str, str]]:
    """Lỗi của chính schema (không phải Draft 2020-12 hợp lệ); rỗng nếu hợp lệ."""
    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as exc:
        return [{"path": _path("schema", exc.absolute_path), "message": f"Schema không hợp lệ: {exc.message}"}]
    return []


def data_errors(schema: dict[str, Any], data: Any) -> list[dict[str, str]]:
    """Lỗi của `data` so với `schema`; `path` bắt đầu bằng `data` (thân yêu cầu là `{"data": …}`)."""
    validator = Draft202012Validator(schema, format_checker=Draft202012Validator.FORMAT_CHECKER)
    # jsonschema báo mỗi trường thiếu thành một lỗi riêng, mà `_messages` đã liệt kê hết các trường thiếu: bỏ trùng.
    pairs = {
        (_path("data", parts), message) for error in validator.iter_errors(data) for parts, message in _messages(error)
    }
    return [{"path": path, "message": message} for path, message in sorted(pairs)]
