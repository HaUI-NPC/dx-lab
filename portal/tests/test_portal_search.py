# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

"""Tra cứu chuyển tiếp token và giữ trích dẫn của core."""

import httpx
from fastapi.testclient import TestClient

from portal_fakes import FakeCore, FakeKeycloak, login


def test_search_returns_document_citation(client: TestClient, keycloak: FakeKeycloak, core: FakeCore) -> None:
    def search(request: httpx.Request) -> httpx.Response:
        assert request.url.params["q"] == "máy chiếu"
        assert request.headers["authorization"].startswith("Bearer ")
        return httpx.Response(200, json={"mode": "fts", "total": 1, "items": [{"document": {"id": "doc-1", "title": "Hướng dẫn", "source": "DX-Lab", "license": "CC-BY-4.0"}, "snippet": {"text": "Máy chiếu bị hỏng"}}]})

    core.routes[("GET", "/api/search")] = search
    login(client, keycloak)
    response = client.post("/ui/search", json={"query": "máy chiếu"})
    assert response.status_code == 200
    item = response.json()["items"][0]
    assert item["snippet_text"] == "Máy chiếu bị hỏng"
    assert item["provenance"] == "DX-Lab · CC-BY-4.0"
    assert item["href"] == "/api/documents/doc-1/content"
