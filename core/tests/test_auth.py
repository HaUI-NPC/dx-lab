# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

"""Xác thực JWT, mặc định từ chối, SoD-4 (docs/AUTHZ.md mục 1, 7)."""

import time
from collections.abc import Callable
from typing import Annotated

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import APIRouter, Depends, FastAPI
from fastapi.testclient import TestClient

from dxlab_core.auth.deps import CurrentPrincipal, require_role
from dxlab_core.auth.principal import Principal
from dxlab_core.config import Settings

Headers = Callable[..., dict[str, str]]


def _bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _add_business_routes(app: FastAPI) -> None:
    router = APIRouter()

    @router.get("/probe/business")
    def business(principal: CurrentPrincipal) -> dict[str, str]:
        return {"username": principal.username}

    @router.post("/probe/approve")
    def approve(principal: Annotated[Principal, Depends(require_role("faculty_head", "school_head"))]) -> dict[str, str]:
        return {"username": principal.username}

    app.include_router(router, prefix="/api")


def test_me_returns_roles_and_units_from_groups(client: TestClient, headers_for: Headers) -> None:
    headers = headers_for("tl.giang", ["/haui/sict/khmt/lab-a1-305/lab_manager"], name="Hoàng Thu Giang")

    response = client.get("/api/me", headers=headers)

    assert response.status_code == 200
    assert response.json() == {
        "username": "tl.giang",
        "name": "Hoàng Thu Giang",
        "roles": [{"role": "lab_manager", "unit": "/haui/sict/khmt/lab-a1-305"}],
        "units": ["/haui/sict/khmt/lab-a1-305"],
    }


@pytest.mark.parametrize(
    "headers",
    [{}, {"Authorization": "Basic dXNlcjpwYXNz"}, {"Authorization": "Bearer "}, {"Authorization": "Bearer abc.def.ghi"}],
    ids=["thieu-token", "sai-kieu", "rong", "khong-phai-jwt"],
)
def test_missing_or_malformed_token_is_401(client: TestClient, headers: dict[str, str]) -> None:
    response = client.get("/api/me", headers=headers)

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHENTICATED"


@pytest.mark.parametrize(
    ("claims", "message"),
    [
        ({"exp": int(time.time()) - 120}, "Phiên đăng nhập đã hết hạn, đăng nhập lại."),
        ({"aud": "account"}, "Token không hợp lệ."),
        ({"iss": "http://evil.example/realms/dxlab"}, "Token không hợp lệ."),
    ],
    ids=["het-han", "sai-audience", "sai-issuer"],
)
def test_token_with_wrong_claims_is_401(
    client: TestClient, headers_for: Headers, claims: dict[str, object], message: str
) -> None:
    response = client.get("/api/me", headers=headers_for("sv.an", **claims))

    assert response.status_code == 401
    assert response.json()["error"]["message"] == message


def test_token_signed_by_other_key_is_401(client: TestClient, settings: Settings) -> None:
    other = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    now = int(time.time())
    forged = jwt.encode(
        {"iss": settings.oidc_issuer, "aud": settings.oidc_audience, "preferred_username": "gd.nam",
         "groups": ["/haui/ban-giam-doc/president"], "iat": now, "exp": now + 300},
        other,
        algorithm="RS256",
    )

    response = client.get("/api/me", headers=_bearer(forged))

    assert response.status_code == 401


def test_unsigned_token_is_401(client: TestClient, settings: Settings) -> None:
    now = int(time.time())
    unsigned = jwt.encode(
        {"iss": settings.oidc_issuer, "aud": settings.oidc_audience, "preferred_username": "gd.nam",
         "iat": now, "exp": now + 300},
        key=None,
        algorithm="none",
    )

    response = client.get("/api/me", headers=_bearer(unsigned))

    assert response.status_code == 401


def test_system_admin_sees_me_but_blocked_from_business_actions(
    app: FastAPI, client: TestClient, headers_for: Headers
) -> None:
    _add_business_routes(app)
    admin = headers_for("admin.dx", ["/haui/tt-cntt/system_admin"])

    assert client.get("/api/me", headers=admin).status_code == 200
    response = client.get("/api/probe/business", headers=admin)

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN_ROLE"
    assert response.json()["error"]["details"] == {"layer": 1, "rule": "SoD-4"}


def test_require_role_allows_holder_and_rejects_others(
    app: FastAPI, client: TestClient, headers_for: Headers
) -> None:
    _add_business_routes(app)

    allowed = client.post("/api/probe/approve", headers=headers_for("tk.hai", ["/haui/sict/khmt/faculty_head"]))
    denied = client.post("/api/probe/approve", headers=headers_for("sv.an"))

    assert allowed.status_code == 200
    assert denied.status_code == 403
    assert denied.json()["error"]["details"] == {"layer": 1, "required_roles": ["faculty_head", "school_head"]}
