# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

"""Danh sách có phân trang: tham số `limit`/`offset`, phản hồi `{"items": [...], "total": n}`."""

from dataclasses import dataclass
from typing import Annotated

from fastapi import Query
from pydantic import BaseModel


class Page[T](BaseModel):
    items: list[T]
    total: int


@dataclass(frozen=True)
class PageParams:
    limit: int
    offset: int


def page_params(
    limit: Annotated[int, Query(ge=1, le=200, description="Số phần tử tối đa")] = 50,
    offset: Annotated[int, Query(ge=0, description="Bỏ qua bao nhiêu phần tử đầu")] = 0,
) -> PageParams:
    return PageParams(limit=limit, offset=offset)
