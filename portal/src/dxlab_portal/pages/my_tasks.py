# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

"""Tab "Việc của tôi"."""

from __future__ import annotations

from dxlab_portal.pages.placeholder import render_pending


def render() -> None:
    render_pending("Việc của tôi", "Hộp việc theo vai trò: các bước đang chờ bạn xử lý")
