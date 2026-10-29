# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

import mimetypes
import re
import unicodedata
import uuid
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from typing import BinaryIO

from sqlalchemy import ColumnElement, and_, func, or_, select, true
from sqlalchemy.orm import Session

from dxlab_core.audit import service as audit
from dxlab_core.auth.principal import SYSTEM_ADMIN, Principal
from dxlab_core.documents import storage
from dxlab_core.documents.models import KINDS, Document
from dxlab_core.errors import ApiError, NotFound, ValidationFailed
from dxlab_core.pagination import PageParams
from dxlab_core.workflows.access import can_read, visible_clause
from dxlab_core.workflows.models import Workflow

# Ai được tải tài liệu lên [GĐ]: danh mục tri thức do Ban CSVC và người thiết kế quy trình quản;
# báo giá còn do kỹ thuật viên đính kèm khi lập biên bản tình trạng (docs/AUTHZ.md mục 4, `technical_assessment.confirm`).
UPLOAD_ROLES = frozenset({"facility_officer", "process_admin"})
QUOTE_UPLOAD_ROLES = UPLOAD_ROLES | {"it_technician", "lab_technician", "facility_technician"}

_APP_ID = re.compile(r"[a-z0-9][a-z0-9-]{0,63}")
_CONTROL = re.compile(r"[\x00-\x1f\x7f]")
_CONTENT_TYPE = re.compile(r"[a-z0-9][a-z0-9!#$&^_.+-]*/[a-z0-9][a-z0-9!#$&^_.+-]*")
_TEXT_SUFFIXES = {".md", ".markdown", ".txt"}


def _forbidden(message: str) -> ApiError:
    return ApiError(403, "FORBIDDEN_ROLE", message, {"layer": 1})


def can_upload(principal: Principal, kind: str) -> bool:
    allowed = QUOTE_UPLOAD_ROLES if kind == "quote" else UPLOAD_ROLES
    return any(assignment.role in allowed for assignment in principal.roles)


def _has_business_role(principal: Principal) -> bool:
    return any(assignment.role != SYSTEM_ADMIN for assignment in principal.roles)


def visible_to(principal: Principal) -> ColumnElement[bool]:
    """Điều kiện SQL: tài liệu người này được xem (dùng cho danh sách và tìm kiếm).

    Tài liệu gắn phiếu chỉ hiển thị cho người được xem phiếu đó. Tài liệu không gắn phiếu giữ quy tắc
    danh mục [GĐ]: báo giá chỉ hiển thị cho người tải lên hoặc người giữ vai trò nghiệp vụ.
    """
    unlinked = true() if _has_business_role(principal) else or_(
        Document.kind != "quote", Document.created_by == principal.username
    )
    linked = select(Workflow.id).where(
        Workflow.id == Document.workflow_id,
        Workflow.app_id == Document.app_id,
        visible_clause(principal),
    ).exists()
    return or_(and_(Document.workflow_id.is_(None), unlinked), linked)


def clean_filename(raw: str | None) -> str:
    """Chỉ lấy tên cuối, bỏ ký tự điều khiển; dùng để hiển thị và đặt tên khi tải về, không để lưu."""
    name = PurePosixPath((raw or "").replace("\\", "/")).name
    name = _CONTROL.sub("", name).strip()
    return name[:255] or "tep-tai-len"


def resolve_content_type(filename: str, declared: str | None) -> str:
    declared = (declared or "").split(";")[0].strip().lower()
    if _CONTENT_TYPE.fullmatch(declared) and declared != "application/octet-stream":
        return declared[:255]
    suffix = PurePosixPath(filename).suffix.lower()
    if suffix in (".md", ".markdown"):
        return "text/markdown"
    return mimetypes.guess_type(filename)[0] or "application/octet-stream"


def _extract_text(path: Path, filename: str, content_type: str) -> str | None:
    """Văn bản của tệp `.md` / `.txt` / `text/*`; dạng khác trả `None`."""
    if content_type.startswith("text/") or PurePosixPath(filename).suffix.lower() in _TEXT_SUFFIXES:
        # Postgres không lưu được NUL trong text. NFC: chữ có dấu luôn ở dạng dựng sẵn, để tìm kiếm khớp mọi nguồn gõ.
        text = path.read_text(encoding="utf-8", errors="replace").replace("\x00", "")
        return unicodedata.normalize("NFC", text)
    return None


def create_document(
    session: Session,
    actor: Principal,
    documents_dir: Path,
    stream: BinaryIO,
    *,
    filename: str | None,
    content_type: str | None,
    app_id: str,
    kind: str,
    title: str,
    source: str,
    license: str,
    source_ref: str | None = None,
    workflow_id: uuid.UUID | None = None,
) -> Document:
    if not can_upload(actor, kind):
        raise _forbidden("Vai trò của bạn không được tải tài liệu loại này lên.")
    errors: list[dict[str, str]] = []
    if not _APP_ID.fullmatch(app_id):
        errors.append({"path": "app_id", "message": "Mã ứng dụng chỉ gồm chữ thường, số, gạch ngang."})
    if kind not in KINDS:
        errors.append({"path": "kind", "message": f"Loại tài liệu phải là một trong: {', '.join(KINDS)}."})
    for field, value, limit in (("title", title, 255), ("source", source, 2000), ("license", license, 255)):
        if not value.strip():
            errors.append({"path": field, "message": "Không được để trống."})
        elif len(value) > limit:
            errors.append({"path": field, "message": f"Dài tối đa {limit} ký tự."})
    if errors:
        raise ValidationFailed(errors)
    if workflow_id is not None:
        workflow = session.get(Workflow, workflow_id)
        if workflow is None or workflow.app_id != app_id or not can_read(actor, workflow):
            raise NotFound("Không tìm thấy phiếu.")

    name = clean_filename(filename)
    try:
        sha256, size = storage.save(documents_dir, stream, max_bytes=storage.MAX_BYTES)
    except storage.TooLarge:
        raise ValidationFailed(
            [{"path": "file", "message": f"Tệp vượt quá {storage.MAX_BYTES // (1024 * 1024)} MB."}]
        ) from None
    if size == 0:
        raise ValidationFailed([{"path": "file", "message": "Tệp rỗng."}])
    ctype = resolve_content_type(name, content_type)
    document = Document(
        app_id=app_id,
        kind=kind,
        title=title.strip(),
        filename=name,
        content_type=ctype,
        size=size,
        sha256=sha256,
        text=_extract_text(storage.path_for(documents_dir, sha256), name, ctype),
        workflow_id=workflow_id,
        source=source.strip(),
        license=license.strip(),
        source_ref=source_ref,
        created_by=actor.username,
        created_at=datetime.now(UTC),
    )
    session.add(document)
    session.flush()
    audit.record(
        session,
        actor=actor,
        action="document.upload",
        object_type="document",
        object_id=str(document.id),
        details={
            "app_id": app_id,
            "kind": kind,
            "sha256": sha256,
            "size": size,
            "content_type": ctype,
            "workflow_id": str(workflow_id) if workflow_id else None,
            "source": document.source,
            "license": document.license,
        },
    )
    return document


def list_documents(
    session: Session, principal: Principal, page: PageParams, *, app_id: str | None = None, kind: str | None = None
) -> tuple[list[Document], int]:
    conditions = [visible_to(principal)]
    if app_id:
        conditions.append(Document.app_id == app_id)
    if kind:
        conditions.append(Document.kind == kind)
    stmt = select(Document).where(and_(*conditions))
    total = session.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    items = session.scalars(stmt.order_by(Document.created_at.desc(), Document.id).limit(page.limit).offset(page.offset))
    return list(items), total


def get_document(session: Session, principal: Principal, document_id: uuid.UUID) -> Document:
    """Không thấy hoặc không được xem đều báo `NOT_FOUND` để không lộ sự tồn tại của tài liệu."""
    document = session.scalar(select(Document).where(Document.id == document_id, visible_to(principal)))
    if document is None:
        raise NotFound("Không tìm thấy tài liệu.")
    return document
