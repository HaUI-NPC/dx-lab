# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

"""Định dạng lỗi chung và mã yêu cầu mà mọi client (portal, CLI, MCP) dựa vào."""

from fastapi import APIRouter, FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field

from dxlab_core.errors import ApiError


class _Body(BaseModel):
    room: str = Field(min_length=3)


def _add_probe_routes(app: FastAPI) -> None:
    router = APIRouter()

    @router.post("/probe/validate")
    def validate(body: _Body) -> dict[str, str]:
        return {"room": body.room}

    @router.get("/probe/forbidden")
    def forbidden() -> None:
        raise ApiError(403, "FORBIDDEN_SCOPE", "Ngoài phạm vi đơn vị của bạn.", {"layer": 2})

    @router.get("/probe/crash")
    def crash() -> None:
        raise RuntimeError("password=secret")

    app.include_router(router, prefix="/api")


def test_api_error_keeps_code_details_and_request_id(app: FastAPI, client: TestClient) -> None:
    _add_probe_routes(app)

    response = client.get("/api/probe/forbidden", headers={"X-Request-Id": "req-123"})

    assert response.status_code == 403
    assert response.json() == {
        "error": {
            "code": "FORBIDDEN_SCOPE",
            "message": "Ngoài phạm vi đơn vị của bạn.",
            "details": {"layer": 2},
            "request_id": "req-123",
        }
    }
    assert response.headers["x-request-id"] == "req-123"


def test_validation_error_lists_field_paths_in_vietnamese(app: FastAPI, client: TestClient) -> None:
    _add_probe_routes(app)

    response = client.post("/api/probe/validate", json={"room": "A"})

    error = response.json()["error"]
    assert response.status_code == 422
    assert error["code"] == "VALIDATION_FAILED"
    assert error["details"]["errors"] == [{"path": "body.room", "message": "Chuỗi quá ngắn."}]


def test_unknown_route_returns_not_found_with_generated_request_id(client: TestClient) -> None:
    response = client.get("/api/khong-co")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"
    assert response.json()["error"]["request_id"] == response.headers["x-request-id"]
    assert len(response.headers["x-request-id"]) == 36


def test_unexpected_error_hides_internals(app: FastAPI, client: TestClient) -> None:
    _add_probe_routes(app)

    response = client.get("/api/probe/crash")

    assert response.status_code == 500
    assert response.json()["error"]["code"] == "INTERNAL"
    assert "secret" not in response.text


def test_unsafe_request_id_is_replaced(client: TestClient) -> None:
    response = client.get("/api/health", headers={"X-Request-Id": "bad id\nwith newline"})

    assert response.headers["x-request-id"] != "bad id\nwith newline"
    assert len(response.headers["x-request-id"]) == 36
