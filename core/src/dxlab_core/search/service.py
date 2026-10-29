# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

import logging
import unicodedata
import uuid
from dataclasses import dataclass, field

from sqlalchemy import Text, cast, func, select
from sqlalchemy.dialects.postgresql import TSQUERY
from sqlalchemy.orm import Session, undefer

from dxlab_core.auth.principal import Principal
from dxlab_core.documents.models import Document
from dxlab_core.documents.schemas import DocumentOut
from dxlab_core.documents.service import visible_to
from dxlab_core.errors import ValidationFailed
from dxlab_core.pagination import PageParams
from dxlab_core.search import text as textutil
from dxlab_core.search.engine import SearchEngine, VectorHit
from dxlab_core.search.embedding import Embedder
from dxlab_core.search.schemas import SearchHitOut, SearchOut, SnippetOut

log = logging.getLogger(__name__)

CANDIDATES = 50
# Trộn hai tín hiệu bằng cộng điểm có trọng số, mỗi điểm trong [0, 1]. Không dùng RRF (chỉ trộn theo hạng) vì khi tiêu đề và
# nội dung khớp trọn câu hỏi, `ts_rank_cd` cách biệt hàng nghìn lần so với khớp lẻ, mà hạng thì mất thông tin đó; còn mô hình
# đa ngữ nhỏ dễ nhiễu với câu hỏi không dấu nên chỉ nên bổ sung, không được lật kết quả toàn văn.
WEIGHT_FTS = 0.7
WEIGHT_VECTOR = 0.3
# Điểm toàn văn = rank / (rank + FTS_HALF): `ts_rank_cd` từ ~0,004 (khớp lẻ một từ) tới vài đơn vị (khớp trọn cụm ở tiêu đề).
FTS_HALF = 0.1
# Vector xa hơn ngưỡng này (khoảng cách cosine) coi như không liên quan.
MAX_VECTOR_DISTANCE = 0.8


@dataclass
class _Candidate:
    fts_rank: float | None = None
    vector_distance: float | None = None
    vector_chunk: int | None = None

    @property
    def score(self) -> float:
        total = 0.0
        if self.fts_rank is not None:
            total += WEIGHT_FTS * self.fts_rank / (self.fts_rank + FTS_HALF)
        if self.vector_distance is not None:
            total += WEIGHT_VECTOR * max(0.0, 1.0 - self.vector_distance / MAX_VECTOR_DISTANCE)
        return total


def _fts_hits(
    session: Session, principal: Principal, query: str, app_id: str | None, kind: str | None
) -> list[tuple[uuid.UUID, float]]:
    """`(id tài liệu, ts_rank_cd)` khớp toàn văn, tốt nhất trước. Thử khớp mọi từ trước; không có gì thì nới thành khớp một trong các từ."""
    folded = func.dxlab_unaccent(query)
    conditions = [visible_to(principal)]
    if app_id:
        conditions.append(Document.app_id == app_id)
    if kind:
        conditions.append(Document.kind == kind)

    def run(tsquery) -> list[tuple[uuid.UUID, float]]:
        rank = func.ts_rank_cd(Document.fts, tsquery).label("rank")
        stmt = (
            select(Document.id, rank)
            .where(*conditions, Document.fts.op("@@")(tsquery))
            .order_by(rank.desc(), Document.created_at.desc(), Document.id)
            .limit(CANDIDATES)
        )
        return [(row.id, float(row.rank)) for row in session.execute(stmt)]

    strict = func.websearch_to_tsquery("simple", folded)
    found = run(strict)
    if found:
        return found
    loose = cast(func.replace(cast(func.plainto_tsquery("simple", folded), Text), "&", "|"), TSQUERY)
    return run(loose)


def _visible_ids(
    session: Session, principal: Principal, ids: list[uuid.UUID], app_id: str | None, kind: str | None
) -> set[uuid.UUID]:
    if not ids:
        return set()
    stmt = select(Document.id).where(Document.id.in_(ids), visible_to(principal))
    if app_id:
        stmt = stmt.where(Document.app_id == app_id)
    if kind:
        stmt = stmt.where(Document.kind == kind)
    return set(session.scalars(stmt))


def _vector_candidates(
    session: Session,
    principal: Principal,
    engine: SearchEngine,
    embedder: Embedder,
    query: str,
    app_id: str | None,
    kind: str | None,
) -> list[tuple[uuid.UUID, int, float]]:
    """`(id tài liệu, số thứ tự đoạn gần nhất, khoảng cách)`, gần nhất trước, chỉ gồm tài liệu người gọi được xem."""
    hits: list[VectorHit] = [hit for hit in engine.hits(embedder, query, CANDIDATES * 3) if hit.distance <= MAX_VECTOR_DISTANCE]
    best: dict[uuid.UUID, VectorHit] = {}
    for hit in hits:  # `hits` đã xếp gần nhất trước: đoạn đầu tiên của mỗi tài liệu là đoạn gần nhất
        best.setdefault(uuid.UUID(hit.document_id), hit)
    visible = _visible_ids(session, principal, list(best), app_id, kind)
    return [(i, hit.chunk_index, hit.distance) for i, hit in best.items() if i in visible][:CANDIDATES]


def search(
    session: Session,
    principal: Principal,
    engine: SearchEngine,
    query: str,
    page: PageParams,
    *,
    app_id: str | None = None,
    kind: str | None = None,
) -> SearchOut:
    query = unicodedata.normalize("NFC", query).strip()
    if not query:
        raise ValidationFailed([{"path": "q", "message": "Từ khóa không được để trống."}])

    candidates: dict[uuid.UUID, _Candidate] = {}
    for document_id, rank in _fts_hits(session, principal, query, app_id, kind):
        candidates.setdefault(document_id, _Candidate()).fts_rank = rank

    mode = "fts"
    embedder = engine.embedder()
    if embedder is not None:
        try:
            engine.sync(session, embedder)
            vector = _vector_candidates(session, principal, engine, embedder, query, app_id, kind)
        except Exception:
            # Chỉ mục hay mô hình lỗi không được làm hỏng tìm kiếm: vẫn trả kết quả toàn văn và báo `mode`.
            log.exception("vector_search_failed")
        else:
            mode = "hybrid"
            for document_id, chunk, distance in vector:
                candidate = candidates.setdefault(document_id, _Candidate())
                candidate.vector_distance = distance
                candidate.vector_chunk = chunk

    ranked = sorted(candidates.items(), key=lambda item: (-item[1].score, str(item[0])))
    window = ranked[page.offset : page.offset + page.limit]
    documents = {
        document.id: document
        for document in session.scalars(
            select(Document).options(undefer(Document.text)).where(Document.id.in_([document_id for document_id, _ in window]))
        )
    }

    terms = textutil.terms(query)
    items: list[SearchHitOut] = []
    for document_id, candidate in window:
        document = documents[document_id]
        matched = [name for name, value in (("fts", candidate.fts_rank), ("vector", candidate.vector_distance)) if value is not None]
        items.append(
            SearchHitOut(
                document=DocumentOut.model_validate(document),
                snippet=_snippet(document.text, terms, candidate),
                score=round(candidate.score, 6),
                matched_by=matched,
            )
        )
    return SearchOut(mode=mode, items=items, total=len(ranked))


def _snippet(text: str | None, terms: list[str], candidate: _Candidate) -> SnippetOut | None:
    if not text:
        return None
    chunks = textutil.chunk_text(text)
    if not chunks:
        return None
    # Ưu tiên đoạn chứa nhiều từ khóa nhất (giải thích vì sao khớp từ khóa); không có từ nào khớp thì lấy đoạn vector gần nhất.
    chunk = textutil.best_chunk(chunks, terms)
    if chunk is None:
        index = candidate.vector_chunk if candidate.vector_chunk is not None and candidate.vector_chunk < len(chunks) else 0
        chunk = chunks[index]
    snippet = textutil.snippet_from(text, chunk, terms)
    return SnippetOut(text=snippet.text, start=snippet.start, end=snippet.end)
