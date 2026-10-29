# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class FileOut(BaseModel):
    path: str
    sha256: str
    size: int


class VersionOut(BaseModel):
    app_id: str
    version: int
    status: str = Field(description="`pending_approval`, `active` hoặc `superseded`")
    display_name: str
    process_id: str
    checksum: str
    published_by: str
    published_at: datetime
    activated_by: str | None
    activated_at: datetime | None
    files: list[FileOut]


class AppOut(BaseModel):
    app_id: str
    display_name: str
    version: int
    status: str


class StartFormOut(BaseModel):
    app_id: str
    version: int
    step_id: str
    step_name: str
    schema_: dict[str, Any] = Field(alias="schema", serialization_alias="schema")
    uischema: dict[str, Any]

    model_config = {"populate_by_name": True}
