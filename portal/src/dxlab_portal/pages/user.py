# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

"""Thông tin người đăng nhập để hiển thị: tên và vai trò theo từng đơn vị."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# Vai trò mặc định của mọi tài khoản đã đăng nhập, không có nhóm riêng (docs/AUTHZ.md mục 3).
DEFAULT_ROLE = "reporter"


@dataclass(frozen=True)
class RoleInUnit:
    role: str
    unit: str | None


@dataclass(frozen=True)
class UserView:
    username: str
    name: str
    roles: list[RoleInUnit] = field(default_factory=list)
    # "core" nếu vai trò lấy từ /api/me, "token" nếu lấy từ claim `groups` của token.
    source: str = "token"

    @property
    def role_labels(self) -> list[str]:
        return [f"{r.role} · {r.unit}" if r.unit else r.role for r in self.roles]


def roles_from_groups(groups: list[str]) -> list[RoleInUnit]:
    """Tách đường dẫn nhóm: đoạn cuối là vai trò, phần trước là đơn vị (docs/AUTHZ.md mục 2)."""
    roles: list[RoleInUnit] = []
    for path in groups:
        parts = [p for p in str(path).split("/") if p]
        if not parts:
            continue
        unit = "/" + "/".join(parts[:-1]) if len(parts) > 1 else None
        roles.append(RoleInUnit(role=parts[-1], unit=unit))
    return roles


def user_from_claims(claims: dict[str, Any]) -> UserView:
    username = str(claims.get("preferred_username") or claims.get("sub") or "")
    name = str(claims.get("name") or username)
    groups = claims.get("groups")
    roles = roles_from_groups(groups if isinstance(groups, list) else [])
    if not roles:
        roles = [RoleInUnit(DEFAULT_ROLE, None)]
    return UserView(username=username, name=name, roles=roles)


def user_from_me(me: dict[str, Any], fallback: UserView) -> UserView:
    """Ưu tiên ``/api/me`` của core: đó là vai trò mà core thực sự áp dụng."""
    raw_roles = me.get("roles")
    roles = (
        [RoleInUnit(str(r.get("role")), r.get("unit")) for r in raw_roles if isinstance(r, dict)]
        if isinstance(raw_roles, list)
        else []
    )
    return UserView(
        username=str(me.get("username") or fallback.username),
        name=str(me.get("name") or fallback.name),
        roles=roles or fallback.roles,
        source="core" if roles else fallback.source,
    )
