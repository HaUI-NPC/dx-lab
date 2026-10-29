# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

"""Nạp thuộc tính có thẩm quyền của đối tượng từ record, không tin đầu vào client."""

from typing import Any

from sqlalchemy.orm import Session

from dxlab_core.errors import ApiError


def apply_record_bindings(session: Session, app_id: str, metadata: dict, data: dict[str, Any]) -> None:
    # Record là tài nguyên độc lập; tra trong cùng transaction với việc tạo phiếu.
    from dxlab_core.records.service import get_record

    for binding in metadata.get("record_bindings", []):
        key = data.get(binding["key_field"])
        if not isinstance(key, str) or not key:
            raise ApiError(422, "VALIDATION_FAILED", "Thiếu mã đối tượng liên kết.")
        record = get_record(session, app_id, binding["type"], key)
        for source, destination in binding["fields"].items():
            if source not in record.data:
                raise ApiError(422, "VALIDATION_FAILED", "Đối tượng liên kết thiếu thuộc tính bắt buộc.")
            data[destination] = record.data[source]
    room = data.get("room_unit")
    if room is not None:
        if not isinstance(room, str) or not room.startswith("/") or len(room.strip("/").split("/")) < 4:
            raise ApiError(422, "VALIDATION_FAILED", "Đường dẫn đơn vị phòng không hợp lệ.")
        data["owner_faculty"] = room.rsplit("/", 1)[0]
        data["owner_school"] = data["owner_faculty"].rsplit("/", 1)[0]
