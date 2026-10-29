# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

"""Fixture dùng chung cho test portal."""

from __future__ import annotations

import httpx
import pytest
from dxlab_portal.app import create_app
from fastapi.testclient import TestClient
from portal_fakes import PUBLIC_URL, FakeCore, FakeKeycloak, make_settings


@pytest.fixture
def keycloak() -> FakeKeycloak:
    return FakeKeycloak()


@pytest.fixture
def core() -> FakeCore:
    return FakeCore()


@pytest.fixture
def client(keycloak: FakeKeycloak, core: FakeCore) -> TestClient:
    app = create_app(
        make_settings(),
        oidc_transport=httpx.MockTransport(keycloak.handler),
        core_transport=httpx.MockTransport(core.handler),
    )
    return TestClient(app, base_url=PUBLIC_URL, follow_redirects=False)
