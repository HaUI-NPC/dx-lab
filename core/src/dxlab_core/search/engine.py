# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

"""Chỉ mục vector zvec của các đoạn văn bản tài liệu.

Mỗi đoạn là một bản ghi zvec `<document_id>:<số thứ tự đoạn>` (vector cosine + `document_id`). Chỉ mục là dữ liệu dẫn xuất:
mất thì dựng lại từ `documents.text`. Tài liệu nào chưa được đưa vào chỉ mục bằng mô hình hiện tại
(`documents.embedded_model` khác tên mô hình) sẽ được đưa vào ở lần tìm kiếm kế tiếp.
"""

import json
import logging
import os
import shutil
import threading
from dataclasses import dataclass
from typing import Literal

import zvec
from sqlalchemy import Engine, select, text, update
from sqlalchemy.orm import Session, undefer

from dxlab_core.config import Settings
from dxlab_core.documents.models import Document
from dxlab_core.search.embedding import Embedder, EmbedderProvider, EmbedderSource
from dxlab_core.search.text import chunk_text

log = logging.getLogger(__name__)

COLLECTION = "chunks"
EMBED_BATCH = 32


@dataclass(frozen=True)
class VectorHit:
    document_id: str
    chunk_index: int
    distance: float  # khoảng cách cosine (1 − độ tương đồng): càng nhỏ càng gần


class SearchEngine:
    def __init__(self, settings: Settings, provider: EmbedderSource | None = None) -> None:
        self._dir = settings.search_index_dir
        self._provider = provider or EmbedderProvider(settings.embedding_model, settings.model_cache_dir)
        self._collection: zvec.Collection | None = None
        self._collection_model: str | None = None
        self._lock = threading.Lock()

    def embedder(self) -> Embedder | None:
        return self._provider.get()

    def health(self, engine: Engine) -> tuple[Literal["ok", "error"], Literal["ok", "missing"]]:
        """`(search_index, embedding_model)` cho `/api/health`.

        `search_index` lỗi khi toàn văn không dùng được (database hay hàm `dxlab_unaccent` hỏng) hoặc, khi có mô hình,
        thư mục chỉ mục vector không ghi được. Thiếu mô hình không phải lỗi: tìm kiếm chỉ dùng toàn văn.
        """
        embedding: Literal["ok", "missing"] = "ok" if self.embedder() is not None else "missing"
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT to_tsvector('simple', dxlab_unaccent('kiểm tra'))"))
            if embedding == "ok":
                self._dir.mkdir(parents=True, exist_ok=True)
                if not os.access(self._dir, os.W_OK):
                    raise PermissionError(str(self._dir))
        except Exception as exc:
            log.warning("health_search_index_error type=%s", type(exc).__name__)
            return "error", embedding
        return "ok", embedding

    def sync(self, session: Session, embedder: Embedder) -> None:
        """Đưa vào chỉ mục mọi tài liệu có văn bản mà chưa được lập vector bằng mô hình hiện tại."""
        with self._lock:
            collection = self._open(session, embedder)
            while True:
                stale = session.scalars(
                    select(Document)
                    .options(undefer(Document.text))
                    .where(Document.text.is_not(None), Document.embedded_model.is_distinct_from(embedder.name))
                    .order_by(Document.created_at)
                    .limit(EMBED_BATCH)
                ).all()
                if not stale:
                    return
                for document in stale:
                    self._index_document(collection, embedder, document)
                    document.embedded_model = embedder.name
                session.flush()
                collection.flush()

    def hits(self, embedder: Embedder, query: str, topk: int) -> list[VectorHit]:
        collection = self._collection
        if collection is None or self._collection_model != embedder.name:
            return []
        (vector,) = embedder.embed([query])
        found = collection.query(zvec.Query(field_name="embedding", vector=vector), topk=topk)
        result: list[VectorHit] = []
        for doc in found:
            document_id, _, chunk = doc.id.partition(":")
            result.append(VectorHit(document_id, int(chunk), float(doc.score)))
        return result

    def _index_document(self, collection: zvec.Collection, embedder: Embedder, document: Document) -> None:
        chunks = chunk_text(document.text or "")
        if not chunks:
            return
        vectors = embedder.embed([chunk.text for chunk in chunks])
        docs = [
            zvec.Doc(
                id=f"{document.id}:{chunk.index}",
                vectors={"embedding": vector},
                fields={"document_id": str(document.id)},
            )
            for chunk, vector in zip(chunks, vectors, strict=True)
        ]
        for status in collection.upsert(docs):
            if not status.ok():
                raise RuntimeError(f"zvec upsert thất bại: {status}")

    def _open(self, session: Session, embedder: Embedder) -> zvec.Collection:
        if self._collection is not None and self._collection_model == embedder.name:
            return self._collection
        path = self._dir / COLLECTION
        meta = self._dir / "meta.json"
        recorded = json.loads(meta.read_text()) if meta.exists() else None
        if path.exists() and recorded == {"model": embedder.name, "dimension": embedder.dimension}:
            collection = zvec.open(str(path))
        else:
            # Chưa có chỉ mục, hoặc dựng bằng mô hình khác (số chiều khác): dựng lại từ đầu.
            if path.exists():
                shutil.rmtree(path)
            self._dir.mkdir(parents=True, exist_ok=True)
            schema = zvec.CollectionSchema(
                name=COLLECTION,
                fields=[zvec.FieldSchema("document_id", zvec.DataType.STRING)],
                vectors=zvec.VectorSchema(
                    "embedding",
                    zvec.DataType.VECTOR_FP32,
                    embedder.dimension,
                    index_param=zvec.FlatIndexParam(metric_type=zvec.MetricType.COSINE),
                ),
            )
            collection = zvec.create_and_open(str(path), schema)
            meta.write_text(json.dumps({"model": embedder.name, "dimension": embedder.dimension}))
            session.execute(update(Document).values(embedded_model=None))
            log.info("search_index_created model=%s", embedder.name)
        self._collection = collection
        self._collection_model = embedder.name
        return collection
