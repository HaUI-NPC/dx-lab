# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

import uuid
from datetime import datetime
from typing import Annotated, Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, StringConstraints


class CreateDelegation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    delegate: str = Field(min_length=1, max_length=255, description="Tên đăng nhập người nhận ủy quyền")
    role: str = Field(min_length=1, max_length=64, description="Vai trò được ủy quyền, ví dụ `faculty_head`")
    unit: str | None = Field(default=None, max_length=255,
                             description="Đơn vị giữ vai trò; bỏ trống nếu chỉ giữ vai trò ở một đơn vị")
    number: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=50)] = Field(
        description="Số giấy ủy quyền")
    starts_at: AwareDatetime
    ends_at: AwareDatetime = Field(description="Tối đa 30 ngày sau `starts_at`")
    action: Literal["repair.approve"] = "repair.approve"


class DelegationOut(BaseModel):
    id: uuid.UUID
    number: str
    action: str
    delegator: str
    role: str
    unit: str
    delegate: str
    starts_at: datetime
    ends_at: datetime
    created_at: datetime
    revoked_at: datetime | None
    status: Literal["scheduled", "active", "expired", "revoked"]
