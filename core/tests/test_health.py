# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path

from fastapi.testclient import TestClient

from dxlab_core.app import create_app
from dxlab_core.config import load_settings


def test_health_ok_when_database_reachable(client: TestClient) -> None:
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["database"] == "ok"


def test_health_503_when_database_unreachable(tmp_path: Path) -> None:
    settings = load_settings(
        database_url="postgresql+psycopg://dxlab:dxlab@127.0.0.1:1/dxlab",
        documents_dir=tmp_path,
        search_index_dir=tmp_path,
    )
    with TestClient(create_app(settings)) as client:
        response = client.get("/api/health")

    assert response.status_code == 503
    assert response.json()["database"] == "error"


def test_openapi_served_under_api_prefix(client: TestClient) -> None:
    response = client.get("/api/openapi.json")

    assert response.status_code == 200
    assert "/api/health" in response.json()["paths"]
