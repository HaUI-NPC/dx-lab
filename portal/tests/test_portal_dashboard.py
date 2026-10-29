# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

"""Tab Dashboard: hiển thị số liệu của ``GET /api/stats``, lỗi của core hiện nguyên văn."""

from __future__ import annotations

import httpx
from dxlab_portal.pages.dashboard import format_vnd
from fastapi.testclient import TestClient
from portal_fakes import FakeCore, FakeKeycloak, login, prefab_strings, prefab_text, prefab_wire

STATS = {
    "by_status": [
        {"status": "pending_assessment", "status_name": "Chờ đánh giá", "count": 4},
        {"status": "awaiting_approval", "status_name": "Chờ duyệt", "count": 3},
        {"status": "completed", "status_name": "Hoàn tất", "count": 5},
    ],
    "by_unit": [
        {"unit": "/haui/sict/khmt/lab-a1-305", "count": 7},
        {"unit": "/haui/sict/mmt/lab-a1-601", "count": 5},
    ],
    "overdue": 2,
    "cost": {"approved_total": 15500000, "actual_total": 16000000},
}


def test_dashboard_hien_so_lieu_cua_core(client: TestClient, keycloak: FakeKeycloak, core: FakeCore) -> None:
    core.routes[("GET", "/api/stats")] = lambda request: httpx.Response(200, json=STATS)
    login(client, keycloak)

    html = client.get("/?tab=dashboard").text
    strings = prefab_strings(prefab_wire(html)["view"])
    text = "\n".join(strings)

    assert "Tổng số phiếu" in text and "12" in strings  # 4 + 3 + 5
    assert "Phiếu quá hạn" in text and "2" in strings
    assert "15.500.000\u00a0₫" in strings and "16.000.000\u00a0₫" in strings
    assert "Chờ duyệt" in text and "/haui/sict/mmt/lab-a1-601" in text
    assert core.requests[-1].headers["authorization"].startswith("Bearer ")


def test_core_chua_co_stats_thi_hien_dung_loi_cua_core(client: TestClient, keycloak: FakeKeycloak) -> None:
    login(client, keycloak)  # FakeCore chưa có /api/stats → 404 theo định dạng lỗi chung
    text = prefab_text(client.get("/?tab=dashboard").text)
    assert "Chưa tải được số liệu dashboard" in text
    assert "Không có tài nguyên." in text and "NOT_FOUND" in text and "r-404" in text
    assert "Tổng số phiếu" not in text


def test_core_cam_xem_thong_ke_thi_hien_thong_bao_cua_core(
    client: TestClient, keycloak: FakeKeycloak, core: FakeCore
) -> None:
    core.routes[("GET", "/api/stats")] = lambda request: httpx.Response(
        403,
        json={
            "error": {
                "code": "FORBIDDEN_ROLE",
                "message": "Vai trò của bạn không được xem thống kê.",
                "details": {"layer": 1},
                "request_id": "r-403",
            }
        },
    )
    login(client, keycloak)
    text = prefab_text(client.get("/?tab=dashboard").text)
    assert "Vai trò của bạn không được xem thống kê." in text and "FORBIDDEN_ROLE" in text


def test_dinh_dang_tien_dong_kieu_viet_nam() -> None:
    assert format_vnd(3500000) == "3.500.000\u00a0₫"
    assert format_vnd(0) == "0\u00a0₫"
    assert format_vnd(None) == "—"
