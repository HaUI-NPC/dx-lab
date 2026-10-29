# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class TaskOut(BaseModel):
    task_id: uuid.UUID
    workflow_id: uuid.UUID
    app_id: str
    step_id: str
    step_name: str
    lane: str
    due_at: datetime | None
    overdue: bool


class TaskForm(BaseModel):
    json_schema: dict[str, Any] = Field(alias="schema")
    uischema: dict[str, Any]


class TaskDetail(TaskOut):
    form: TaskForm
    data: dict[str, Any]
