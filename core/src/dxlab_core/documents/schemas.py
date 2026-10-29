# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

import uuid
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from dxlab_core.utc import UtcDatetime

DocumentKind = Literal["sop", "quote", "other"]


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    app_id: str
    kind: DocumentKind
    title: str
    filename: str = Field(description="Tên tệp gốc do người tải lên đặt; không dùng làm đường dẫn lưu")
    content_type: str
    size: int = Field(description="Số byte")
    sha256: str = Field(description="Checksum SHA-256 của nội dung, 64 ký tự hex")
    workflow_id: uuid.UUID | None
    source: str
    license: str
    source_ref: str | None
    created_by: str
    created_at: UtcDatetime
