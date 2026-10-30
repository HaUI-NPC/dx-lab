# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

"""Đọc thứ tự cấp thẩm quyền từ output của bảng DMN đã ghim theo phiếu."""

import ast
import operator
import xml.etree.ElementTree as ET
from typing import Any

from dxlab_core.auth.principal import unit_contains
from dxlab_core.definitions.service import files_of


_ARITHMETIC = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv}
_UNARY = {ast.USub: operator.neg, ast.UAdd: operator.pos}


def _evaluate(node: ast.AST) -> Any:
    """Hằng số và phép tính số học đơn giản, đúng tập mà validator cho phép trong ô kết quả DMN."""
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY:
        return _UNARY[type(node.op)](_evaluate(node.operand))
    if isinstance(node, ast.BinOp) and type(node.op) in _ARITHMETIC:
        return _ARITHMETIC[type(node.op)](_evaluate(node.left), _evaluate(node.right))
    raise ValueError("biểu thức không được hỗ trợ")


def _literal(text: str | None) -> Any:
    if text is None:
        return None
    try:
        return _evaluate(ast.parse(text.strip(), mode="eval").body)
    except (ValueError, SyntaxError, TypeError, ZeroDivisionError):
        return None


def authority_levels(instance: Any) -> list[dict[str, Any]]:
    """Lấy output của các dòng có quyền duyệt, giữ đúng thứ tự của bảng FIRST."""
    required = {"approver_role", "approval_scope", "approval_limit_vnd", "approval_required"}
    for path, content in files_of(instance.definition).items():
        if not path.endswith(".dmn"):
            continue
        root = ET.fromstring(content)
        for table in root.findall(".//{*}decisionTable"):
            names = [node.get("name") for node in table.findall("{*}output")]
            if not required.issubset(names):
                continue
            levels = []
            for rule in table.findall("{*}rule"):
                values = [_literal(entry.findtext("{*}text")) for entry in rule.findall("{*}outputEntry")]
                row = dict(zip(names, values))
                if row.get("approval_required") is True and row.get("approver_role"):
                    if not levels or row["approver_role"] != levels[-1]["approver_role"]:
                        levels.append(row)
            return levels
    return []


def next_authority(instance: Any, role: str) -> dict[str, Any] | None:
    levels = authority_levels(instance)
    return next((levels[index + 1] for index, row in enumerate(levels[:-1])
                 if row["approver_role"] == role), None)


def actor_has_authority(event: Any, role: str, scope_unit: str | None) -> bool:
    for assignment in event.actor_roles or []:
        if assignment.get("role") != role:
            continue
        unit = assignment.get("unit")
        if scope_unit is None or (unit and unit_contains(unit, scope_unit)):
            return True
    return False


def escalate(instance: Any, data: dict, events: list[Any]) -> None:
    """Leo thang khi một trong các diễn viên bị loại giữ vai trò duyệt hiện tại."""
    while True:
        role = data.get("approver_role")
        scope = data.get("approval_scope")
        scope_unit = {"faculty": data.get("owner_faculty"),
                      "school": data.get("owner_school"),
                      "university": None}.get(scope)
        if scope != "university" and not scope_unit:
            return
        if not any(actor_has_authority(event, role, scope_unit) for event in events):
            return
        level = next_authority(instance, role)
        if level is None:
            return
        for key in ("approver_role", "approval_scope", "approval_limit_vnd", "signing_type", "authority_basis"):
            if key in level:
                data[key] = level[key]
