# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

"""Nạp, kiểm, gắn phiên bản và duyệt áp dụng gói ứng dụng."""

import hashlib
import re
import uuid
from collections.abc import Mapping
from datetime import UTC, datetime
from functools import lru_cache
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from dxlab_core.audit.service import record
from dxlab_core.auth.principal import Principal
from dxlab_core.definitions.engine import LoadedPackage, first_user_task, form_of, load_package, read_process_model
from dxlab_core.definitions.models import ACTIVE, PENDING, SUPERSEDED, DefinitionFile, DefinitionVersion
from dxlab_core.definitions.validator import changed_kinds, package_files, validate_package
from dxlab_core.errors import ApiError, Conflict, NotFound

APP_ID = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")
PROCESS_ADMIN = "process_admin"
RULE_ADMIN = "rule_admin"
PROCESS_OWNER = "process_owner"


class DefinitionRejected(ApiError):
    def __init__(self, errors: list[dict[str, str]]) -> None:
        super().__init__(422, "DEFINITION_REJECTED", "Gói ứng dụng không qua được kiểm tra.", {"errors": errors})


def files_of(version: DefinitionVersion) -> dict[str, bytes]:
    return {f.path: f.content for f in version.files}


def _checksum(files: Mapping[str, bytes]) -> str:
    digest = hashlib.sha256()
    for path in sorted(files):
        digest.update(path.encode() + b"\0" + hashlib.sha256(files[path]).digest())
    return digest.hexdigest()


def find_version(session: Session, app_id: str, version: int, *, lock: bool = False) -> DefinitionVersion:
    stmt = select(DefinitionVersion).where(DefinitionVersion.app_id == app_id, DefinitionVersion.version == version)
    found = session.scalars(stmt.with_for_update() if lock else stmt).first()
    if found is None:
        raise NotFound(f"Không có phiên bản {version} của ứng dụng {app_id}.")
    return found


def active_version(session: Session, app_id: str) -> DefinitionVersion:
    stmt = select(DefinitionVersion).where(DefinitionVersion.app_id == app_id, DefinitionVersion.status == ACTIVE)
    found = session.scalars(stmt).first()
    if found is None:
        raise NotFound(f"Ứng dụng {app_id} chưa có phiên bản đang áp dụng.")
    return found


def _active_or_none(session: Session, app_id: str) -> DefinitionVersion | None:
    try:
        return active_version(session, app_id)
    except NotFound:
        return None


def _require_publish_right(principal: Principal, kinds: set[str], has_previous: bool) -> None:
    """Cửa 1 (docs/AUTHZ.md mục 4): `rule_admin` chỉ nạp thay đổi bảng luật; còn lại cần `process_admin`."""
    if principal.has_role(PROCESS_ADMIN):
        return
    if principal.has_role(RULE_ADMIN) and has_previous and kinds <= {"dmn"}:
        return
    raise ApiError(
        403,
        "FORBIDDEN_ROLE",
        "Bạn không được nạp loại tệp này: người soạn bảng luật chỉ nạp thay đổi .dmn, "
        "thay đổi quy trình, form hay ứng dụng mới cần cán bộ thiết kế quy trình.",
        {"layer": 1, "changed_kinds": sorted(kinds), "required_roles": [PROCESS_ADMIN]},
    )


def publish(session: Session, principal: Principal, app_id: str, uploaded: Mapping[str, bytes]) -> DefinitionVersion:
    if not APP_ID.match(app_id):
        raise DefinitionRejected([{"file": "", "element": "app_id",
                                   "message": "Mã ứng dụng chỉ gồm chữ thường, số, gạch ngang."}])
    files = package_files(uploaded)
    previous = _active_or_none(session, app_id)
    previous_files = files_of(previous) if previous else None
    kinds = changed_kinds(files, previous_files)
    _require_publish_right(principal, kinds, previous is not None)
    if previous is not None and not kinds:
        raise Conflict("Gói giống hệt phiên bản đang áp dụng, không có gì để nạp.", {"version": previous.version})

    issues = validate_package(files, previous_files)
    if issues:
        raise DefinitionRejected([issue.as_dict() for issue in issues])

    model = read_process_model(files)
    latest = session.scalar(select(func.max(DefinitionVersion.version)).where(DefinitionVersion.app_id == app_id))
    version = DefinitionVersion(
        id=uuid.uuid4(),
        app_id=app_id,
        version=(latest or 0) + 1,
        status=PENDING,
        display_name=model.display_name,
        process_id=model.primary_process_id,
        checksum=_checksum(files),
        published_by=principal.username,
        files=[
            DefinitionFile(path=path, sha256=hashlib.sha256(content).hexdigest(), content=content)
            for path, content in sorted(files.items())
        ],
    )
    session.add(version)
    session.flush()
    record(session, actor=principal, action="definition.publish", object_type="definition", object_id=app_id,
           details={"version": version.version, "changed_kinds": sorted(kinds), "checksum": version.checksum})
    return version


def activate(session: Session, principal: Principal, app_id: str, version_number: int) -> DefinitionVersion:
    """Cửa 3: `process_owner` duyệt; người nạp không tự duyệt (SoD-5). Phiên bản cũ thôi áp dụng cho việc mới."""
    if not principal.has_role(PROCESS_OWNER):
        raise ApiError(403, "FORBIDDEN_ROLE", "Chỉ chủ quy trình được duyệt áp dụng phiên bản.",
                       {"layer": 1, "required_roles": [PROCESS_OWNER]})
    version = find_version(session, app_id, version_number, lock=True)
    if version.published_by == principal.username:
        raise ApiError(403, "FORBIDDEN_SOD", "Người nạp phiên bản không được tự duyệt áp dụng.",
                       {"layer": 4, "rule": "SoD-5"})
    if version.status != PENDING:
        raise Conflict(f"Phiên bản {version_number} đang ở trạng thái {version.status}, không duyệt được.")
    current = _active_or_none(session, app_id)
    if current is not None:
        current.status = SUPERSEDED
        session.flush()
    version.status = ACTIVE
    version.activated_by = principal.username
    version.activated_at = datetime.now(UTC)
    session.flush()
    record(session, actor=principal, action="definition.activate", object_type="definition", object_id=app_id,
           details={"version": version.version, "previous_version": current.version if current else None})
    return version


def list_active(session: Session) -> list[DefinitionVersion]:
    stmt = select(DefinitionVersion).where(DefinitionVersion.status == ACTIVE).order_by(DefinitionVersion.app_id)
    return list(session.scalars(stmt))


def list_versions(session: Session, app_id: str) -> list[DefinitionVersion]:
    stmt = (
        select(DefinitionVersion)
        .where(DefinitionVersion.app_id == app_id)
        .order_by(DefinitionVersion.version.desc())
    )
    return list(session.scalars(stmt))


@lru_cache(maxsize=32)
def _package_cache(version_id: uuid.UUID, checksum: str, files: tuple[tuple[str, bytes], ...]) -> LoadedPackage:
    return load_package(dict(files))


def loaded_package(version: DefinitionVersion) -> LoadedPackage:
    """Spec SpiffWorkflow của một phiên bản (đã cache: nội dung phiên bản không bao giờ đổi)."""
    return _package_cache(version.id, version.checksum, tuple(sorted(files_of(version).items())))


def start_form(session: Session, app_id: str) -> dict[str, Any]:
    version = active_version(session, app_id)
    task_spec = first_user_task(loaded_package(version).spec)
    if task_spec is None:
        raise NotFound(f"Ứng dụng {app_id} không có bước người dùng nào.")
    schema, uischema = form_of(task_spec, files_of(version))
    return {
        "app_id": app_id,
        "version": version.version,
        "step_id": task_spec.bpmn_id,
        "step_name": task_spec.bpmn_name or task_spec.bpmn_id,
        "schema": schema,
        "uischema": uischema,
    }
