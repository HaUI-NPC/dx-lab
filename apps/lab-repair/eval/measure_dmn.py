# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

"""Đo độ chính xác của routing.dmn và triage.dmn trên bộ phiếu gán nhãn tay (tickets.json).

Chạy từ gốc repo:

    uv run --with "spiffworkflow>=3.2" python apps/lab-repair/eval/measure_dmn.py

Mỗi phiếu chạy qua quy trình thật (`lab-repair.bpmn`): bước `report` nhận các trường của phiếu, hai bước tự động
`route` và `triage` chạy, rồi đọc kết quả ở bước `pending_assessment`. Script chỉ đọc DMN, không sửa gì;
ca sai được in ra để người có thẩm quyền quyết định có sửa luật hay không.
"""

import argparse
import collections
import json
import pathlib
import sys

from SpiffWorkflow.bpmn import BpmnWorkflow
from SpiffWorkflow.spiff.parser.process import SpiffBpmnParser
from SpiffWorkflow.util.task import TaskState

APP = pathlib.Path(__file__).resolve().parent.parent

# Loại người báo phải chọn trên form (report-schema.json) cho mỗi loại thật; dùng để đo "chọn đúng loại".
FORM_CATEGORY = {
    "computer": "computer", "projector": "projector", "network": "network", "printer": "printer",
    "electrical": "electrical", "lighting": "electrical", "air_conditioner": "hvac",
    "lab_equipment": "lab_instrument", "furniture": "other", "plumbing": "other", "other": "other",
}


def load_spec():
    meta = json.loads((APP / "process_model.json").read_text(encoding="utf-8"))
    parser = SpiffBpmnParser()
    parser.add_bpmn_file(str(APP / meta["primary_file_name"]))
    parser.add_dmn_files(sorted(str(p) for p in APP.glob("*.dmn")))
    return parser.get_spec(meta["primary_process_id"])


def predict(spec, ticket):
    wf = BpmnWorkflow(spec)
    wf.do_engine_steps()
    (task,) = wf.get_tasks(state=TaskState.READY, manual=True)
    assert task.task_spec.bpmn_id == "report", task.task_spec.bpmn_id
    task.data.update({k: ticket[k] for k in ("room_id", "asset_id", "asset_category", "impact", "safety_hazard", "urgency")})
    task.run()
    wf.do_engine_steps()
    (task,) = wf.get_tasks(state=TaskState.READY, manual=True)
    assert task.task_spec.bpmn_id == "pending_assessment", task.task_spec.bpmn_id
    d = task.data
    return {"priority": d["priority"], "priority_reason": d["priority_reason"], "tech_unit": d["tech_unit"], "tech_role": d["tech_role"]}


def explain(t, got):
    """Gợi ý nguyên nhân ca sai, chỉ để người đọc dễ xử lý; không dùng để tính điểm."""
    notes = []
    lab = t["label"]
    if got["priority"] != lab["priority"]:
        text = t["issue_description"]
        if lab["priority"] == "P1" and not t["safety_hazard"] and t["impact"] != "whole_room":
            notes.append("mô tả có nguy cơ an toàn nhưng người báo không đánh dấu safety_hazard")
        elif got["priority"] == "P1" and t["impact"] == "whole_room":
            notes.append("người báo chọn ảnh hưởng cả phòng, người gán nhãn đánh giá chỉ ảnh hưởng một phần")
        else:
            notes.append("giá trị urgency/impact người báo chọn dẫn tới mức khác nhãn")
        notes.append(f"urgency={t['urgency']}, impact={t['impact']}, safety_hazard={t['safety_hazard']}: «{text}»")
    if (got["tech_unit"], got["tech_role"]) != (lab["tech_unit"], lab["tech_role"]):
        if FORM_CATEGORY[lab["true_category"]] != t["asset_category"]:
            notes.append(f"người báo chọn loại {t['asset_category']} (loại thật {lab['true_category']})")
        elif t["asset_category"] == "other":
            notes.append(f"loại thật {lab['true_category']} chưa có trong form nên rơi vào dòng còn lại của routing.dmn")
        else:
            notes.append("luật routing.dmn không khớp nhãn")
    return notes


def pct(n, d):
    return f"{n}/{d} = {100 * n / d:.1f}%"


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--tickets", default=str(pathlib.Path(__file__).with_name("tickets.json")))
    args = ap.parse_args()
    tickets = json.loads(pathlib.Path(args.tickets).read_text(encoding="utf-8"))
    spec = load_spec()
    rows = []
    for t in tickets:
        got = predict(spec, t)
        rows.append((t, got))
    n = len(rows)
    ok_prio = sum(g["priority"] == t["label"]["priority"] for t, g in rows)
    ok_unit = sum(g["tech_unit"] == t["label"]["tech_unit"] for t, g in rows)
    ok_role = sum(g["tech_role"] == t["label"]["tech_role"] for t, g in rows)
    ok_route = sum((g["tech_unit"], g["tech_role"]) == (t["label"]["tech_unit"], t["label"]["tech_role"]) for t, g in rows)
    ok_cat = sum(FORM_CATEGORY[t["label"]["true_category"]] == t["asset_category"] for t, _ in rows)

    print(f"Bộ phiếu: {n} phiếu từ {pathlib.Path(args.tickets).name}\n")
    print("| Chỉ số | Đúng / Tổng |")
    print("|---|---|")
    print(f"| Mức ưu tiên (triage.dmn) | {pct(ok_prio, n)} |")
    print(f"| Đơn vị kỹ thuật (routing.dmn: tech_unit) | {pct(ok_unit, n)} |")
    print(f"| Vai trò xử lý (routing.dmn: tech_role) | {pct(ok_role, n)} |")
    print(f"| Định tuyến đúng cả đơn vị và vai trò | {pct(ok_route, n)} |")
    print(f"| Người báo chọn đúng loại trên form (đầu vào, không phải do DMN) | {pct(ok_cat, n)} |")

    print("\nMa trận nhầm lẫn mức ưu tiên (hàng = nhãn tay, cột = DMN):\n")
    levels = ["P1", "P2", "P3"]
    conf = collections.Counter((t["label"]["priority"], g["priority"]) for t, g in rows)
    print("| Nhãn \\ DMN | P1 | P2 | P3 |")
    print("|---|---|---|---|")
    for a in levels:
        print(f"| {a} | " + " | ".join(str(conf[(a, b)]) for b in levels) + " |")

    wrong = [(t, g) for t, g in rows if g["priority"] != t["label"]["priority"] or (g["tech_unit"], g["tech_role"]) != (t["label"]["tech_unit"], t["label"]["tech_role"])]
    print(f"\nCa sai ({len(wrong)} phiếu):\n")
    for t, g in wrong:
        lab = t["label"]
        print(f"- {t['id']} [{t['room_id']}, loại chọn {t['asset_category']}]")
        if g["priority"] != lab["priority"]:
            print(f"  ưu tiên: nhãn {lab['priority']}, DMN {g['priority']} ({g['priority_reason']})")
        if (g["tech_unit"], g["tech_role"]) != (lab["tech_unit"], lab["tech_role"]):
            print(f"  định tuyến: nhãn {lab['tech_unit']} / {lab['tech_role']}, DMN {g['tech_unit']} / {g['tech_role']}")
        for note in explain(t, g):
            print(f"  → {note}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
