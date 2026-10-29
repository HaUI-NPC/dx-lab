# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

"""Tab "Báo hỏng"."""

from __future__ import annotations

from dxlab_portal.pages.placeholder import render_pending


def render() -> None:
    render_pending("Báo hỏng", "Gửi phiếu báo hỏng thiết bị phòng lab")
