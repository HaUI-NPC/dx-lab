# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

"""Kiểm tra sức khỏe các thành phần của DX-Lab từ phía máy chủ portal (không cần đăng nhập).

Chỉ báo điều quan sát được: không đoán trạng thái của thành phần mà portal không có đường tới.
- Keycloak: ``DXLAB_OIDC_INTERNAL_URL`` (hoặc issuer) + ``/.well-known/openid-configuration``;
  ``issuer`` trả về phải khớp cấu hình.
- APISIX: ``DXLAB_API_URL/health`` có phản hồi HTTP là cổng API còn sống.
- Core và PostgreSQL: nội dung JSON của ``/api/health`` (``database``), chỉ mục tìm kiếm và mô hình từ
  ``search_index`` và ``embedding_model`` khi core có các trường này.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Any

from dxlab_portal.bff.core_client import CoreClient
from dxlab_portal.bff.oidc import OidcClient
from dxlab_portal.bff.probe import ProbeResult
from dxlab_portal.config import Settings

# Giờ Việt Nam không có giờ mùa hè (CONTRIBUTING: portal hiển thị giờ Việt Nam).
VIETNAM_TZ = timezone(timedelta(hours=7))
LABELS = {
    "ok": "Hoạt động",
    "warn": "Hoạt động hạn chế",
    "down": "Lỗi",
    "unknown": "Chưa có thông tin",
}
# Biến thể màu của Badge/Dot trong Prefab.
VARIANTS = {"ok": "success", "warn": "warning", "down": "destructive", "unknown": "secondary"}


def _service(key: str, name: str, state: str, detail: str, elapsed_ms: int | None = None) -> dict[str, Any]:
    return {
        "key": key,
        "name": name,
        "state": state,
        "label": LABELS[state],
        "variant": VARIANTS[state],
        "latency": f"{elapsed_ms} ms" if elapsed_ms is not None else "—",
        "detail": detail,
    }


def _keycloak(result: ProbeResult, settings: Settings) -> dict[str, Any]:
    name = "Keycloak (đăng nhập)"
    if result.response is None:
        return _service("keycloak", name, "down", result.error or "Không kết nối được", result.elapsed_ms)
    if result.response.status_code != 200:
        return _service("keycloak", name, "down", f"HTTP {result.response.status_code}", result.elapsed_ms)
    body = result.json
    issuer = str(body.get("issuer", "")).rstrip("/") if isinstance(body, dict) else ""
    if issuer != settings.oidc_issuer:
        return _service("keycloak", name, "down", "Issuer khác DXLAB_OIDC_ISSUER", result.elapsed_ms)
    return _service("keycloak", name, "ok", "Realm dxlab phản hồi", result.elapsed_ms)


def _optional_component(
    key: str, name: str, health: dict[str, Any], field: str, states: dict[str, tuple[str, str]]
) -> dict[str, Any]:
    value = health.get(field)
    if value is None:
        return _service(key, name, "unknown", "Core chưa báo thông tin này")
    state, detail = states.get(str(value), ("down", f"Core báo: {value}"))
    return _service(key, name, state, detail)


def _gateway_and_core(result: ProbeResult) -> list[dict[str, Any]]:
    gateway = "APISIX (cổng API)"
    if result.response is None:
        reason = result.error or "Không kết nối được"
        blocked = "Chưa kiểm được vì cổng API không phản hồi"
        return [
            _service("apisix", gateway, "down", reason, result.elapsed_ms),
            _service("core", "Core API", "unknown", blocked),
            _service("postgres", "PostgreSQL", "unknown", blocked),
            _service("search_index", "Chỉ mục tìm kiếm", "unknown", blocked),
            _service("embedding_model", "Mô hình embedding", "unknown", blocked),
        ]
    apisix = _service("apisix", gateway, "ok", "Cổng API có phản hồi", result.elapsed_ms)
    health = result.json
    if not isinstance(health, dict) or "database" not in health:
        detail = f"Cổng API trả HTTP {result.response.status_code}, không phải trả lời của core"
        unknown = "Chưa kiểm được vì core không phản hồi"
        return [
            apisix,
            _service("core", "Core API", "down", detail, result.elapsed_ms),
            _service("postgres", "PostgreSQL", "unknown", unknown),
            _service("search_index", "Chỉ mục tìm kiếm", "unknown", unknown),
            _service("embedding_model", "Mô hình embedding", "unknown", unknown),
        ]
    version = health.get("version")
    core = _service(
        "core", "Core API", "ok", f"Phiên bản {version}" if version else "Core phản hồi", result.elapsed_ms
    )
    database = (
        _service("postgres", "PostgreSQL", "ok", "Core kết nối được database")
        if health["database"] == "ok"
        else _service("postgres", "PostgreSQL", "down", "Core không kết nối được database")
    )
    search = _optional_component(
        "search_index",
        "Chỉ mục tìm kiếm",
        health,
        "search_index",
        {"ok": ("ok", "Chỉ mục sẵn sàng"), "error": ("down", "Chỉ mục lỗi")},
    )
    model = _optional_component(
        "embedding_model",
        "Mô hình embedding",
        health,
        "embedding_model",
        {"ok": ("ok", "Mô hình sẵn sàng"), "missing": ("warn", "Chỉ tìm theo từ khóa (chưa có mô hình)")},
    )
    return [apisix, core, database, search, model]


async def check_all(settings: Settings, oidc: OidcClient, core: CoreClient) -> dict[str, Any]:
    """Thăm dò song song; trả ``{"checked_at", "overall", "services": [...]}`` để hiện trên trang."""
    keycloak, health = await asyncio.gather(oidc.probe(), core.probe("/health"))
    services = [
        _service("portal", "Portal", "ok", "Portal đang phục vụ yêu cầu này"),
        _keycloak(keycloak, settings),
        *_gateway_and_core(health),
    ]
    failed = [s["name"] for s in services if s["state"] == "down"]
    now = datetime.now(VIETNAM_TZ).strftime("%d/%m/%Y %H:%M:%S")
    return {
        "checked_at": now,
        "overall": f"Có dịch vụ lỗi: {', '.join(failed)}" if failed else "Các dịch vụ đã kiểm đều hoạt động",
        "has_error": bool(failed),
        "services": services,
    }
