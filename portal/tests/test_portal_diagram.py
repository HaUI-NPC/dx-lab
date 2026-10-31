# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

"""Tab "Sơ đồ quy trình": Mermaid sinh từ BPMN của phiên bản đang áp dụng, không vẽ cứng."""

from __future__ import annotations


import httpx
import pytest
from dxlab_portal.pages.diagram import DiagramError, bpmn_to_mermaid
from fastapi.testclient import TestClient
from portal_fakes import REPO_ROOT, FakeCore, FakeKeycloak, login, prefab_strings, prefab_text, prefab_wire

MINI = """<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" id="d">
  <bpmn:process id="p">
    <bpmn:laneSet id="ls">
      <bpmn:lane id="l1" name="reporter"><bpmn:flowNodeRef>start</bpmn:flowNodeRef><bpmn:flowNodeRef>report</bpmn:flowNodeRef></bpmn:lane>
    </bpmn:laneSet>
    <bpmn:startEvent id="start" name="Có sự cố" />
    <bpmn:userTask id="report" name="Báo &quot;hỏng&quot;" />
    <bpmn:businessRuleTask id="rule" name="Tra luật" />
    <bpmn:exclusiveGateway id="gw" name="Cần duyệt?" />
    <bpmn:endEvent id="end" />
    <bpmn:sequenceFlow id="f1" sourceRef="start" targetRef="report" />
    <bpmn:sequenceFlow id="f2" sourceRef="report" targetRef="rule" />
    <bpmn:sequenceFlow id="f3" sourceRef="rule" targetRef="gw" />
    <bpmn:sequenceFlow id="f4" name="Có" sourceRef="gw" targetRef="end" />
    <bpmn:sequenceFlow id="f5" sourceRef="gw" targetRef="missing" />
  </bpmn:process>
</bpmn:definitions>
"""

LAB_REPAIR_BPMN = (REPO_ROOT / "apps" / "lab-repair" / "lab-repair.bpmn").read_text(encoding="utf-8")


def test_node_theo_buoc_canh_theo_sequence_flow_va_nhom_theo_lane() -> None:
    chart = bpmn_to_mermaid(MINI)

    lines = chart.splitlines()
    assert lines[0] == "flowchart TD"
    assert '    subgraph lane_0["Vai trò: reporter"]' in lines
    assert '        n_0(["Có sự cố"])' in lines  # sự kiện bắt đầu nằm trong lane
    assert '        n_1["Báo #quot;hỏng#quot;"]' in lines  # nháy kép trong tên không phá cú pháp
    assert '    n_2[["Tra luật"]]' in lines  # bước bảng luật ở ngoài lane
    assert '    n_3{"Cần duyệt?"}' in lines
    assert '    n_4(["end"])' in lines  # thiếu tên thì dùng mã bước, mã `end` không đụng từ khóa Mermaid
    assert "    n_0 --> n_1" in lines and "    n_3 -->|\"Có\"| n_4" in lines
    assert not any("missing" in line or "n_5" in line for line in lines)  # cạnh tới nút không có bị bỏ


def test_bpmn_hong_hoac_khong_co_quy_trinh_bao_loi_tieng_viet() -> None:
    with pytest.raises(DiagramError, match="không đọc được"):
        bpmn_to_mermaid("<bpmn:definitions")
    with pytest.raises(DiagramError, match="không có quy trình"):
        bpmn_to_mermaid('<definitions xmlns="http://www.omg.org/spec/BPMN/20100524/MODEL"/>')


def test_sinh_tu_bpmn_that_cua_lab_repair() -> None:
    chart = bpmn_to_mermaid(LAB_REPAIR_BPMN)

    for step in ("Báo hỏng", "Chờ duyệt", "Đang sửa", "Chờ nghiệm thu", "Đã chuyển Ban CSVC"):
        assert f'"{step}"' in chart
    assert 'subgraph lane_4["Vai trò: approver"]' in chart
    assert '|"Không sửa được"|' in chart and '|"Vượt: duyệt lại"|' in chart


def serve_definition(core: FakeCore, *, version: int = 3, bpmn: str = MINI, primary: str = "lab-repair.bpmn") -> None:
    base = f"/api/definitions/lab-repair/versions/{version}/files"
    core.routes[("GET", "/api/definitions")] = lambda request: httpx.Response(
        200,
        json={"items": [{"app_id": "lab-repair", "display_name": "Báo hỏng thiết bị", "version": version, "status": "active"}], "total": 1},
    )
    core.routes[("GET", f"{base}/process_model.json")] = lambda request: httpx.Response(
        200, json={"primary_file_name": primary}
    )
    core.routes[("GET", f"{base}/{primary}")] = lambda request: httpx.Response(
        200, content=bpmn.encode(), headers={"content-type": "application/xml"}
    )


def mermaid_charts(html: str) -> list[str]:
    def walk(node: object) -> list[str]:
        if isinstance(node, dict):
            found = [node["chart"]] if node.get("type") == "Mermaid" else []
            return found + [c for v in node.values() for c in walk(v)]
        if isinstance(node, list):
            return [c for v in node for c in walk(v)]
        return []

    return walk(prefab_wire(html)["view"])


def test_tab_hien_so_do_cua_phien_ban_dang_ap_dung(client: TestClient, keycloak: FakeKeycloak, core: FakeCore) -> None:
    serve_definition(core, version=3)
    login(client, keycloak)

    html = client.get("/?tab=diagram").text

    assert "Báo hỏng thiết bị — phiên bản 3" in "\n".join(prefab_strings(prefab_wire(html)["view"]))
    assert mermaid_charts(html) == [bpmn_to_mermaid(MINI)]
    paths = [r.url.path for r in core.requests]
    assert "/api/definitions/lab-repair/versions/3/files/lab-repair.bpmn" in paths
    assert core.requests[-1].headers["authorization"].startswith("Bearer ")


def test_doi_phien_ban_thi_so_do_doi_theo(client: TestClient, keycloak: FakeKeycloak, core: FakeCore) -> None:
    other = MINI.replace("Tra luật", "Tra bảng thẩm quyền")
    serve_definition(core, version=4, bpmn=other, primary="main.bpmn")
    login(client, keycloak)

    charts = mermaid_charts(client.get("/?tab=diagram").text)

    assert len(charts) == 1 and "Tra bảng thẩm quyền" in charts[0] and "Tra luật" not in charts[0]


def test_core_loi_thi_hien_nguyen_van_loi_cua_core(client: TestClient, keycloak: FakeKeycloak, core: FakeCore) -> None:
    core.routes[("GET", "/api/definitions")] = lambda request: httpx.Response(
        403,
        json={"error": {"code": "FORBIDDEN_ROLE", "message": "Bạn không được xem định nghĩa.", "details": {}, "request_id": "r-9"}},
    )
    login(client, keycloak)

    text = prefab_text(client.get("/?tab=diagram").text)

    assert "Chưa tải được định nghĩa quy trình" in text and "Bạn không được xem định nghĩa." in text
    assert mermaid_charts(client.get("/?tab=diagram").text) == []


def test_chua_co_phien_ban_ap_dung_thi_noi_ro(client: TestClient, keycloak: FakeKeycloak, core: FakeCore) -> None:
    core.routes[("GET", "/api/definitions")] = lambda request: httpx.Response(200, json={"items": [], "total": 0})
    login(client, keycloak)

    text = prefab_text(client.get("/?tab=diagram").text)

    assert "Chưa dựng được sơ đồ quy trình" in text and "chưa có phiên bản nào được áp dụng" in text
