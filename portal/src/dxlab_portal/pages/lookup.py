# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

"""Tra cứu tài liệu qua API tìm kiếm của core."""

from __future__ import annotations

from prefab_ui.actions import Fetch, SetState, ShowToast
from prefab_ui.components import Button, Card, CardContent, CardHeader, CardTitle, Column, ForEach, Input, Link, Muted, Text
from prefab_ui.components.control_flow import If
from prefab_ui.rx import RESULT


def state(_: object) -> dict[str, object]:
    return {"search_query": "", "search_result": {"items": [], "total": 0, "mode": ""}}


def render() -> None:
    search = Fetch.post(
        "/ui/search", body={"query": "{{ search_query }}"},
        on_success=SetState("search_result", RESULT),
        on_error=ShowToast("Không tìm kiếm được: {{ $error }}", variant="error"),
    )
    with Card():
        with CardHeader():
            CardTitle("Tra cứu hướng dẫn sửa chữa")
        with CardContent():
            with Column(gap=4):
                Input(name="search_query", placeholder="Nhập từ khóa tìm kiếm")
                Button("Tìm kiếm", on_click=search)
                with If("search_result.mode"):
                    Muted("Tìm thấy {{ search_result.total }} kết quả · Chế độ: {{ search_result.mode }}")
                with ForEach("search_result.items") as item:
                    with Card():
                        with CardContent():
                            with Column(gap=2):
                                Link(item.document.title, href=item.href)
                                Text(item.snippet_text)
                                Muted(item.provenance)
