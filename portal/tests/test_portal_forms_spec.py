# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

"""Form động: dựng từ JSON Schema + uischema và kiểm tra tiếng Việt theo từng trường."""

from __future__ import annotations

from typing import Any

from dxlab_portal.pages.forms.spec import FormField, Layout, build_form
from dxlab_portal.pages.forms.validate import validate_form
from portal_fakes import VALID_REPORT, load_app_json


def report_spec():  # type: ignore[no-untyped-def]
    return build_form(
        load_app_json("lab-repair", "report-schema.json"), load_app_json("lab-repair", "report-uischema.json")
    )


def names(node: Any) -> list[str]:
    if isinstance(node, FormField):
        return [node.name]
    if isinstance(node, Layout):
        return [n for child in node.children for n in names(child)]
    return []


# --- Form báo hỏng thật của APP-02 ---


def test_o_dong_thuan_khong_tick_san() -> None:
    consent = {f.name: f for f in report_spec().fields}["data_processing_consent"]
    assert consent.kind == "checkbox"
    assert consent.initial is False


def test_bao_hong_hop_le_khong_loi_va_gui_kem_phien_ban_thong_bao() -> None:
    data, errors = validate_form(report_spec(), VALID_REPORT)
    assert errors == {}
    assert data["consent_notice_version"] == "v1.0"
    assert data["data_processing_consent"] is True and data["urgency"] == "high"


def test_moi_form_cua_lab_repair_dung_duoc_va_de_trong_thi_bao_loi_cho_truong_bat_buoc() -> None:
    for step in ("report", "assessment", "confirm-need", "approval", "repair", "acceptance", "handoff"):
        schema = load_app_json("lab-repair", f"{step}-schema.json")
        spec = build_form(schema, load_app_json("lab-repair", f"{step}-uischema.json"))
        shown = {f.name for f in spec.fields}
        # Mọi trường bắt buộc nhập được đều hiện trên form (hoặc là kiểu chưa hỗ trợ, có thông báo riêng).
        unsupported = {p for p, v in schema["properties"].items() if v["type"] in ("array", "object")}
        assert set(schema["required"]) <= shown | unsupported, step
        _, errors = validate_form(spec, {})
        assert {f.name for f in spec.fields if f.required and f.kind != "checkbox"} <= set(errors), step


# --- Hành vi chung, không phụ thuộc gói ứng dụng ---

SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["amount", "count", "approved", "decision", "note"],
    "properties": {
        "amount": {"type": "integer", "title": "Số tiền duyệt chi", "minimum": 0, "maximum": 20000000},
        "count": {"type": "number", "title": "Hệ số", "exclusiveMinimum": 0},
        "approved": {"type": "boolean", "title": "Đã duyệt", "default": True},
        "decision": {
            "type": "string",
            "title": "Quyết định",
            "oneOf": [{"const": "approved", "title": "Duyệt"}, {"const": "rejected", "title": "Từ chối"}],
        },
        "note": {"type": "string", "title": "Ý kiến", "minLength": 5},
        "when": {"type": "string", "format": "date", "title": "Ngày duyệt"},
        "attachments": {"type": "array", "title": "Tệp đính kèm", "items": {"type": "string"}},
    },
}
UISCHEMA: dict[str, Any] = {
    "type": "VerticalLayout",
    "elements": [
        {"type": "Control", "scope": "#/properties/decision", "options": {"format": "radio"}},
        {
            "type": "Control",
            "scope": "#/properties/note",
            "label": "Ý kiến chỉ đạo",
            "options": {"multi": True},
        },
        {"type": "Control", "scope": "#/properties/amount"},
    ],
}


def test_uischema_quyet_dinh_thu_tu_radio_textarea_nhan_va_ep_hien_truong_bat_buoc() -> None:
    spec = build_form(SCHEMA, UISCHEMA)
    assert (
        names(spec.root) == ["decision", "note", "amount", "count", "approved"] + []
    )  # trường bắt buộc còn lại nối cuối
    by_name = {f.name: f for f in spec.fields}
    assert by_name["decision"].kind == "radio"
    assert [(o.value, o.label) for o in by_name["decision"].options] == [
        ("approved", "Duyệt"),
        ("rejected", "Từ chối"),
    ]
    assert by_name["note"].kind == "textarea" and by_name["note"].label == "Ý kiến chỉ đạo"
    assert by_name["note"].title == "Ý kiến"  # thông báo lỗi dùng title của schema
    assert by_name["amount"].kind == "integer" and by_name["approved"].initial is True


def test_so_nguyen_va_so_thuc_duoc_chuyen_kieu_va_kiem_rang_buoc() -> None:
    spec = build_form(SCHEMA, UISCHEMA)
    base = {
        "amount": "3500000",
        "count": "1,5",
        "approved": True,
        "decision": "approved",
        "note": "Đồng ý sửa",
    }
    data, errors = validate_form(spec, base)
    assert errors == {} and data["amount"] == 3500000 and data["count"] == 1.5

    _, errors = validate_form(spec, {**base, "amount": "-1", "count": "0", "decision": "khac"})
    assert errors == {
        "amount": "Số tiền duyệt chi phải từ 0 trở lên.",
        "count": "Hệ số phải lớn hơn 0.",
        "decision": "Giá trị của quyết định không nằm trong danh sách lựa chọn.",
    }
    _, errors = validate_form(spec, {**base, "amount": "25000000"})
    assert errors == {"amount": "Số tiền duyệt chi không được vượt quá 20.000.000."}
    _, errors = validate_form(spec, {**base, "amount": "12,5", "count": "một"})
    assert errors == {"amount": "Số tiền duyệt chi phải là số nguyên.", "count": "Hệ số phải là một số."}


def test_truong_tuy_chon_de_trong_khong_gui_va_ngay_sai_bi_bao_loi() -> None:
    spec = build_form(SCHEMA, None)  # không có uischema thì hiện đủ mọi trường
    base = {"amount": "0", "count": "1", "approved": False, "decision": "rejected", "note": "Không đạt"}
    data, errors = validate_form(spec, base)
    assert errors == {} and "when" not in data and data["approved"] is False
    _, errors = validate_form(spec, {**base, "when": "31/02/2026"})
    assert errors == {"when": "Ngày duyệt chưa phải ngày hợp lệ."}
    data, _ = validate_form(spec, {**base, "when": "2026-10-29"})
    assert data["when"] == "2026-10-29"


def test_truong_kieu_mang_duoc_hien_va_gui() -> None:
    spec = build_form(SCHEMA, None)
    assert {f.name: f.kind for f in spec.fields}["attachments"] == "array"
    data, errors = validate_form(spec, {
        "amount": "0", "count": "1", "approved": False,
        "decision": "rejected", "note": "Không đạt", "attachments": '["a.pdf"]',
    })
    assert errors == {}
    assert data["attachments"] == ["a.pdf"]


def test_o_danh_dau_const_khong_bao_gio_tick_san_ke_ca_khi_schema_dat_mac_dinh_true() -> None:
    schema = {
        "type": "object",
        "required": ["consent"],
        "properties": {"consent": {"type": "boolean", "title": "Đồng thuận", "const": True, "default": True}},
    }
    spec = build_form(schema, None)
    assert spec.fields[0].initial is False
    _, errors = validate_form(spec, {"consent": False})
    assert errors == {"consent": "Bạn cần đánh dấu ô “Đồng thuận” để tiếp tục."}
    data, errors = validate_form(spec, {"consent": "true"})
    assert errors == {} and data == {"consent": True}


# Chuỗi, nhóm và giá trị mặc định: kiểm trên schema riêng của test để test không gãy mỗi khi gói ứng dụng đổi form.
TEXT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["ho_ten", "dien_thoai", "email", "phong", "mo_ta", "dong_y"],
    "properties": {
        "ho_ten": {"type": "string", "title": "Họ và tên", "minLength": 2},
        "dien_thoai": {"type": "string", "title": "Số điện thoại", "pattern": "^[0-9+]{9,15}$"},
        "email": {"type": "string", "title": "Email", "format": "email"},
        "phong": {"type": "string", "title": "Phòng", "enum": ["p1", "p2"]},
        "mo_ta": {"type": "string", "title": "Mô tả", "maxLength": 10},
        "dong_y": {"type": "boolean", "title": "Đồng thuận", "const": True},
        "phien_ban": {"type": "string", "title": "Phiên bản", "default": "v1.0"},
    },
}
TEXT_UISCHEMA: dict[str, Any] = {
    "type": "VerticalLayout",
    "elements": [
        {"type": "Group", "label": "1. Người báo", "elements": [
            {"type": "Control", "scope": "#/properties/ho_ten"},
            {"type": "Control", "scope": "#/properties/dien_thoai"},
            {"type": "Control", "scope": "#/properties/email"},
        ]},
        {"type": "Control", "scope": "#/properties/phong"},
        {"type": "Control", "scope": "#/properties/mo_ta", "options": {"multi": True, "rows": 4}},
        {"type": "Control", "scope": "#/properties/dong_y"},
    ],
}  # fmt: skip


def test_nhom_kieu_o_nhap_va_mac_dinh_an_lay_tu_schema() -> None:
    spec = build_form(TEXT_SCHEMA, TEXT_UISCHEMA)
    by_name = {f.name: f for f in spec.fields}

    assert [c.label for c in spec.root.children if isinstance(c, Layout)] == ["1. Người báo"]
    assert (by_name["mo_ta"].kind, by_name["mo_ta"].rows) == ("textarea", 4)
    assert (by_name["email"].kind, by_name["phong"].kind) == ("email", "select")
    # Trường không có trên uischema nhưng schema có mặc định thì vẫn được gửi kèm.
    assert spec.hidden_defaults == {"phien_ban": "v1.0"}
    data, errors = validate_form(spec, {"ho_ten": "An", "dien_thoai": "0901234567", "email": "a@b.vn",
                                        "phong": "p1", "mo_ta": "ngắn", "dong_y": True})
    assert errors == {} and data["phien_ban"] == "v1.0"


def test_de_trong_va_sai_rang_buoc_bao_loi_tieng_viet_dung_tung_truong() -> None:
    spec = build_form(TEXT_SCHEMA, TEXT_UISCHEMA)

    _, empty = validate_form(spec, {})
    _, wrong = validate_form(spec, {"ho_ten": "A", "dien_thoai": "abc", "email": "x", "phong": "p9",
                                    "mo_ta": "x" * 11, "dong_y": True})

    assert empty == {
        "ho_ten": "Vui lòng nhập họ và tên.",
        "dien_thoai": "Vui lòng nhập số điện thoại.",
        "email": "Vui lòng nhập email.",
        "phong": "Vui lòng chọn phòng.",
        "mo_ta": "Vui lòng nhập mô tả.",
        "dong_y": "Bạn cần đánh dấu ô “Đồng thuận” để tiếp tục.",
    }
    assert wrong == {
        "ho_ten": "Họ và tên cần có ít nhất 2 ký tự (hiện có 1).",
        "dien_thoai": "Số điện thoại chưa đúng định dạng.",
        "email": "Email chưa hợp lệ, cần có dạng ten@ten-mien.",
        "phong": "Giá trị của phòng không nằm trong danh sách lựa chọn.",
        "mo_ta": "Mô tả chỉ được tối đa 10 ký tự (hiện có 11).",
    }
