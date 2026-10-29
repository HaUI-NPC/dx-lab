# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

"""Người gọi API: tên, vai trò và đơn vị tách từ claim `groups` của token (docs/AUTHZ.md mục 2).

Vai trò gắn với đơn vị là một nhóm con mang tên khóa vai trò: `/haui/sict/khmt/lab-a1-305/lab_manager`
→ vai trò `lab_manager` tại đơn vị `/haui/sict/khmt/lab-a1-305`. Mọi người đã đăng nhập đều có vai trò
`reporter`. Core không giữ danh sách đơn vị hay vai trò của ứng dụng nào.
"""

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any

REPORTER = "reporter"
SYSTEM_ADMIN = "system_admin"


@dataclass(frozen=True)
class RoleAssignment:
    role: str
    unit: str


@dataclass(frozen=True)
class Principal:
    username: str
    name: str
    roles: tuple[RoleAssignment, ...]

    @classmethod
    def from_claims(cls, claims: Mapping[str, Any]) -> "Principal":
        username = str(claims.get("preferred_username") or claims.get("sub") or "")
        return cls(
            username=username,
            name=str(claims.get("name") or username),
            roles=parse_groups(claims.get("groups") or ()),
        )

    def has_role(self, role: str) -> bool:
        return role == REPORTER or any(assignment.role == role for assignment in self.roles)

    def units_for(self, role: str) -> tuple[str, ...]:
        """Các đơn vị mà người này giữ `role`."""
        return tuple(assignment.unit for assignment in self.roles if assignment.role == role)

    @property
    def is_system_admin(self) -> bool:
        return any(assignment.role == SYSTEM_ADMIN for assignment in self.roles)


def parse_groups(groups: Iterable[str]) -> tuple[RoleAssignment, ...]:
    """Tách vai trò và đơn vị; bỏ qua nhóm không có đơn vị cha (ví dụ `/haui`)."""
    assignments: list[RoleAssignment] = []
    for path in groups:
        parts = [part for part in str(path).split("/") if part]
        if len(parts) < 2:
            continue
        assignment = RoleAssignment(role=parts[-1], unit="/" + "/".join(parts[:-1]))
        if assignment not in assignments:
            assignments.append(assignment)
    return tuple(assignments)


def unit_contains(ancestor: str, unit: str) -> bool:
    """`unit` là `ancestor` hoặc nằm dưới `ancestor` trong cây tổ chức."""
    ancestor = ancestor.rstrip("/")
    return unit == ancestor or unit.startswith(ancestor + "/")
