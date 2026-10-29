# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

import math
import os
import zlib
from collections.abc import Sequence
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from dxlab_core.config import Settings
from dxlab_core.search import text as textutil
from dxlab_core.search.embedding import Embedder
from dxlab_core.search.engine import SearchEngine
from sample_data import (
    ADMIN_DX,
    APP_ID,
    CSVC_LAN,
    QUOTE_TEXT,
    SOP_NETWORK,
    SOP_PC,
    SOP_PROJECTOR,
    SV_AN,
    HeadersFactory,
)

pytestmark = pytest.mark.usefixtures("clean_data")

# Đồng nghĩa giả: "dead laptop boot" cho vector giống "không tính lên" dù không chung từ nào với văn bản.
_SYNONYMS = {"dead": "khong", "laptop": "tinh", "boot": "len", "offline": "mang", "cable": "day"}


class FakeEmbedder:
    """Mô hình giả có tính chất vừa đủ để thử đường vector thật của zvec: túi từ băm vào 64 chiều, có bảng đồng nghĩa."""

    dimension = 64

    def __init__(self, name: str = "mo-hinh-gia-v1") -> None:
        self.name = name
        self.calls = 0

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        self.calls += 1
        vectors = []
        for text in texts:
            vector = [0.01] * self.dimension
            for word in textutil.terms(text):
                vector[zlib.crc32(_SYNONYMS.get(word, word).encode()) % self.dimension] += 1.0
            norm = math.sqrt(sum(value * value for value in vector))
            vectors.append([value / norm for value in vector])
        return vectors


class FixedProvider:
    def __init__(self, embedder: Embedder | None) -> None:
        self.embedder = embedder

    def get(self) -> Embedder | None:
        return self.embedder


class BrokenEmbedder(FakeEmbedder):
    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        raise RuntimeError("mô hình hỏng")


def upload(client: TestClient, headers: dict[str, str], text: str, *, title: str, kind: str = "sop", filename: str = "tai-lieu.md"):
    response = client.post(
        "/api/documents",
        data={"app_id": APP_ID, "kind": kind, "title": title, "source": f"Nguồn của {title}", "license": "CC-BY-4.0"},
        files={"file": (filename, text.encode(), "text/markdown")},
        headers=headers,
    )
    assert response.status_code == 201, response.text
    return response.json()


@pytest.fixture
def sops(client: TestClient, headers_for: HeadersFactory) -> dict[str, dict]:
    csvc = headers_for(*CSVC_LAN)
    return {
        "pc": upload(client, csvc, SOP_PC, title="SOP-IT-01: Máy tính không lên nguồn"),
        "projector": upload(client, csvc, SOP_PROJECTOR, title="SOP-IT-02: Máy chiếu không nhận tín hiệu"),
        "network": upload(client, csvc, SOP_NETWORK, title="SOP-IT-04: Mất kết nối mạng LAN"),
    }


def search(client: TestClient, headers: dict[str, str], q: str, **params: object) -> dict:
    response = client.get("/api/search", params={"q": q, **params}, headers=headers)
    assert response.status_code == 200, response.text
    return response.json()


@pytest.fixture
def hybrid(app: FastAPI, settings: Settings) -> FakeEmbedder:
    embedder = FakeEmbedder()
    app.state.search = SearchEngine(settings, provider=FixedProvider(embedder))
    return embedder


@pytest.fixture
def fts_only(app: FastAPI, settings: Settings) -> None:
    app.state.search = SearchEngine(settings, provider=FixedProvider(None))


def test_no_model_falls_back_to_fts_and_finds_pc_sop(
    app: FastAPI, settings: Settings, client: TestClient, sops: dict, headers_for: HeadersFactory
) -> None:
    # Không đặt DXLAB_MODEL_CACHE_DIR: không có mô hình (đặt tường minh để không phụ thuộc môi trường chạy test).
    app.state.search = SearchEngine(settings.model_copy(update={"model_cache_dir": None}))
    body = search(client, headers_for(*SV_AN), "may tinh khong len")
    assert body["mode"] == "fts"
    top = body["items"][0]
    assert top["document"]["id"] == sops["pc"]["id"]
    assert top["matched_by"] == ["fts"]
    assert "may tinh khong len" in top["snippet"]["text"]
    assert top["document"]["source"] == "Nguồn của SOP-IT-01: Máy tính không lên nguồn"
    assert top["document"]["license"] == "CC-BY-4.0"
    # Máy chiếu và mạng không chứa đủ cả bốn từ nên không lọt vào nhóm khớp chặt.
    assert [item["document"]["id"] for item in body["items"]] == [sops["pc"]["id"]]
    assert body["total"] == 1


def test_model_directory_without_model_files_is_fts_only(
    app: FastAPI, settings: Settings, client: TestClient, sops: dict, headers_for: HeadersFactory, tmp_path: Path
) -> None:
    empty = tmp_path / "models"
    empty.mkdir()
    app.state.search = SearchEngine(settings.model_copy(update={"model_cache_dir": empty}))
    body = search(client, headers_for(*SV_AN), "may tinh khong len")
    assert body["mode"] == "fts"
    assert body["items"][0]["document"]["id"] == sops["pc"]["id"]


@pytest.mark.parametrize("query", ["máy tính không lên", "MAY TINH KHONG LEN", "Máy  Tính, không lên!", "bat may khong len"])
def test_fts_ignores_case_diacritics_and_punctuation(
    client: TestClient, fts_only: None, sops: dict, headers_for: HeadersFactory, query: str
) -> None:
    body = search(client, headers_for(*SV_AN), query)
    assert body["items"][0]["document"]["id"] == sops["pc"]["id"]


def test_fts_relaxes_to_any_word_when_no_document_has_all(
    client: TestClient, fts_only: None, sops: dict, headers_for: HeadersFactory
) -> None:
    body = search(client, headers_for(*SV_AN), "mất mạng lan nhưng switch không cắm")
    assert body["items"][0]["document"]["id"] == sops["network"]["id"]


def test_fts_matches_title_and_no_match_returns_empty(
    client: TestClient, fts_only: None, sops: dict, headers_for: HeadersFactory
) -> None:
    sv = headers_for(*SV_AN)
    assert search(client, sv, "chiếu tín hiệu")["items"][0]["document"]["id"] == sops["projector"]["id"]
    empty = search(client, sv, "zzzkhongco")
    assert empty["items"] == [] and empty["total"] == 0


def test_hybrid_ranks_keyword_match_first_and_reports_both_signals(
    client: TestClient, hybrid: FakeEmbedder, sops: dict, headers_for: HeadersFactory
) -> None:
    body = search(client, headers_for(*SV_AN), "may tinh khong len")
    assert body["mode"] == "hybrid"
    top = body["items"][0]
    assert top["document"]["id"] == sops["pc"]["id"]
    assert top["matched_by"] == ["fts", "vector"]
    assert top["snippet"]["text"] in SOP_PC
    assert top["snippet"]["start"] == SOP_PC.index(top["snippet"]["text"])


def test_hybrid_finds_by_meaning_when_no_word_matches(
    client: TestClient, hybrid: FakeEmbedder, sops: dict, headers_for: HeadersFactory
) -> None:
    body = search(client, headers_for(*SV_AN), "dead laptop boot")
    assert body["mode"] == "hybrid"
    top = body["items"][0]
    assert top["document"]["id"] == sops["pc"]["id"]
    assert top["matched_by"] == ["vector"]
    assert "không lên" in top["snippet"]["text"] or "khong len" in top["snippet"]["text"]


def test_documents_uploaded_after_first_search_are_indexed_lazily(
    client: TestClient, hybrid: FakeEmbedder, sops: dict, headers_for: HeadersFactory
) -> None:
    sv = headers_for(*SV_AN)
    assert search(client, sv, "offline cable")["mode"] == "hybrid"  # lần tìm đầu dựng chỉ mục cho ba SOP
    late = upload(
        client,
        headers_for(*CSVC_LAN),
        "# Cắm lại\n\nXử lý bằng cách kiểm tra dây mạng và cổng switch.\n",
        title="Khôi phục đường truyền",
    )
    hits = {item["document"]["id"]: item for item in search(client, sv, "offline cable")["items"]}
    assert hits[late["id"]]["matched_by"] == ["vector"]


def test_changing_the_model_rebuilds_the_index(
    app: FastAPI, settings: Settings, client: TestClient, sops: dict, headers_for: HeadersFactory
) -> None:
    sv = headers_for(*SV_AN)
    app.state.search = SearchEngine(settings, provider=FixedProvider(FakeEmbedder("mo-hinh-v1")))
    assert search(client, sv, "dead laptop boot")["items"][0]["document"]["id"] == sops["pc"]["id"]
    v2 = FakeEmbedder("mo-hinh-v2")
    app.state.search = SearchEngine(settings, provider=FixedProvider(v2))
    body = search(client, sv, "dead laptop boot")
    assert body["mode"] == "hybrid"
    assert body["items"][0]["document"]["id"] == sops["pc"]["id"]
    assert v2.calls > 1  # đã lập lại vector cho cả ba tài liệu bằng mô hình mới


def test_broken_model_degrades_to_fts_instead_of_failing(
    app: FastAPI, settings: Settings, client: TestClient, sops: dict, headers_for: HeadersFactory
) -> None:
    app.state.search = SearchEngine(settings, provider=FixedProvider(BrokenEmbedder()))
    body = search(client, headers_for(*SV_AN), "may tinh khong len")
    assert body["mode"] == "fts"
    assert body["items"][0]["document"]["id"] == sops["pc"]["id"]


@pytest.mark.parametrize("mode", ["fts", "hybrid"])
def test_results_are_filtered_by_what_the_caller_may_see(
    request: pytest.FixtureRequest, client: TestClient, sops: dict, headers_for: HeadersFactory, mode: str
) -> None:
    request.getfixturevalue("fts_only" if mode == "fts" else "hybrid")
    quote = upload(client, headers_for(*CSVC_LAN), QUOTE_TEXT, title="Báo giá bộ nguồn", kind="quote", filename="bao-gia.md")
    query = "bộ nguồn 1.850.000" if mode == "fts" else "dead laptop boot nguon bao gia"

    officer = search(client, headers_for(*CSVC_LAN), query)
    assert quote["id"] in [item["document"]["id"] for item in officer["items"]]

    reporter = search(client, headers_for(*SV_AN), query)
    assert quote["id"] not in [item["document"]["id"] for item in reporter["items"]]
    assert reporter["total"] == len(reporter["items"])


def test_filters_and_pagination(client: TestClient, fts_only: None, sops: dict, headers_for: HeadersFactory) -> None:
    sv = headers_for(*SV_AN)
    both = search(client, sv, "không kiểm tra")  # chung từ khóa với nhiều SOP: phải có > 1 kết quả
    assert both["total"] >= 2
    first = search(client, sv, "không kiểm tra", limit=1)
    second = search(client, sv, "không kiểm tra", limit=1, offset=1)
    assert first["total"] == second["total"] == both["total"]
    assert first["items"][0]["document"]["id"] == both["items"][0]["document"]["id"]
    assert second["items"][0]["document"]["id"] == both["items"][1]["document"]["id"]
    assert search(client, sv, "không kiểm tra", app_id="app-khac")["items"] == []
    assert search(client, sv, "không kiểm tra", kind="quote")["items"] == []
    assert search(client, sv, "không kiểm tra", kind="sop", app_id=APP_ID)["total"] == both["total"]


def test_search_requires_login_blocks_system_admin_and_rejects_blank_query(client: TestClient, headers_for: HeadersFactory) -> None:
    assert client.get("/api/search", params={"q": "x"}).status_code == 401
    assert client.get("/api/search", params={"q": "x"}, headers=headers_for(*ADMIN_DX)).status_code == 403
    blank = client.get("/api/search", params={"q": "   "}, headers=headers_for(*SV_AN))
    assert blank.status_code == 422
    assert blank.json()["error"]["details"]["errors"] == [{"path": "q", "message": "Từ khóa không được để trống."}]
    assert client.get("/api/search", headers=headers_for(*SV_AN)).status_code == 422


def test_fold_keeps_length_so_offsets_line_up() -> None:
    text = "Đường điện Ỷ máy tính KHÔNG lên İ"
    folded = textutil.fold(text)
    assert len(folded) == len(text)
    assert folded.startswith("duong dien y may tinh khong len")


def test_chunks_cover_paragraphs_with_exact_offsets() -> None:
    paragraphs = [f"Đoạn số {n}: " + "từ " * 60 for n in range(5)]
    text = "\n\n".join(paragraphs)
    chunks = textutil.chunk_text(text, max_chars=500)
    assert len(chunks) >= 3
    for chunk in chunks:
        assert text[chunk.start : chunk.end] == chunk.text
        assert 0 < len(chunk.text) <= 500
    assert [chunk.index for chunk in chunks] == list(range(len(chunks)))
    covered = "".join(chunk.text for chunk in chunks).replace("\n", "").replace(" ", "")
    assert covered == text.replace("\n", "").replace(" ", "")


def test_chunks_skip_html_comments_such_as_spdx_headers() -> None:
    text = "<!--\nSPDX-FileCopyrightText: 2026 DX-Lab contributors\n-->\n\n# Tiêu đề\n\nNội dung chính.\n"
    chunks = textutil.chunk_text(text)
    assert [chunk.text for chunk in chunks] == ["# Tiêu đề\n\nNội dung chính."]
    assert text[chunks[0].start : chunks[0].end] == chunks[0].text


def test_snippet_centers_on_the_match_and_keeps_offsets() -> None:
    text = ("Lời mở đầu rất dài. " * 20) + "Kiểm tra cáp HDMI cắm chặt. " + ("Phần kết dài dòng. " * 20)
    chunk = textutil.chunk_text(text, max_chars=2000)[0]
    snippet = textutil.snippet_from(text, chunk, ["hdmi"])
    assert "HDMI" in snippet.text
    assert len(snippet.text) <= textutil.SNIPPET_CHARS
    assert text[snippet.start : snippet.end] == snippet.text


@pytest.mark.skipif(
    not os.environ.get("DXLAB_TEST_MODEL_CACHE_DIR"),
    reason="Cần mô hình fastembed đã tải sẵn: đặt DXLAB_TEST_MODEL_CACHE_DIR trỏ tới thư mục cache (INT-04 / scripts/download-models.sh)",
)
def test_real_minilm_model_hybrid(
    app: FastAPI, settings: Settings, client: TestClient, sops: dict, headers_for: HeadersFactory
) -> None:
    app.state.search = SearchEngine(
        settings.model_copy(update={"model_cache_dir": Path(os.environ["DXLAB_TEST_MODEL_CACHE_DIR"])})
    )
    sv = headers_for(*SV_AN)
    body = search(client, sv, "may tinh khong len")
    assert body["mode"] == "hybrid"
    assert body["items"][0]["document"]["id"] == sops["pc"]["id"]

    # Câu hỏi có dấu, không trùng từ nào với tài liệu: mô hình thật tìm ra theo nghĩa.
    by_meaning = search(client, sv, "PC không bật được")
    assert by_meaning["items"][0]["document"]["id"] == sops["pc"]["id"]
    assert "vector" in by_meaning["items"][0]["matched_by"]


def test_health_reports_missing_model_without_degrading(client: TestClient, fts_only: None) -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    body = response.json()
    assert (body["status"], body["search_index"], body["embedding_model"]) == ("ok", "ok", "missing")


def test_health_with_model_checks_the_index_directory(
    app: FastAPI, settings: Settings, client: TestClient, hybrid: FakeEmbedder, tmp_path: Path
) -> None:
    ok = client.get("/api/health").json()
    assert (ok["status"], ok["search_index"], ok["embedding_model"]) == ("ok", "ok", "ok")

    blocker = tmp_path / "la-mot-tep"
    blocker.write_text("không phải thư mục")
    broken = settings.model_copy(update={"search_index_dir": blocker})
    app.state.search = SearchEngine(broken, provider=FixedProvider(FakeEmbedder()))
    response = client.get("/api/health")
    assert response.status_code == 503
    body = response.json()
    assert (body["status"], body["database"], body["search_index"]) == ("degraded", "ok", "error")
