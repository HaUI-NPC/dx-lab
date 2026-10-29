# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response

from dxlab_core.auth.deps import CurrentPrincipal, require_role
from dxlab_core.auth.principal import Principal
from dxlab_core.db import DbSession
from dxlab_core.errors import ErrorResponse
from dxlab_core.pagination import Page, PageParams, page_params
from dxlab_core.records import service
from dxlab_core.records.schemas import RecordIn, RecordOut

router = APIRouter(prefix="/records", tags=["Danh mục"])

# Danh mục là dữ liệu nhập liệu của Ban CSVC và người thiết kế quy trình (docs/AUTHZ.md mục 3); system_admin bị chặn (SoD-4).
RecordWriter = Annotated[Principal, Depends(require_role("facility_officer", "process_admin"))]

_AUTH_ERRORS = {
    401: {"model": ErrorResponse, "description": "Thiếu hoặc sai token"},
    403: {"model": ErrorResponse, "description": "Vai trò không đủ quyền"},
}


@router.get(
    "/{app_id}/{record_type}",
    response_model=Page[RecordOut],
    summary="Danh sách bản ghi của một loại",
    description="Mọi người đã đăng nhập đều đọc được. `q`: mọi từ phải có trong khóa hoặc dữ liệu (không phân biệt hoa thường). "
    "`unit`: đơn vị theo trường `org_path` (hoặc `unit`) của bản ghi, gồm cả các đơn vị con.",
    responses={**_AUTH_ERRORS, 404: {"model": ErrorResponse, "description": "Ứng dụng không có loại bản ghi này"}},
)
def list_records(
    app_id: str,
    record_type: str,
    session: DbSession,
    _: CurrentPrincipal,
    page: Annotated[PageParams, Depends(page_params)],
    q: Annotated[str | None, Query(max_length=200, description="Từ khóa, cách nhau bằng dấu cách")] = None,
    unit: Annotated[str | None, Query(max_length=500, description="Đường dẫn đơn vị, ví dụ `/haui/sict/khmt`")] = None,
) -> Page[RecordOut]:
    items, total = service.list_records(session, app_id, record_type, page, q=q, unit=unit)
    return Page[RecordOut](items=[RecordOut.model_validate(item) for item in items], total=total)


@router.get(
    "/{app_id}/{record_type}/{key}",
    response_model=RecordOut,
    summary="Xem một bản ghi",
    responses={**_AUTH_ERRORS, 404: {"model": ErrorResponse, "description": "Không có bản ghi"}},
)
def get_record(app_id: str, record_type: str, key: str, session: DbSession, _: CurrentPrincipal) -> RecordOut:
    return RecordOut.model_validate(service.get_record(session, app_id, record_type, key))


@router.put(
    "/{app_id}/{record_type}/{key}",
    response_model=RecordOut,
    summary="Tạo hoặc sửa một bản ghi",
    description="Tạo mới trả 201, sửa trả 200. `data` được kiểm bằng JSON Schema của loại bản ghi; `source` và `license` "
    "bắt buộc. Người tạo và thời điểm tạo giữ nguyên khi sửa; người sửa và thời điểm sửa cập nhật. Ghi audit `record.upsert`.",
    responses={
        **_AUTH_ERRORS,
        201: {"model": RecordOut, "description": "Đã tạo bản ghi mới"},
        404: {"model": ErrorResponse, "description": "Ứng dụng không có loại bản ghi này"},
        409: {"model": ErrorResponse, "description": "Bản ghi vừa được người khác tạo"},
        422: {"model": ErrorResponse, "description": "Dữ liệu sai JSON Schema; `details.errors` ghi đường dẫn từng lỗi"},
    },
)
def put_record(
    app_id: str,
    record_type: str,
    key: str,
    body: RecordIn,
    response: Response,
    session: DbSession,
    actor: RecordWriter,
) -> RecordOut:
    record, created = service.upsert_record(
        session,
        actor,
        app_id,
        record_type,
        key,
        data=body.data,
        source=body.source,
        license=body.license,
        source_ref=body.source_ref,
    )
    if created:
        response.status_code = 201
    return RecordOut.model_validate(record)
