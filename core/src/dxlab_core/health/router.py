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
    summary="Trạng thái core, database và tìm kiếm",
    description="Không cần token. Trả 503 khi database hoặc chỉ mục tìm kiếm lỗi; thiếu mô hình embedding chỉ báo "
    "`embedding_model: missing`, vẫn 200.",
    responses={503: {"model": HealthOut, "description": "Database hoặc chỉ mục tìm kiếm lỗi"}},
)
def health(request: Request, response: Response) -> HealthOut:
    result = service.check(request.app.state.engine, request.app.state.search)
    if result.status != "ok":
        response.status_code = 503
    return result
