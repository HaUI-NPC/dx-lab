# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

"""Kiểm tra giao diện hộp việc và dữ liệu báo giá."""

from dxlab_portal.pages.forms.spec import build_form
from dxlab_portal.pages.forms.validate import validate_form
from dxlab_portal.pages.my_tasks import _value


def test_mang_bao_gia_duoc_gui_voi_kieu_json():
    schema = {"type": "object", "properties": {"quotes": {"type": "array", "items": {"type": "object"}}}}
    spec = build_form(schema, None)
    data, errors = validate_form(spec, {"quotes": '[{"supplier_name":"Công ty A","quote_amount_vnd":100}]'})
    assert errors == {}
    assert data == {"quotes": [{"supplier_name": "Công ty A", "quote_amount_vnd": 100}]}
    assert validate_form(spec, {"quotes": "không phải JSON"})[1]["quotes"]


def test_can_cu_gia_dinh_duoc_danh_nhan():
    assert "giả định" in _value("GĐ-PC-01/2026")
