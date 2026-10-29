# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

"""Nạp mô hình embedding (fastembed) từ cache cục bộ. Core không tải mô hình: thiếu thì không có vector (INT-04 lo việc tải)."""

import logging
import threading
import time
from collections.abc import Sequence
from pathlib import Path
from typing import Protocol

log = logging.getLogger(__name__)


class Embedder(Protocol):
    name: str
    dimension: int

    def embed(self, texts: Sequence[str]) -> list[list[float]]: ...


class EmbedderSource(Protocol):
    def get(self) -> Embedder | None: ...


class FastEmbedder:
    def __init__(self, name: str, cache_dir: Path) -> None:
        from fastembed import TextEmbedding

        # `local_files_only`: không bao giờ tải trong lúc phục vụ yêu cầu.
        self._model = TextEmbedding(name, cache_dir=str(cache_dir), local_files_only=True)
        self.name = name
        self.dimension = len(next(iter(self._model.embed(["kiểm tra"]))))

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        return [vector.tolist() for vector in self._model.embed(list(texts))]


class EmbedderProvider:
    """Giữ mô hình đã nạp; chưa nạp được (chưa đặt cache, chưa có tệp) thì thử lại ở lần gọi sau.

    Nhờ vậy mô hình tải về sau khi core đã chạy sẽ được dùng sau tối đa `retry_seconds` mà không cần khởi động lại.
    """

    def __init__(self, name: str, cache_dir: Path | None, retry_seconds: float = 30.0) -> None:
        self._name = name
        self._cache_dir = cache_dir
        self._retry_seconds = retry_seconds
        self._next_attempt = 0.0
        self._embedder: Embedder | None = None
        self._lock = threading.Lock()
        self._reported = False

    def get(self) -> Embedder | None:
        if self._cache_dir is None:
            return None
        with self._lock:
            if self._embedder is None and time.monotonic() >= self._next_attempt:
                try:
                    self._embedder = FastEmbedder(self._name, self._cache_dir)
                    log.info("embedding_model_loaded name=%s", self._name)
                    self._reported = False
                except Exception as exc:  # fastembed ném nhiều loại lỗi khi thiếu tệp hay tệp hỏng
                    # Không thử lại dồn dập: `/api/health` và `/api/search` đều gọi `get()`.
                    self._next_attempt = time.monotonic() + self._retry_seconds
                    if not self._reported:
                        log.warning("embedding_model_unavailable name=%s error=%s", self._name, type(exc).__name__)
                        self._reported = True
            return self._embedder
