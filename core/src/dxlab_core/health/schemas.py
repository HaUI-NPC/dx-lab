# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

from typing import Literal

from pydantic import BaseModel, Field


class HealthOut(BaseModel):
    status: Literal["ok", "degraded"] = Field(description="`ok` khi mọi phụ thuộc bắt buộc hoạt động")
    version: str
    database: Literal["ok", "error"]
    search_index: Literal["ok", "error"] = Field(description="Toàn văn (và thư mục chỉ mục vector nếu có mô hình) dùng được")
    embedding_model: Literal["ok", "missing"] = Field(
        description="`missing`: không có mô hình embedding, `/api/search` chỉ dùng toàn văn; không làm `status` thành `degraded`"
    )
