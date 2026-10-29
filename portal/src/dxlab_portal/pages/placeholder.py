# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

"""Nội dung tab chưa có ở bản này: nói rõ, không dựng dữ liệu giả."""

from __future__ import annotations

from prefab_ui.components import Card, CardContent, CardDescription, CardHeader, CardTitle, Muted


def render_pending(title: str, description: str) -> None:
    with Card():
        with CardHeader():
            CardTitle(title)
            CardDescription(description)
        with CardContent():
            Muted("Nội dung tab này chưa có trong bản hiện tại; sẽ được bổ sung ở các bản sau.")
