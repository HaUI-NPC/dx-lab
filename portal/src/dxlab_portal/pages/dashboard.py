# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

"""Tab "Dashboard"."""

from __future__ import annotations

from dxlab_portal.pages.placeholder import render_pending


def render() -> None:
    render_pending("Dashboard", "Số liệu tổng hợp theo trạng thái, đơn vị, quá hạn")
