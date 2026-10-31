# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

"""Tab "Sơ đồ quy trình": sơ đồ Mermaid sinh từ BPMN của phiên bản ``lab-repair`` đang áp dụng.

Portal lấy định nghĩa qua API của core (``/definitions``, rồi tệp ``process_model.json`` và tệp BPMN chính của phiên bản
đang áp dụng), đọc XML bằng thư viện chuẩn và dựng ``flowchart`` theo bước, ``sequenceFlow`` và lane. Không vẽ cứng:
phiên bản mới được áp dụng thì sơ đồ đổi theo.
"""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Any
from urllib.parse import quote

from prefab_ui.components import Card, CardContent, CardHeader, CardTitle, Column, Mermaid, Muted

from dxlab_portal.bff.core_client import CoreResult
from dxlab_portal.pages.context import PageContext
from dxlab_portal.pages.core_error import render_core_error

APP_ID = "lab-repair"
_BPMN = "{http://www.omg.org/spec/BPMN/20100524/MODEL}"
_EVENTS = {"startEvent", "endEvent", "intermediateCatchEvent", "intermediateThrowEvent"}
_GATEWAYS = {"exclusiveGateway", "inclusiveGateway", "parallelGateway", "eventBasedGateway"}


class DiagramError(ValueError):
    """BPMN không dựng được sơ đồ; ``args[0]`` là thông báo tiếng Việt cho người dùng."""


@dataclass(frozen=True)
class Diagram:
    app_id: str
    display_name: str
    version: int
    status: str
    chart: str


def _label(text: str) -> str:
    """Nhãn trong ngoặc kép của Mermaid; ``"`` là ký tự duy nhất phải thay."""
    return text.replace('"', "#quot;").replace("\n", " ")


def _shape(kind: str, node_id: str, text: str) -> str:
    label = _label(text)
    if kind in _EVENTS:
        return f'{node_id}(["{label}"])'
    if kind in _GATEWAYS:
        return f'{node_id}{{"{label}"}}'
    if kind == "businessRuleTask":
        return f'{node_id}[["{label}"]]'
    return f'{node_id}["{label}"]'


def bpmn_to_mermaid(xml_text: str) -> str:
    """Dựng Mermaid ``flowchart TD`` từ BPMN: node theo bước, cạnh theo ``sequenceFlow``, nhóm theo lane."""
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as exc:
        raise DiagramError("Tệp BPMN của phiên bản đang áp dụng không đọc được.") from exc
    process = root.find(f"{_BPMN}process")
    if process is None:
        raise DiagramError("Tệp BPMN không có quy trình nào để vẽ.")

    nodes: dict[str, tuple[str, str]] = {}
    for element in process:
        kind = element.tag.removeprefix(_BPMN)
        node_id = element.get("id")
        if node_id and (kind in _EVENTS or kind in _GATEWAYS or kind.endswith("Task") or kind == "subProcess"):
            nodes[node_id] = (kind, element.get("name") or node_id)
    if not nodes:
        raise DiagramError("Quy trình không có bước nào để vẽ.")

    # Mã bước thành tên node Mermaid; tiền tố tránh trùng từ khóa như ``end``.
    ref = {node_id: f"n_{index}" for index, node_id in enumerate(nodes)}
    lines = ["flowchart TD"]
    placed: set[str] = set()
    for lane_index, lane in enumerate(process.iter(f"{_BPMN}lane")):
        members = [m.text.strip() for m in lane.findall(f"{_BPMN}flowNodeRef") if m.text and m.text.strip() in nodes]
        if not members:
            continue
        lines.append(f'    subgraph lane_{lane_index}["Vai trò: {_label(lane.get("name") or lane.get("id") or "")}"]')
        lines.extend(f"        {_shape(nodes[m][0], ref[m], nodes[m][1])}" for m in members)
        lines.append("    end")
        placed.update(members)
    lines.extend(f"    {_shape(kind, ref[node_id], name)}" for node_id, (kind, name) in nodes.items() if node_id not in placed)

    for flow in process.iter(f"{_BPMN}sequenceFlow"):
        source, target = flow.get("sourceRef"), flow.get("targetRef")
        if source not in nodes or target not in nodes:
            continue
        name = flow.get("name")
        arrow = f'-->|"{_label(name)}"|' if name else "-->"
        lines.append(f"    {ref[source]} {arrow} {ref[target]}")
    return "\n".join(lines) + "\n"


def _file_path(app_id: str, version: int, path: str) -> str:
    return f"/definitions/{quote(app_id)}/versions/{version}/files/{quote(path)}"


async def load(ctx: PageContext) -> Diagram | CoreResult | DiagramError:
    """Lấy BPMN của phiên bản đang áp dụng; lỗi của core trả nguyên để trang hiện đúng thông báo của core."""
    apps = await ctx.core.call("GET", "/definitions", token=ctx.access_token)
    if not apps.ok:
        return apps
    items = apps.json.get("items", []) if isinstance(apps.json, dict) else []
    active = next((a for a in items if isinstance(a, dict) and a.get("app_id") == APP_ID), None)
    if active is None:
        return DiagramError(f"Ứng dụng {APP_ID} chưa có phiên bản nào được áp dụng.")
    version = int(active["version"])
    model = await ctx.core.call("GET", _file_path(APP_ID, version, "process_model.json"), token=ctx.access_token)
    if not model.ok:
        return model
    primary = model.json.get("primary_file_name") if isinstance(model.json, dict) else None
    if not isinstance(primary, str) or not primary:
        return DiagramError("process_model.json của phiên bản đang áp dụng không ghi tệp BPMN chính.")
    bpmn = await ctx.core.call("GET", _file_path(APP_ID, version, primary), token=ctx.access_token)
    if not bpmn.ok:
        return bpmn
    try:
        chart = bpmn_to_mermaid(bpmn.text or "")
    except DiagramError as exc:
        return exc
    return Diagram(APP_ID, str(active.get("display_name") or APP_ID), version, str(active.get("status") or ""), chart)


def render(result: Diagram | CoreResult | DiagramError) -> None:
    if isinstance(result, CoreResult):
        render_core_error("Chưa tải được định nghĩa quy trình", result)
        return
    with Column(gap=4):
        if isinstance(result, DiagramError):
            with Card():
                with CardHeader():
                    CardTitle("Chưa dựng được sơ đồ quy trình")
                with CardContent():
                    Muted(str(result))
            return
        with Card():
            with CardHeader():
                CardTitle(f"{result.display_name} — phiên bản {result.version}")
            with CardContent():
                with Column(gap=3):
                    Muted(
                        "Sơ đồ dựng từ BPMN của phiên bản đang áp dụng: hình chữ nhật là bước người làm, hình chữ nhật "
                        "hai viền là bước tra bảng luật DMN, hình thoi là điều kiện rẽ nhánh, các khung nhóm bước theo vai trò."
                    )
                    Mermaid(result.chart)
