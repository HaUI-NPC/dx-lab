# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

"""Tab "Tra cứu"."""

from __future__ import annotations

from dxlab_portal.pages.placeholder import render_pending


def render() -> None:
    render_pending("Tra cứu", "Tìm kiếm phiếu, tài sản và hướng dẫn sửa chữa")
