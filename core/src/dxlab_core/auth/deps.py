# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

"""Dependency xác thực và lớp 1 của phân quyền (docs/AUTHZ.md mục 1).

- `CurrentPrincipal`: người gọi đã xác thực, **không phải** `system_admin` (SoD-4). Dùng cho mọi route nghiệp vụ —
  mặc định từ chối tài khoản quản trị hệ thống.
- `AnyPrincipal`: người gọi đã xác thực, kể cả `system_admin`. Chỉ dùng cho route không chạm dữ liệu nghiệp vụ
  (ví dụ `/api/me`).
- `require_role(...)`: thêm điều kiện giữ ít nhất một vai trò.
"""

from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, Request

from dxlab_core.auth.principal import Principal
from dxlab_core.auth.tokens import Unauthenticated
from dxlab_core.errors import ApiError


class ForbiddenRole(ApiError):
    def __init__(self, message: str, details: dict[str, object] | None = None) -> None:
        super().__init__(403, "FORBIDDEN_ROLE", message, {"layer": 1, **(details or {})})


def _bearer_token(request: Request) -> str:
    scheme, _, token = request.headers.get("authorization", "").partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        raise Unauthenticated()
    return token.strip()


def get_any_principal(request: Request) -> Principal:
    cached = getattr(request.state, "principal", None)
    if cached is not None:
        return cached
    claims = request.app.state.token_verifier.verify(_bearer_token(request))
    principal = Principal.from_claims(claims)
    request.state.principal = principal
    return principal


def get_principal(principal: Annotated[Principal, Depends(get_any_principal)]) -> Principal:
    if principal.is_system_admin:
        raise ForbiddenRole("Tài khoản quản trị hệ thống không được thực hiện thao tác nghiệp vụ.", {"rule": "SoD-4"})
    return principal


AnyPrincipal = Annotated[Principal, Depends(get_any_principal)]
CurrentPrincipal = Annotated[Principal, Depends(get_principal)]


def require_role(*roles: str) -> Callable[[Principal], Principal]:
    """Dependency: người gọi (không phải system_admin) phải giữ ít nhất một trong `roles`."""

    def dependency(principal: CurrentPrincipal) -> Principal:
        if not any(principal.has_role(role) for role in roles):
            raise ForbiddenRole("Bạn không có vai trò cần cho thao tác này.", {"required_roles": list(roles)})
        return principal

    return dependency
