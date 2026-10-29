# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

"""Che dữ liệu cá nhân dựa trên các schema của phiên bản định nghĩa đã ghim."""

import json
from typing import Any

from dxlab_core.definitions.service import files_of
from dxlab_core.audit.service import record
from dxlab_core.errors import ApiError

_REDACTED = object()


def _mask(value: Any, schema: dict, root: dict) -> Any:
    if not isinstance(schema, dict):
        return value
    if schema.get("x-personal-data") is True:
        return _REDACTED
    ref = schema.get("$ref")
    if isinstance(ref, str) and ref.startswith("#/"):
        target = root
        for part in ref[2:].split("/"):
            if not isinstance(target, dict):
                break
            target = target.get(part.replace("~1", "/").replace("~0", "~"), {})
        value = _mask(value, target, root)
    for keyword in ("allOf", "anyOf", "oneOf"):
        for branch in schema.get(keyword, []):
            value = _mask(value, branch, root)
    if isinstance(value, dict):
        properties = schema.get("properties", {})
        result = {}
        for key, item in value.items():
            child = properties.get(key, {})
            masked = _mask(item, child, root)
            if masked is not _REDACTED:
                result[key] = masked
        return result
    if isinstance(value, list):
        items = (_mask(item, schema.get("items", {}), root) for item in value)
        return [item for item in items if item is not _REDACTED]
    return value


def mask_personal_data(instance: Any, data: dict) -> dict:
    """Loại các trường được đánh dấu, kể cả trong đối tượng và mảng lồng nhau."""
    result = data
    for path, content in files_of(instance.definition).items():
        if path.endswith("-schema.json") and not path.endswith("-uischema.json"):
            schema = json.loads(content)
            result = _mask(result, schema, schema)
    return {} if result is _REDACTED else result


def mask_history(instance: Any, value: Any) -> Any:
    """Audit không trả lại dữ liệu form, kể cả khi nằm trong một đối tượng bọc."""
    if isinstance(value, dict):
        return {key: mask_history(instance, item)
                for key, item in mask_personal_data(instance, value).items()}
    if isinstance(value, list):
        return [mask_history(instance, item) for item in value]
    return value


def export_personal_data(session: Any, principal: Any, instance: Any, reason: str) -> dict:
    """Xuất có kiểm soát; audit chỉ chứa lý do, không chứa nội dung xuất."""
    if principal.is_system_admin or not principal.has_role("internal_auditor"):
        raise ApiError(403, "FORBIDDEN_PERSONAL_DATA", "Chỉ kiểm soát nội bộ được xuất dữ liệu cá nhân.", {"layer": 5})
    if not reason.strip():
        raise ApiError(422, "VALIDATION_FAILED", "Phải nêu lý do xuất dữ liệu cá nhân.")
    record(session, actor=principal, action="personal_data.export", object_type="workflow",
           object_id=str(instance.id), details={"reason": reason.strip()})
    return dict(instance.data)
