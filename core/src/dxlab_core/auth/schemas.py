# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

from pydantic import BaseModel


class RoleOut(BaseModel):
    role: str
    unit: str


class MeOut(BaseModel):
    username: str
    name: str
    roles: list[RoleOut]
    units: list[str]
