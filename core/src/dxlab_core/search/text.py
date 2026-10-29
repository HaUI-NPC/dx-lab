# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

"""Xử lý văn bản thuần (không đụng database): bỏ dấu, chia đoạn để đánh vector, chọn trích đoạn."""

import re
import unicodedata
from dataclasses import dataclass

CHUNK_CHARS = 500
SNIPPET_CHARS = 300

_PARAGRAPH = re.compile(r"\S(?:.|\n)*?(?=\n[ \t]*\n|\Z)")
_WORD = re.compile(r"\w+")
_HTML_COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)


@dataclass(frozen=True)
class Chunk:
    index: int
    start: int
    end: int
    text: str


@dataclass(frozen=True)
class Snippet:
    text: str
    start: int
    end: int


def fold(text: str) -> str:
    """Chữ thường, bỏ dấu tiếng Việt, **cùng độ dài** với `text` (mỗi ký tự thành đúng một ký tự) để vị trí khớp nhau.

    Đồng bộ với `dxlab_unaccent` + `simple` bên PostgreSQL: "Máy tính KHÔNG lên" → "may tinh khong len".
    """
    out: list[str] = []
    for char in text:
        if char in "đĐ":
            out.append("d")
            continue
        decomposed = unicodedata.normalize("NFD", char)
        base = (decomposed[0] if decomposed else char).lower()
        out.append(base if len(base) == 1 else char)
    return "".join(out)


def terms(query: str) -> list[str]:
    """Các từ khóa của câu hỏi sau khi bỏ dấu, không trùng, giữ thứ tự."""
    seen: dict[str, None] = {}
    for word in _WORD.findall(fold(unicodedata.normalize("NFC", query))):
        seen.setdefault(word)
    return list(seen)


def chunk_text(text: str, max_chars: int = CHUNK_CHARS) -> list[Chunk]:
    """Chia văn bản thành các đoạn cỡ `max_chars` ở ranh giới đoạn văn (dòng trống); đoạn dài hơn thì cắt ở khoảng trắng.

    Mỗi `Chunk` giữ vị trí trong văn bản gốc, nên `text[chunk.start:chunk.end] == chunk.text`. Chú thích HTML
    (`<!-- … -->`, ví dụ khối bản quyền SPDX đầu tệp Markdown) không được đưa vào đoạn nào.
    """
    spans: list[tuple[int, int]] = []
    # Thay chú thích bằng khoảng trắng cùng độ dài để vị trí vẫn khớp với văn bản gốc.
    visible = _HTML_COMMENT.sub(lambda match: " " * len(match.group()), text)
    for match in _PARAGRAPH.finditer(visible):
        start, end = match.start(), match.start() + len(match.group().rstrip())
        while end - start > max_chars:
            cut = visible.rfind(" ", start + max_chars // 2, start + max_chars)
            cut = cut if cut != -1 else start + max_chars
            spans.append((start, cut))
            start = cut
            while start < end and visible[start].isspace():
                start += 1
        if start < end:
            spans.append((start, end))

    merged: list[tuple[int, int]] = []
    for start, end in spans:
        if merged and end - merged[-1][0] <= max_chars:
            merged[-1] = (merged[-1][0], end)
        else:
            merged.append((start, end))
    return [Chunk(index, start, end, text[start:end]) for index, (start, end) in enumerate(merged)]


def match_count(chunk: Chunk, query_terms: list[str]) -> int:
    words = set(_WORD.findall(fold(chunk.text)))
    return sum(1 for term in query_terms if term in words)


def snippet_from(text: str, chunk: Chunk, query_terms: list[str], max_chars: int = SNIPPET_CHARS) -> Snippet:
    """Trích đoạn ngắn từ `chunk`, canh quanh chỗ khớp từ khóa đầu tiên nếu đoạn dài hơn `max_chars`."""
    if chunk.end - chunk.start <= max_chars:
        return Snippet(chunk.text, chunk.start, chunk.end)
    folded = fold(chunk.text)
    hits = [match.start() for term in query_terms if (match := re.search(rf"\b{re.escape(term)}\b", folded))]
    anchor = min(hits) if hits else 0
    begin = max(0, anchor - max_chars // 3)
    finish = min(len(chunk.text), begin + max_chars)
    begin = max(0, finish - max_chars)
    # Lùi / tiến tới khoảng trắng gần nhất để không cắt giữa từ.
    if begin > 0:
        space = chunk.text.find(" ", begin, begin + 30)
        begin = space + 1 if space != -1 else begin
    if finish < len(chunk.text):
        space = chunk.text.rfind(" ", finish - 30, finish)
        finish = space if space != -1 else finish
    return Snippet(chunk.text[begin:finish], chunk.start + begin, chunk.start + finish)


def best_chunk(chunks: list[Chunk], query_terms: list[str]) -> Chunk | None:
    """Đoạn chứa nhiều từ khóa nhất (cùng số thì đoạn đứng trước); không có từ nào khớp thì `None`."""
    best: Chunk | None = None
    best_count = 0
    for chunk in chunks:
        count = match_count(chunk, query_terms)
        if count > best_count:
            best, best_count = chunk, count
    return best
