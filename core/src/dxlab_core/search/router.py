# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request

from dxlab_core.auth.deps import CurrentPrincipal
from dxlab_core.db import DbSession
from dxlab_core.errors import ErrorResponse
from dxlab_core.pagination import PageParams, page_params
from dxlab_core.search import service
from dxlab_core.search.schemas import SearchOut

router = APIRouter(prefix="/search", tags=["Tìm kiếm"])


@router.get(
    "",
    response_model=SearchOut,
    summary="Tìm tài liệu (toàn văn + vector)",
    description="Tìm trong văn bản tài liệu, không phân biệt hoa thường và dấu tiếng Việt (`may tinh khong len` khớp "
    "\"máy tính không lên\"). Kết quả chỉ gồm tài liệu người gọi được xem, mỗi kết quả kèm trích đoạn và tài liệu nguồn "
    "(nguồn, giấy phép). `mode` là `hybrid` khi có mô hình embedding, `fts` khi thiếu mô hình: khi đó chỉ dùng toàn văn.",
    responses={
        401: {"model": ErrorResponse, "description": "Thiếu hoặc sai token"},
        403: {"model": ErrorResponse, "description": "Tài khoản quản trị hệ thống không được tìm dữ liệu nghiệp vụ"},
        422: {"model": ErrorResponse, "description": "Từ khóa trống"},
    },
)
def search(
    request: Request,
    session: DbSession,
    principal: CurrentPrincipal,
    page: Annotated[PageParams, Depends(page_params)],
    q: Annotated[str, Query(max_length=500, description="Câu hỏi hoặc từ khóa")],
    app_id: Annotated[str | None, Query(description="Chỉ tìm trong một ứng dụng")] = None,
    kind: Annotated[str | None, Query(description="Chỉ tìm một loại tài liệu: `sop`, `quote`, `other`")] = None,
) -> SearchOut:
    return service.search(session, principal, request.app.state.search, q, page, app_id=app_id, kind=kind)
