# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

"""Fixture chung cho test core.

Test chạy trên PostgreSQL thật. `DXLAB_TEST_DATABASE_URL` trỏ tới một máy chủ PostgreSQL mà tài khoản có quyền
`CREATE DATABASE`; mỗi lần chạy tạo một database tạm, nâng migration, xóa khi xong. Ví dụ chạy cục bộ:

    docker run -d --name dxlab-testdb -p 127.0.0.1:55432:5432 \\
        -e POSTGRES_USER=dxlab -e POSTGRES_PASSWORD=dxlab postgres:17.11-alpine
    DXLAB_TEST_DATABASE_URL=postgresql+psycopg://dxlab:dxlab@127.0.0.1:55432/postgres uv run --all-packages pytest core
"""

import os
import time
import uuid
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

from dxlab_core.app import create_app
from dxlab_core.auth.tokens import TokenVerifier
from dxlab_core.config import Settings, load_settings
from dxlab_core.db.migrate import upgrade

TokenFactory = Callable[..., str]
HeadersFactory = Callable[..., dict[str, str]]


@pytest.fixture(scope="session")
def database_url() -> Iterator[str]:
    server_url = os.environ.get("DXLAB_TEST_DATABASE_URL")
    if not server_url:
        pytest.fail("Thiếu DXLAB_TEST_DATABASE_URL: test core cần PostgreSQL thật (xem core/tests/conftest.py).")
    name = f"dxlab_test_{uuid.uuid4().hex[:12]}"
    admin = create_engine(server_url, isolation_level="AUTOCOMMIT")
    with admin.connect() as conn:
        conn.execute(text(f'CREATE DATABASE "{name}"'))
    url = make_url(server_url).set(database=name).render_as_string(hide_password=False)
    try:
        upgrade(url)
        yield url
    finally:
        with admin.connect() as conn:
            conn.execute(text(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)'))
        admin.dispose()


@pytest.fixture
def settings(database_url: str, tmp_path: Path) -> Settings:
    return load_settings(
        database_url=database_url,
        documents_dir=tmp_path / "documents",
        search_index_dir=tmp_path / "search",
    )


@pytest.fixture(scope="session")
def signing_key() -> rsa.RSAPrivateKey:
    """Khóa ký token cho test, đóng vai khóa realm của Keycloak."""
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


@pytest.fixture
def app(settings: Settings, signing_key: rsa.RSAPrivateKey) -> Iterator[FastAPI]:
    application = create_app(settings)
    public_key = signing_key.public_key()
    application.state.token_verifier = TokenVerifier(settings, key_resolver=lambda _token: public_key)
    yield application
    application.state.engine.dispose()


@pytest.fixture
def token_for(settings: Settings, signing_key: rsa.RSAPrivateKey) -> TokenFactory:
    """`token_for("tk.hai", ["/haui/sict/khmt/faculty_head"])` → access token như Keycloak cấp cho tài khoản đó.

    Tham số khóa thêm ghi đè claim (ví dụ `exp=...`, `aud=...`, `iss=...`).
    """

    def make(username: str, groups: list[str] | None = None, **claims: Any) -> str:
        now = int(time.time())
        payload = {
            "iss": settings.oidc_issuer,
            "aud": [settings.oidc_audience, "account"],
            "sub": str(uuid.uuid5(uuid.NAMESPACE_DNS, username)),
            "preferred_username": username,
            "name": username,
            "groups": groups or [],
            "iat": now,
            "exp": now + 300,
            **claims,
        }
        return jwt.encode(payload, signing_key, algorithm="RS256", headers={"kid": "test"})

    return make


@pytest.fixture
def headers_for(token_for: TokenFactory) -> HeadersFactory:
    """`headers_for("tk.hai", [...])` → header `Authorization: Bearer <token>` cho tài khoản đó."""

    def make(username: str, groups: list[str] | None = None, **claims: Any) -> dict[str, str]:
        return {"Authorization": f"Bearer {token_for(username, groups, **claims)}"}

    return make


@pytest.fixture
def client(app: FastAPI) -> Iterator[TestClient]:
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client
