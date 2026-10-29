# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

"""Cấu hình: thiếu biến bắt buộc thì dừng và báo đúng tên biến, không lộ giá trị secret."""

from __future__ import annotations

import pytest
from dxlab_portal.config import load_settings


def test_thieu_bien_bat_buoc_thi_dung_va_bao_dung_ten_bien(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for name in (
        "DXLAB_PORTAL_PUBLIC_URL",
        "DXLAB_PORTAL_CLIENT_SECRET",
        "DXLAB_PORTAL_SESSION_SECRET",
    ):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.chdir("/")  # tránh đọc nhầm tệp .env của thư mục làm việc

    with pytest.raises(SystemExit) as stop:
        load_settings()

    message = str(stop.value)
    assert "DXLAB_PORTAL_PUBLIC_URL" in message
    assert "DXLAB_PORTAL_CLIENT_SECRET" in message
    assert "DXLAB_PORTAL_SESSION_SECRET" in message


def test_secret_rong_bi_tu_choi_ma_khong_in_gia_tri(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DXLAB_PORTAL_PUBLIC_URL", "http://localhost:8000")
    monkeypatch.setenv("DXLAB_PORTAL_CLIENT_SECRET", "co-gia-tri")
    monkeypatch.setenv("DXLAB_PORTAL_SESSION_SECRET", "   ")
    with pytest.raises(SystemExit) as stop:
        load_settings()
    assert "DXLAB_PORTAL_SESSION_SECRET" in str(stop.value)
    assert "co-gia-tri" not in str(stop.value)


def test_mac_dinh_issuer_va_kenh_noi_bo(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DXLAB_PORTAL_PUBLIC_URL", "http://localhost:8000/")
    monkeypatch.setenv("DXLAB_PORTAL_CLIENT_SECRET", "a")
    monkeypatch.setenv("DXLAB_PORTAL_SESSION_SECRET", "b")
    monkeypatch.delenv("DXLAB_OIDC_ISSUER", raising=False)
    monkeypatch.delenv("DXLAB_OIDC_INTERNAL_URL", raising=False)
    settings = load_settings()
    assert settings.public_url == "http://localhost:8000"
    assert settings.discovery_url == "http://localhost:8180/realms/dxlab/.well-known/openid-configuration"
    monkeypatch.setenv("DXLAB_OIDC_INTERNAL_URL", "http://keycloak:8080/realms/dxlab")
    assert (
        load_settings().discovery_url == "http://keycloak:8080/realms/dxlab/.well-known/openid-configuration"
    )
