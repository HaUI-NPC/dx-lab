# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

"""Tab "Trạng thái hệ thống"."""

from __future__ import annotations

from dxlab_portal.pages.placeholder import render_pending


def render() -> None:
    render_pending("Trạng thái hệ thống", "Tình trạng các thành phần của DX-Lab")
