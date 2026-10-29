# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

from fastapi import APIRouter

from dxlab_core.auth.deps import AnyPrincipal
from dxlab_core.auth.schemas import MeOut, RoleOut
from dxlab_core.errors import ErrorResponse

router = APIRouter(tags=["Người dùng"])


@router.get(
    "/me",
    response_model=MeOut,
    summary="Người đang gọi: tên, vai trò, đơn vị tách từ token",
    responses={401: {"model": ErrorResponse, "description": "Thiếu hoặc sai token"}},
)
def me(principal: AnyPrincipal) -> MeOut:
    roles = [RoleOut(role=a.role, unit=a.unit) for a in principal.roles]
    return MeOut(
        username=principal.username,
        name=principal.name,
        roles=roles,
        units=sorted({a.unit for a in principal.roles}),
    )
