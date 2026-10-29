# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

from typing import Annotated

from fastapi import APIRouter, File, UploadFile
from fastapi.responses import Response

from dxlab_core.auth.deps import CurrentPrincipal
from dxlab_core.db import DbSession
from dxlab_core.definitions import service
from dxlab_core.definitions.models import DefinitionVersion
from dxlab_core.definitions.schemas import AppOut, FileOut, StartFormOut, VersionOut
from dxlab_core.errors import ErrorResponse, NotFound
from dxlab_core.pagination import Page

router = APIRouter(prefix="/definitions", tags=["Định nghĩa ứng dụng"])

_ERRORS = {
    401: {"model": ErrorResponse, "description": "Thiếu hoặc sai token"},
    403: {"model": ErrorResponse, "description": "Không đủ quyền (lớp 1) hoặc vi phạm không kiêm nhiệm (SoD-5)"},
    404: {"model": ErrorResponse, "description": "Không có ứng dụng / phiên bản"},
}
MAX_UPLOAD_FILES = 200


def _version_out(version: DefinitionVersion) -> VersionOut:
    return VersionOut(
        app_id=version.app_id,
        version=version.version,
        status=version.status,
        display_name=version.display_name,
        process_id=version.process_id,
        checksum=version.checksum,
        published_by=version.published_by,
        published_at=version.published_at,
        activated_by=version.activated_by,
        activated_at=version.activated_at,
        files=[FileOut(path=f.path, sha256=f.sha256, size=len(f.content)) for f in version.files],
    )


@router.get("", response_model=Page[AppOut], summary="Ứng dụng đang có phiên bản áp dụng", responses=_ERRORS)
def list_apps(session: DbSession, _: CurrentPrincipal) -> Page[AppOut]:
    items = [
        AppOut(app_id=v.app_id, display_name=v.display_name, version=v.version, status=v.status)
        for v in service.list_active(session)
    ]
    return Page(items=items, total=len(items))


@router.post(
    "/{app_id}/versions",
    response_model=VersionOut,
    status_code=201,
    summary="Nạp một phiên bản mới của gói ứng dụng (chờ chủ quy trình duyệt)",
    description=(
        "Multipart: mỗi tệp của thư mục ứng dụng là một phần tên `files`, filename = đường dẫn tương đối "
        "(ví dụ `lab-repair.bpmn`, `records/room-record.json`). Thư mục `eval/` và tệp ẩn bị bỏ qua. "
        "`rule_admin` chỉ nạp được thay đổi `.dmn`; mọi thay đổi khác cần `process_admin`."
    ),
    responses={**_ERRORS, 409: {"model": ErrorResponse, "description": "Không có thay đổi"},
               422: {"model": ErrorResponse, "description": "DEFINITION_REJECTED: danh sách lỗi của validator"}},
)
async def publish(
    app_id: str,
    session: DbSession,
    principal: CurrentPrincipal,
    files: Annotated[list[UploadFile], File(description="Các tệp của gói ứng dụng")],
) -> VersionOut:
    if len(files) > MAX_UPLOAD_FILES:
        raise service.DefinitionRejected([{"file": "", "element": "", "message": "Gói có quá nhiều tệp."}])
    uploaded = {upload.filename or "": await upload.read() for upload in files}
    return _version_out(service.publish(session, principal, app_id, uploaded))


@router.get("/{app_id}/versions", response_model=Page[VersionOut], summary="Mọi phiên bản của một ứng dụng",
            responses=_ERRORS)
def list_versions(app_id: str, session: DbSession, _: CurrentPrincipal) -> Page[VersionOut]:
    items = [_version_out(v) for v in service.list_versions(session, app_id)]
    return Page(items=items, total=len(items))


@router.get("/{app_id}/versions/{version}", response_model=VersionOut, summary="Chi tiết một phiên bản",
            responses=_ERRORS)
def get_version(app_id: str, version: int, session: DbSession, _: CurrentPrincipal) -> VersionOut:
    return _version_out(service.find_version(session, app_id, version))


@router.post(
    "/{app_id}/versions/{version}/activate",
    response_model=VersionOut,
    summary="Chủ quy trình duyệt áp dụng phiên bản (phiếu mới dùng phiên bản này, phiếu cũ giữ phiên bản của nó)",
    responses={**_ERRORS, 409: {"model": ErrorResponse, "description": "Phiên bản không ở trạng thái chờ duyệt"}},
)
def activate(app_id: str, version: int, session: DbSession, principal: CurrentPrincipal) -> VersionOut:
    return _version_out(service.activate(session, principal, app_id, version))


@router.get(
    "/{app_id}/versions/{version}/files/{path:path}",
    summary="Tải một tệp của phiên bản (BPMN, DMN, form)",
    responses={**_ERRORS, 200: {"content": {"application/octet-stream": {}}}},
)
def get_file(app_id: str, version: int, path: str, session: DbSession, _: CurrentPrincipal) -> Response:
    found = service.find_version(session, app_id, version)
    for f in found.files:
        if f.path == path:
            media = "application/json" if path.endswith(".json") else "application/xml"
            return Response(content=f.content, media_type=media)
    raise NotFound(f"Phiên bản {version} không có tệp {path}.")


@router.get(
    "/{app_id}/start-form",
    response_model=StartFormOut,
    response_model_by_alias=True,
    summary="Form khởi tạo (bước người dùng đầu tiên) của phiên bản đang áp dụng",
    responses=_ERRORS,
)
def start_form(app_id: str, session: DbSession, _: CurrentPrincipal) -> StartFormOut:
    return StartFormOut(**service.start_form(session, app_id))
