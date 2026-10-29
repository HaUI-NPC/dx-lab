# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

"""Trang "Trạng thái hệ thống": mỗi dịch vụ xanh/đỏ đúng với thực tế, không cần đăng nhập."""

from __future__ import annotations

import httpx
from portal_fakes import FakeKeycloak, connection_refused, make_client, prefab_text

HEALTH_OK = {"status": "ok", "version": "0.1.0", "database": "ok"}


def health(body: dict[str, object], status: int = 200):  # type: ignore[no-untyped-def]
    return lambda request: httpx.Response(status, json=body)


def states(client) -> dict[str, dict[str, str]]:  # type: ignore[no-untyped-def]
    response = client.get("/ui/status")
    assert response.status_code == 200  # không cần đăng nhập
    return {s["key"]: s for s in response.json()["services"]}


def test_moi_dich_vu_hoat_dong_thi_xanh_va_co_thoi_gian_phan_hoi() -> None:
    client = make_client(FakeKeycloak().handler, health(HEALTH_OK))
    result = states(client)
    assert {k: v["state"] for k, v in result.items() if k != "search_index" and k != "embedding_model"} == {
        "portal": "ok",
        "keycloak": "ok",
        "apisix": "ok",
        "core": "ok",
        "postgres": "ok",
    }
    assert result["keycloak"]["latency"].endswith(" ms") and result["apisix"]["latency"].endswith(" ms")
    overall = client.get("/ui/status").json()
    assert overall["has_error"] is False


def test_tat_keycloak_thi_chi_keycloak_do() -> None:
    client = make_client(connection_refused, health(HEALTH_OK))
    result = states(client)
    assert result["keycloak"]["state"] == "down" and result["keycloak"]["label"] == "Lỗi"
    assert result["keycloak"]["detail"] == "Không kết nối được"
    assert {k: result[k]["state"] for k in ("portal", "apisix", "core", "postgres")} == {
        "portal": "ok",
        "apisix": "ok",
        "core": "ok",
        "postgres": "ok",
    }
    overall = client.get("/ui/status").json()
    assert overall["has_error"] is True and "Keycloak" in overall["overall"]


def test_keycloak_tra_issuer_khac_cau_hinh_thi_do() -> None:
    client = make_client(FakeKeycloak(issuer="http://khac.example/realms/dxlab").handler, health(HEALTH_OK))
    assert states(client)["keycloak"]["state"] == "down"


def test_core_bao_database_loi_thi_chi_postgres_do() -> None:
    degraded = {"status": "degraded", "version": "0.1.0", "database": "error"}
    client = make_client(FakeKeycloak().handler, health(degraded, 503))
    result = states(client)
    assert result["core"]["state"] == "ok" and result["apisix"]["state"] == "ok"
    assert result["postgres"]["state"] == "down"


def test_cong_api_khong_phan_hoi_thi_apisix_do_va_cac_dich_vu_sau_no_chua_ro() -> None:
    result = states(make_client(FakeKeycloak().handler, connection_refused))
    assert result["apisix"]["state"] == "down"
    for key in ("core", "postgres", "search_index", "embedding_model"):
        assert result[key]["state"] == "unknown" and result[key]["label"] == "Chưa có thông tin"
    assert result["keycloak"]["state"] == "ok"


def test_cong_api_song_nhung_core_chet_thi_core_do_apisix_van_xanh() -> None:
    bad_gateway = lambda request: httpx.Response(502, text="<html>502 Bad Gateway</html>")  # noqa: E731
    result = states(make_client(FakeKeycloak().handler, bad_gateway))
    assert result["apisix"]["state"] == "ok"
    assert result["core"]["state"] == "down" and "HTTP 502" in result["core"]["detail"]
    assert result["postgres"]["state"] == "unknown"


def test_chi_muc_va_mo_hinh_chua_co_thi_chua_co_thong_tin_khong_doan() -> None:
    result = states(make_client(FakeKeycloak().handler, health(HEALTH_OK)))
    assert result["search_index"]["state"] == "unknown"
    assert result["embedding_model"]["state"] == "unknown"


def test_chi_muc_va_mo_hinh_theo_truong_core_bao() -> None:
    cases = [
        ({"search_index": "ok", "embedding_model": "ok"}, ("ok", "ok")),
        ({"search_index": "ok", "embedding_model": "missing"}, ("ok", "warn")),
        ({"search_index": "error", "embedding_model": "ok"}, ("down", "ok")),
    ]
    for extra, (search, model) in cases:
        result = states(make_client(FakeKeycloak().handler, health({**HEALTH_OK, **extra})))
        assert (result["search_index"]["state"], result["embedding_model"]["state"]) == (search, model)
    result = states(make_client(FakeKeycloak().handler, health({**HEALTH_OK, "embedding_model": "missing"})))
    assert result["embedding_model"]["detail"] == "Chỉ tìm theo từ khóa (chưa có mô hình)"


def test_trang_status_khong_can_dang_nhap_va_nap_trang_thai_tu_ui_status() -> None:
    client = make_client(FakeKeycloak().handler, health(HEALTH_OK))
    response = client.get("/status")
    assert response.status_code == 200
    text = prefab_text(response.text)
    assert "Trạng thái hệ thống" in text and "Kiểm tra lại" in text
    assert "/ui/status" in text
