# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

"""API số liệu tổng hợp theo quyền xem phiếu của người gọi."""
from fastapi import APIRouter

from dxlab_core.auth.deps import CurrentPrincipal
from dxlab_core.db import DbSession
from dxlab_core.stats import service

router = APIRouter(prefix="/stats", tags=["Thống kê"])


@router.get("")
def stats(principal: CurrentPrincipal, session: DbSession, app_id: str | None = None) -> dict:
    """Thống kê trạng thái, đơn vị, quá hạn và chi phí, tùy lọc theo ứng dụng."""
    return service.collect(session, principal, app_id)
