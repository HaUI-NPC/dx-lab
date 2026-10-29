# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class WorkflowOut(BaseModel):
    workflow_id: uuid.UUID
    app_id: str
    version: int
    status: str
    status_name: str
    created_by: str
    created_at: datetime
    updated_at: datetime
    due_at: datetime | None
    revision: int


class HistoryEvent(BaseModel):
    actor: str | None
    action: str
    step_id: str | None = None
    at: datetime
    details: dict[str, Any] = Field(default_factory=dict)


class WorkflowDetail(WorkflowOut):
    data: dict[str, Any]
    history: list[HistoryEvent]
    field_titles: dict[str, str] = Field(
        default_factory=dict,
        description="Tiêu đề hiển thị của các trường dữ liệu lấy từ form của gói; trường không có tiêu đề là dữ liệu nội bộ của engine.",
    )
