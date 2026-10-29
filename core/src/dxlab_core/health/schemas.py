# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

from typing import Literal

from pydantic import BaseModel, Field


class HealthOut(BaseModel):
    status: Literal["ok", "degraded"] = Field(description="`ok` khi mọi phụ thuộc bắt buộc hoạt động")
    version: str
    database: Literal["ok", "error"]
