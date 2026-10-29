# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

"""Đường lấy khóa thật: core tải JWKS từ URL nội bộ của Keycloak nhưng so `iss` với URL công khai."""

import json
import threading
import time
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from jwt.algorithms import RSAAlgorithm

from dxlab_core.auth.tokens import TokenVerifier, Unauthenticated
from dxlab_core.config import load_settings
from dxlab_core.errors import ApiError

PUBLIC_ISSUER = "http://localhost:8180/realms/dxlab"


@pytest.fixture
def realm_key() -> rsa.RSAPrivateKey:
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


@pytest.fixture
def jwks_server(realm_key: rsa.RSAPrivateKey) -> Iterator[str]:
    jwk = json.loads(RSAAlgorithm.to_jwk(realm_key.public_key()))
    body = json.dumps({"keys": [{**jwk, "kid": "realm-key", "use": "sig", "alg": "RS256"}]}).encode()

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            found = self.path == "/realms/dxlab/protocol/openid-connect/certs"
            self.send_response(200 if found else 404)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(body if found else b"{}")

        def log_message(self, *_args: object) -> None:
            pass

    server = HTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{server.server_port}/realms/dxlab"
    server.shutdown()


def _verifier(tmp_path: Path, internal_url: str) -> TokenVerifier:
    settings = load_settings(
        database_url="postgresql+psycopg://unused@127.0.0.1:1/unused",
        documents_dir=tmp_path,
        search_index_dir=tmp_path,
        oidc_issuer=PUBLIC_ISSUER,
        oidc_internal_url=internal_url,
    )
    return TokenVerifier(settings)


def _token(key: rsa.RSAPrivateKey, kid: str) -> str:
    now = int(time.time())
    claims = {"iss": PUBLIC_ISSUER, "aud": "dxlab-core", "preferred_username": "tl.giang", "iat": now, "exp": now + 60}
    return jwt.encode(claims, key, algorithm="RS256", headers={"kid": kid})


def test_key_fetched_from_internal_url_and_public_issuer_accepted(
    tmp_path: Path, jwks_server: str, realm_key: rsa.RSAPrivateKey
) -> None:
    claims = _verifier(tmp_path, jwks_server).verify(_token(realm_key, "realm-key"))

    assert claims["preferred_username"] == "tl.giang"


def test_unknown_key_id_rejected(tmp_path: Path, jwks_server: str, realm_key: rsa.RSAPrivateKey) -> None:
    with pytest.raises(Unauthenticated):
        _verifier(tmp_path, jwks_server).verify(_token(realm_key, "other-key"))


def test_keycloak_unreachable_is_server_error_not_401(tmp_path: Path, realm_key: rsa.RSAPrivateKey) -> None:
    with pytest.raises(ApiError) as excinfo:
        _verifier(tmp_path, "http://127.0.0.1:1/realms/dxlab").verify(_token(realm_key, "realm-key"))

    assert excinfo.value.status == 500
