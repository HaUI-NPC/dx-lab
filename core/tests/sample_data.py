# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

"""Dữ liệu mẫu cho test records, documents, search: phòng theo `data/rooms.json` của APP-03 (PR #55) và hai SOP ngắn."""

from collections.abc import Callable
from typing import Any

# Chữ ký của fixture `headers_for` trong conftest.py.
HeadersFactory = Callable[..., dict[str, str]]

APP_ID = "lab-repair"
ROOM_TYPE = "room"

ROOM_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "Phòng thực hành, phòng thí nghiệm",
    "type": "object",
    "required": ["id", "code", "name", "org_path", "capacity", "status"],
    "additionalProperties": False,
    "properties": {
        "id": {"type": "string", "minLength": 1},
        "code": {"type": "string", "minLength": 1},
        "name": {"type": "string", "minLength": 1},
        "building": {"type": "string"},
        "floor": {"type": "integer", "minimum": 0},
        "org_path": {"type": "string", "pattern": "^/haui(/[a-z0-9-]+)+$"},
        "unit_name": {"type": "string"},
        "school_name": {"type": "string"},
        "manager_role": {"type": "string"},
        "capacity": {"type": "integer", "minimum": 1},
        "status": {"enum": ["active", "inactive"]},
        "description": {"type": "string"},
    },
}

ROOMS: list[dict[str, Any]] = [
    {
        "id": "lab-a1-305",
        "code": "A1-305",
        "name": "Phòng thực hành máy tính A1-305",
        "building": "Nhà A1",
        "floor": 3,
        "org_path": "/haui/sict/khmt/lab-a1-305",
        "unit_name": "Khoa Khoa học máy tính",
        "school_name": "Trường Công nghệ thông tin và Truyền thông",
        "manager_role": "lab_manager",
        "capacity": 40,
        "status": "active",
    },
    {
        "id": "lab-a1-306",
        "code": "A1-306",
        "name": "Phòng thực hành máy tính A1-306",
        "building": "Nhà A1",
        "floor": 3,
        "org_path": "/haui/sict/khmt/lab-a1-306",
        "unit_name": "Khoa Khoa học máy tính",
        "school_name": "Trường Công nghệ thông tin và Truyền thông",
        "manager_role": "lab_manager",
        "capacity": 40,
        "status": "active",
    },
    {
        "id": "lab-a1-601",
        "code": "A1-601",
        "name": "Phòng thực hành mạng A1-601",
        "building": "Nhà A1",
        "floor": 6,
        "org_path": "/haui/sict/mmt/lab-a1-601",
        "unit_name": "Khoa Mạng máy tính và Truyền thông",
        "school_name": "Trường Công nghệ thông tin và Truyền thông",
        "manager_role": "lab_manager",
        "capacity": 35,
        "status": "active",
    },
    {
        "id": "lab-a10-201",
        "code": "A10-201",
        "name": "Phòng thí nghiệm điện A10-201",
        "building": "Nhà A10",
        "floor": 2,
        "org_path": "/haui/truong-dien-dien-tu/khoa-dien/lab-a10-201",
        "unit_name": "Khoa Điện",
        "school_name": "Trường Điện – Điện tử",
        "manager_role": "lab_manager",
        "capacity": 30,
        "status": "active",
    },
]

ROOMS_SOURCE = "data/rooms.json của dự án DX-Lab (APP-03)"
ROOMS_LICENSE = "CC-BY-4.0"

SOP_PC = """# Máy tính không lên nguồn (SOP-IT-01)

## Mục đích
Hướng dẫn chẩn đoán máy tính để bàn không lên nguồn trong phòng thực hành.
Từ khóa tìm kiếm: `may tinh khong len`, `máy tính không lên`, `bat may khong len`.

## Các bước
1. Kiểm tra ổ cắm và cáp nguồn AC cắm chặt hai đầu.
2. Bật công tắc phụ phía sau bộ nguồn (PSU) về vị trí I.
3. Kiểm tra nút nguồn và dây Power SW nối vào bo mạch chủ.
"""

SOP_PROJECTOR = """# Máy chiếu không nhận tín hiệu (SOP-IT-02)

## Mục đích
Hướng dẫn xử lý máy chiếu báo No Signal hoặc mờ hình.
Từ khóa tìm kiếm: `may chieu khong len`, `khong nhan hdmi`, `khong nhan vga`.

## Các bước
1. Kiểm tra cáp HDMI hoặc VGA cắm chặt.
2. Chọn đúng nguồn vào (Source) trên máy chiếu.
"""

# Tài khoản demo (docs/AUTHZ.md mục 11): (tên đăng nhập, nhóm trong token).
CSVC_LAN = ("csvc.lan", ["/haui/ban-csvc/facility_officer", "/haui/ban-csvc/rule_admin"])
QT_SON = ("qt.son", ["/haui/tt-cntt/process_admin"])
ADMIN_DX = ("admin.dx", ["/haui/tt-cntt/system_admin"])
SV_AN = ("sv.an", [])
IT_TECH = ("kt.hung", ["/haui/tt-cntt/it_technician"])
