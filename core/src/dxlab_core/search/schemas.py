# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

from typing import Literal

from pydantic import BaseModel, Field

from dxlab_core.documents.schemas import DocumentOut


class SnippetOut(BaseModel):
    text: str = Field(description="Đoạn văn bản khớp nhất trong tài liệu")
    start: int = Field(description="Vị trí ký tự bắt đầu của đoạn trong `text` của tài liệu")
    end: int = Field(description="Vị trí ký tự kết thúc (không gồm)")


class SearchHitOut(BaseModel):
    document: DocumentOut = Field(description="Tài liệu nguồn, kèm nguồn gốc và giấy phép để trích dẫn")
    snippet: SnippetOut | None = Field(description="Trích đoạn; trống nếu tài liệu không có văn bản (ví dụ PDF)")
    score: float = Field(description="Điểm trộn toàn văn (70%) và vector (30%), trong khoảng 0–1: càng cao càng khớp")
    matched_by: list[Literal["fts", "vector"]] = Field(description="Tìm thấy bằng toàn văn, vector, hay cả hai")


class SearchOut(BaseModel):
    mode: Literal["hybrid", "fts"] = Field(
        description="`hybrid` khi có mô hình embedding; `fts` khi thiếu mô hình hoặc mô hình lỗi, chỉ dùng toàn văn"
    )
    items: list[SearchHitOut]
    total: int = Field(description="Tổng số kết quả (trước khi phân trang)")
