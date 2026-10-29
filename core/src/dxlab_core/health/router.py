# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

from fastapi import APIRouter, Request, Response

from dxlab_core.health import service
from dxlab_core.health.schemas import HealthOut

router = APIRouter(tags=["Hệ thống"])


@router.get(
    "/health",
    response_model=HealthOut,
    summary="Trạng thái core và kết nối database",
    description="Không cần token. Trả 503 khi database không kết nối được.",
    responses={503: {"model": HealthOut, "description": "Database không kết nối được"}},
)
def health(request: Request, response: Response) -> HealthOut:
    result = service.check(request.app.state.engine)
    if result.status != "ok":
        response.status_code = 503
    return result
