# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, Query, Request, UploadFile
from fastapi.responses import FileResponse

from dxlab_core.auth.deps import CurrentPrincipal
from dxlab_core.db import DbSession
from dxlab_core.documents import service, storage
from dxlab_core.documents.schemas import DocumentOut
from dxlab_core.errors import ErrorResponse
from dxlab_core.pagination import Page, PageParams, page_params

router = APIRouter(prefix="/documents", tags=["Tài liệu"])

_AUTH_ERRORS = {
    401: {"model": ErrorResponse, "description": "Thiếu hoặc sai token"},
    403: {"model": ErrorResponse, "description": "Vai trò không đủ quyền"},
}


@router.post(
    "",
    status_code=201,
    response_model=DocumentOut,
    summary="Tải tài liệu lên",
    description="`multipart/form-data`: tệp (`file`, tối đa 20 MB) cùng `app_id`, `kind`, `title`, `source`, `license`; "
    "tùy chọn `source_ref`, `workflow_id`. Tệp lưu theo SHA-256 của nội dung, không theo tên người dùng gửi; tệp `.md` "
    "và `text/*` được trích văn bản để tìm kiếm. Ghi audit `document.upload`. Báo giá (`quote`) do Ban CSVC, "
    "người thiết kế quy trình và kỹ thuật viên tải lên; SOP và tài liệu khác do Ban CSVC, người thiết kế quy trình.",
    responses={**_AUTH_ERRORS, 422: {"model": ErrorResponse, "description": "Thiếu trường, tệp rỗng hoặc quá lớn"}},
)
def upload_document(
    request: Request,
    session: DbSession,
    actor: CurrentPrincipal,
    file: Annotated[UploadFile, File(description="Nội dung tệp")],
    app_id: Annotated[str, Form(description="Mã ứng dụng, ví dụ `lab-repair`")],
    kind: Annotated[str, Form(description="`sop`, `quote` hoặc `other`")],
    title: Annotated[str, Form(description="Tiêu đề hiển thị")],
    source: Annotated[str, Form(description="Nguồn của tài liệu: URI hoặc mô tả")],
    license: Annotated[str, Form(description="Giấy phép, ví dụ `CC-BY-4.0`")],
    source_ref: Annotated[str | None, Form(description="Vị trí cụ thể trong nguồn")] = None,
    workflow_id: Annotated[uuid.UUID | None, Form(description="Phiếu mà tài liệu đính kèm")] = None,
) -> DocumentOut:
    document = service.create_document(
        session,
        actor,
        request.app.state.settings.documents_dir,
        file.file,
        filename=file.filename,
        content_type=file.content_type,
        app_id=app_id,
        kind=kind,
        title=title,
        source=source,
        license=license,
        source_ref=source_ref,
        workflow_id=workflow_id,
    )
    return DocumentOut.model_validate(document)


@router.get(
    "",
    response_model=Page[DocumentOut],
    summary="Danh sách tài liệu",
    description="Chỉ gồm tài liệu người gọi được xem; mới nhất trước.",
    responses=_AUTH_ERRORS,
)
def list_documents(
    session: DbSession,
    principal: CurrentPrincipal,
    page: Annotated[PageParams, Depends(page_params)],
    app_id: Annotated[str | None, Query(description="Lọc theo ứng dụng")] = None,
    kind: Annotated[str | None, Query(description="Lọc theo loại: `sop`, `quote`, `other`")] = None,
) -> Page[DocumentOut]:
    items, total = service.list_documents(session, principal, page, app_id=app_id, kind=kind)
    return Page[DocumentOut](items=[DocumentOut.model_validate(item) for item in items], total=total)


@router.get(
    "/{document_id}",
    response_model=DocumentOut,
    summary="Xem metadata của tài liệu",
    responses={**_AUTH_ERRORS, 404: {"model": ErrorResponse, "description": "Không có hoặc không được xem"}},
)
def get_document(document_id: uuid.UUID, session: DbSession, principal: CurrentPrincipal) -> DocumentOut:
    return DocumentOut.model_validate(service.get_document(session, principal, document_id))


@router.get(
    "/{document_id}/content",
    response_class=FileResponse,
    summary="Tải nội dung tài liệu",
    description="Trả nguyên byte đã tải lên, kèm `Content-Disposition: attachment` và tên tệp gốc.",
    responses={
        **_AUTH_ERRORS,
        200: {"content": {"application/octet-stream": {}}, "description": "Nội dung tệp"},
        404: {"model": ErrorResponse, "description": "Không có hoặc không được xem"},
    },
)
def download_document(
    document_id: uuid.UUID, request: Request, session: DbSession, principal: CurrentPrincipal
) -> FileResponse:
    document = service.get_document(session, principal, document_id)
    return FileResponse(
        storage.path_for(request.app.state.settings.documents_dir, document.sha256),
        media_type=document.content_type,
        filename=document.filename,
        headers={"X-Content-Type-Options": "nosniff"},
    )
