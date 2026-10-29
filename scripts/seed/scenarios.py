# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

"""Phiếu mẫu của `lab-repair` ở nhiều trạng thái, theo các kịch bản 1, 2, 3, 12 và một ca hoàn tất (docs/AUTHZ.md mục 12).

Dữ liệu từng bước đúng trường của `apps/lab-repair/<bước>-schema.json`; người làm từng bước là tài khoản demo
đúng lane (docs/AUTHZ.md mục 11). Id bước = trạng thái của phiếu (docs/ARCHITECTURE.md mục 7).
Mọi tên, mã, số điện thoại là giả định cho demo, không phải người thật.
"""

from dataclasses import dataclass, field
from datetime import date
from typing import Any

TITLE_PREFIX = "[Mẫu] "

REPORTERS: dict[str, dict[str, str]] = {
    "sv.an": {
        "reporter_name": "Nguyễn Văn An",
        "reporter_id": "SV2024001",
        "reporter_phone": "0912000001",
        "reporter_email": "sv.an@dx-lab.example",
    },
    "gv.binh": {
        "reporter_name": "Trần Thị Bình",
        "reporter_id": "GV0305",
        "reporter_phone": "0912000002",
        "reporter_email": "gv.binh@dx-lab.example",
    },
}

# Họ tên hiển thị của người làm bước (AUTHZ mục 11)
NAMES = {
    "ktv.cuong": "Lê Văn Cường",
    "ktv.dung": "Phạm Thị Dung",
    "tl.giang": "Hoàng Thu Giang",
    "tk.hai": "Vũ Đức Hải",
    "ht.khanh": "Bùi Quốc Khánh",
}


@dataclass(frozen=True)
class Step:
    step_id: str  # trạng thái phiếu khi bước này đang chờ
    actor: str  # tài khoản demo làm bước
    data: dict[str, Any]


@dataclass(frozen=True)
class Scenario:
    key: str
    ref: str  # kịch bản trong docs/AUTHZ.md mục 12
    reporter: str
    title: str  # `issue_title` duy nhất: seed dùng để nhận ra phiếu đã tạo
    report: dict[str, Any]  # dữ liệu form báo hỏng (ngoài thông tin người báo)
    steps: tuple[Step, ...] = field(default_factory=tuple)
    target: str = ""  # trạng thái cuối cần đạt; rỗng = chạy hết các bước


def _today() -> str:
    return date.today().isoformat()


def _report(
    room_id: str, asset_id: str, category: str, title: str, description: str, urgency: str = "normal"
) -> dict[str, Any]:
    return {
        "room_id": room_id,
        "asset_id": asset_id,
        "asset_category": category,
        "issue_title": TITLE_PREFIX + title,
        "issue_description": description,
        "urgency": urgency,
        # Trường BPMN/DMN đọc (review APP-01 trên PR #56): mức ảnh hưởng và nguy cơ mất an toàn cho triage.dmn
        "impact": "single",
        "safety_hazard": False,
        "data_processing_consent": True,
        "consent_notice_version": "v1.0",
    }


def _assessment(tech: str, cause: str, action: str, cost: int, recommendation: str, quote_ref: str) -> Step:
    data: dict[str, Any] = {
        "technician_name": NAMES[tech],
        "inspection_date": _today(),
        "fault_cause": cause,
        "action_type": action,
        # Gateway sau bước kiểm tra rẽ theo `assessment_result`; `quote_count` so với `quotes_required` của authority.dmn
        "assessment_result": "not_repairable" if action == "replace" else "needs_cost",
        "is_emergency": False,
        "estimated_cost_vnd": cost,
        "technician_recommendation": recommendation,
    }
    if cost > 0:
        # Dưới 20.000.000 đồng cần 1 báo giá hoặc ước tính của kỹ thuật viên (docs/AUTHZ.md mục 5)
        data["quotes"] = [
            {
                "supplier_name": "Công ty TNHH Thiết bị Trường học Hà Nội (giả định)",
                "quote_amount_vnd": cost,
                "quote_reference": quote_ref,
                "quote_date": _today(),
            }
        ]
    data["quote_count"] = len(data.get("quotes", []))
    return Step("pending_assessment", tech, data)


def _confirm(manager: str = "tl.giang") -> Step:
    return Step(
        "awaiting_endorsement",
        manager,
        {
            "lab_manager_name": NAMES[manager],
            "confirm_date": _today(),
            "need_confirmed": True,
            "urgency_level": "normal",
            "replacement_procurement_requested": False,
            "manager_comment": "Xác nhận nhu cầu: thiết bị phục vụ giảng dạy thường xuyên của phòng.",
        },
    )


def scenarios() -> list[Scenario]:
    return [
        # Kịch bản 1: sv.an báo máy chiếu A1-305 không lên hình → vào hàng đợi it_technician
        Scenario(
            key="ca-1",
            ref="kịch bản 1",
            reporter="sv.an",
            title=TITLE_PREFIX + "Máy chiếu A1-305 không lên hình",
            report=_report(
                "lab-a1-305",
                "AST-PROJ-305-01",
                "projector",
                "Máy chiếu A1-305 không lên hình",
                "Máy chiếu bật đèn báo nguồn nhưng không có hình trên màn chiếu, đã thử đổi cáp HDMI.",
                "high",
            ),
            target="pending_assessment",
        ),
        # Kịch bản 2: ktv.cuong lập biên bản thay bóng chiếu 3.500.000 → chờ tl.giang xác nhận nhu cầu
        Scenario(
            key="ca-2",
            ref="kịch bản 2",
            reporter="gv.binh",
            title=TITLE_PREFIX + "Máy chiếu A1-305 mờ hình, nghi hỏng bóng",
            report=_report(
                "lab-a1-305",
                "AST-PROJ-305-01",
                "projector",
                "Máy chiếu A1-305 mờ hình, nghi hỏng bóng",
                "Hình chiếu mờ và ngả vàng, đèn LAMP trên thân máy nhấp nháy đỏ trong giờ giảng.",
            ),
            steps=(
                _assessment(
                    "ktv.cuong",
                    "Bóng đèn máy chiếu đã hết tuổi thọ, độ sáng giảm mạnh.",
                    "repair",
                    3_500_000,
                    "Thay bóng chiếu chính hãng.",
                    "BG-2026-0142",
                ),
            ),
            target="awaiting_endorsement",
        ),
        # Kịch bản 3: biên bản 12.000.000 → người duyệt ht.khanh (dòng 3)
        Scenario(
            key="ca-3",
            ref="kịch bản 3",
            reporter="sv.an",
            title=TITLE_PREFIX + "Máy tính trạm A1-305 không lên nguồn",
            report=_report(
                "lab-a1-305",
                "AST-PC-305-01",
                "computer",
                "Máy tính trạm A1-305 không lên nguồn",
                "Máy tính không lên nguồn, quạt không quay, đã thử cắm sang ổ điện khác.",
                "high",
            ),
            steps=(
                _assessment(
                    "ktv.cuong",
                    "Bo mạch chủ chập mạch cấp nguồn, cần thay bo mạch.",
                    "repair",
                    12_000_000,
                    "Thay bo mạch chủ tương thích, giữ nguyên CPU và RAM.",
                    "BG-2026-0153",
                ),
                _confirm(),
            ),
            target="awaiting_approval",
        ),
        # Kịch bản 12: không sửa được → tl.giang xuất phiếu đề nghị mua thay thế gửi Ban CSVC
        Scenario(
            key="ca-12",
            ref="kịch bản 12",
            reporter="gv.binh",
            title=TITLE_PREFIX + "Máy tính giảng viên A1-305 hỏng không sửa được",
            report=_report(
                "lab-a1-305",
                "AST-PC-305-02",
                "computer",
                "Máy tính giảng viên A1-305 hỏng không sửa được",
                "Máy tính giảng viên khởi động lại liên tục, mất dữ liệu ổ cứng, đã nhờ kiểm tra nhiều lần.",
            ),
            steps=(
                _assessment(
                    "ktv.cuong",
                    "Bo mạch chủ và ổ cứng hỏng, thiết bị đã hết bảo hành, không còn linh kiện thay thế.",
                    "replace",
                    18_000_000,
                    "Không sửa được; đề nghị mua thay thế.",
                    "BG-2026-0167",
                ),
            ),
            target="awaiting_handoff",
        ),
        # Ca hoàn tất: 3.500.000 qua xác nhận, duyệt (tk.hai, OTP), sửa, nghiệm thu
        Scenario(
            key="ca-hoan-tat",
            ref="ca hoàn tất",
            reporter="gv.binh",
            title=TITLE_PREFIX + "Điều hòa A1-305 chảy nước",
            report=_report(
                "lab-a1-305",
                "AST-AC-305-01",
                "hvac",
                "Điều hòa A1-305 chảy nước",
                "Điều hòa âm trần nhỏ nước xuống bàn thực hành, máy vẫn chạy nhưng làm lạnh kém.",
            ),
            steps=(
                _assessment(
                    "ktv.dung",
                    "Ống thoát nước ngưng bị tắc, dàn lạnh đóng bụi.",
                    "repair",
                    3_500_000,
                    "Thông ống thoát nước, vệ sinh dàn lạnh, bổ sung gas.",
                    "BG-2026-0171",
                ),
                _confirm(),
                Step(
                    "awaiting_approval",
                    "tk.hai",
                    {
                        "approver_name": NAMES["tk.hai"],
                        "approver_role": "faculty_head",
                        "signing_type": "direct",
                        "decision": "approved",
                        "approved_amount_vnd": 3_500_000,
                        "approval_date": _today(),
                        "approval_comment": "Đồng ý sửa theo biên bản và báo giá đính kèm.",
                    },
                ),
                Step(
                    "repairing",
                    "ktv.dung",
                    {
                        "technician_name": NAMES["ktv.dung"],
                        "repair_date": _today(),
                        "work_performed": "Thông ống thoát nước ngưng, vệ sinh dàn lạnh, bổ sung gas R410A.",
                        "parts_replaced": "Gas R410A",
                        "actual_cost_vnd": 3_500_000,
                        "repair_status": "completed",
                        "technical_notes": "Máy đã hết chảy nước, nhiệt độ phòng về 24 độ C sau 20 phút.",
                    },
                ),
                Step(
                    "awaiting_acceptance",
                    "tl.giang",
                    {
                        "acceptor_name": NAMES["tl.giang"],
                        "acceptor_role": "lab_manager",
                        "acceptance_date": _today(),
                        "operational_status": "normal",
                        "acceptance_result": "accepted",
                        "acceptance_notes": "Điều hòa hoạt động bình thường, không còn chảy nước.",
                        "handover_signed": True,
                    },
                ),
            ),
            target="completed",
        ),
    ]


# Tiêu đề là khóa nhận biết phiếu đã tạo: phải trùng `issue_title` của form báo hỏng.
for _scenario in scenarios():
    assert _scenario.title == _scenario.report["issue_title"], _scenario.key
