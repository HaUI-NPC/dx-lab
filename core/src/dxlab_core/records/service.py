# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

import re
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import Text, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from dxlab_core.audit import service as audit
from dxlab_core.auth.principal import Principal
from dxlab_core.errors import ApiError, Conflict, NotFound, ValidationFailed
from dxlab_core.pagination import PageParams
from dxlab_core.records import validation
from dxlab_core.records.models import Record, RecordType

_KEY = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}")


class InvalidRecordSchema(ApiError):
    """Schema của loại bản ghi không phải JSON Schema Draft 2020-12 hợp lệ; `details.errors` là `{"path", "message"}`."""

    def __init__(self, errors: list[dict[str, str]]) -> None:
        super().__init__(422, "VALIDATION_FAILED", "Schema của loại bản ghi không hợp lệ.", {"errors": errors})


def register_record_type(session: Session, app_id: str, record_type: str, schema: dict[str, Any]) -> RecordType:
    """Đăng ký (hoặc nâng phiên bản) loại bản ghi của một ứng dụng.

    CORE-03 gọi hàm này khi một phiên bản định nghĩa được áp dụng, với schema đọc từ
    `apps/<app>/records/<record_type>-record.json` của gói. Schema trùng nội dung thì giữ nguyên phiên bản;
    khác thì tăng `version` — bản ghi cũ giữ `schema_version` đã dùng khi ghi.
    """
    errors = validation.schema_errors(schema)
    if errors:
        raise InvalidRecordSchema(errors)
    existing = session.get(RecordType, (app_id, record_type), with_for_update=True)
    if existing is None:
        existing = RecordType(app_id=app_id, record_type=record_type, schema=schema, version=1)
        session.add(existing)
    elif existing.schema != schema:
        existing.schema = schema
        existing.version += 1
    session.flush()
    session.refresh(existing)
    return existing


def get_record_type(session: Session, app_id: str, record_type: str) -> RecordType:
    found = session.get(RecordType, (app_id, record_type))
    if found is None:
        raise NotFound(f"Ứng dụng `{app_id}` không có loại bản ghi `{record_type}`.")
    return found


def list_records(
    session: Session, app_id: str, record_type: str, page: PageParams, *, q: str | None = None, unit: str | None = None
) -> tuple[list[Record], int]:
    """Danh sách có phân trang. `q`: mọi từ phải xuất hiện (không phân biệt hoa thường) trong khóa hoặc dữ liệu.

    `unit`: đơn vị theo trường `org_path` (hoặc `unit`) của dữ liệu, khớp chính đơn vị đó và các đơn vị con.
    """
    get_record_type(session, app_id, record_type)
    stmt = select(Record).where(Record.app_id == app_id, Record.record_type == record_type)
    for term in (q or "").split():
        stmt = stmt.where(
            or_(
                Record.key.icontains(term, autoescape=True),
                Record.data.cast(Text).icontains(term, autoescape=True),
            )
        )
    if unit:
        unit = unit.rstrip("/")
        owner = func.coalesce(Record.data["org_path"].astext, Record.data["unit"].astext)
        stmt = stmt.where(or_(owner == unit, owner.startswith(unit + "/", autoescape=True)))
    total = session.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    items = session.scalars(stmt.order_by(Record.key).limit(page.limit).offset(page.offset))
    return list(items), total


def get_record(session: Session, app_id: str, record_type: str, key: str) -> Record:
    found = session.get(Record, (app_id, record_type, key))
    if found is None:
        raise NotFound(f"Không có bản ghi `{key}` thuộc loại `{record_type}` của ứng dụng `{app_id}`.")
    return found


def upsert_record(
    session: Session,
    actor: Principal,
    app_id: str,
    record_type: str,
    key: str,
    *,
    data: dict[str, Any],
    source: str,
    license: str,
    source_ref: str | None = None,
) -> tuple[Record, bool]:
    """Tạo hoặc sửa bản ghi sau khi kiểm `data` bằng schema của loại; trả `(bản ghi, đã_tạo_mới)`."""
    if not _KEY.fullmatch(key):
        raise ValidationFailed([{"path": "key", "message": "Khóa chỉ gồm chữ, số, `.`, `_`, `-`, dài tối đa 128 ký tự."}])
    rtype = get_record_type(session, app_id, record_type)
    errors = validation.data_errors(rtype.schema, data)
    if errors:
        raise ValidationFailed(errors)

    now = datetime.now(UTC)
    record = session.get(Record, (app_id, record_type, key), with_for_update=True)
    created = record is None
    if record is None:
        record = Record(
            app_id=app_id,
            record_type=record_type,
            key=key,
            created_by=actor.username,
            created_at=now,
        )
        session.add(record)
    record.data = data
    record.schema_version = rtype.version
    record.source = source
    record.license = license
    record.source_ref = source_ref
    record.updated_by = actor.username
    record.updated_at = now
    try:
        session.flush()
    except IntegrityError:
        # Hai yêu cầu cùng tạo một khóa: bên đến sau báo xung đột để client đọc lại rồi thử.
        raise Conflict("Bản ghi vừa được người khác tạo, tải lại rồi thử lại.") from None
    audit.record(
        session,
        actor=actor,
        action="record.upsert",
        object_type="record",
        object_id=f"{app_id}/{record_type}/{key}",
        details={
            "created": created,
            "schema_version": rtype.version,
            "source": source,
            "license": license,
            "source_ref": source_ref,
        },
    )
    return record, created
