# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from dxlab_core.utc import UtcDatetime


class RecordIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    data: dict[str, Any] = Field(description="Nội dung bản ghi; phải khớp JSON Schema của loại bản ghi")
    source: str = Field(min_length=1, max_length=2000, description="Nguồn của dữ liệu: URI hoặc mô tả")
    license: str = Field(min_length=1, max_length=255, description="Giấy phép của dữ liệu, ví dụ `CC-BY-4.0`")
    source_ref: str | None = Field(
        default=None, max_length=2000, description="Vị trí cụ thể trong nguồn: tệp, dòng, mã tham chiếu"
    )


class RecordOut(BaseModel):
    app_id: str
    record_type: str
    key: str
    data: dict[str, Any]
    schema_version: int = Field(description="Phiên bản schema đã dùng để kiểm `data`")
    source: str
    license: str
    source_ref: str | None
    created_by: str
    created_at: UtcDatetime
    updated_by: str
    updated_at: UtcDatetime

    model_config = ConfigDict(from_attributes=True)
