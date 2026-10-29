# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

"""Ngữ cảnh của một lần render trang: người dùng, token và máy khách core."""

from __future__ import annotations

from dataclasses import dataclass

from dxlab_portal.bff.core_client import CoreClient
from dxlab_portal.pages.user import UserView


@dataclass
class PageContext:
    user: UserView
    access_token: str
    core: CoreClient
    tab: str
    task_id: str = ""
    workflow_id: str = ""
