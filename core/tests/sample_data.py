# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

"""Dữ liệu mẫu cho test records, documents: phòng, tài sản theo APP-03 (PR #55), schema theo APP-01 (PR #69), và các SOP ngắn."""

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

# Chữ ký của fixture `headers_for` trong conftest.py.
HeadersFactory = Callable[..., dict[str, str]]

APP_ID = "lab-repair"
ROOM_TYPE = "room"
ASSET_TYPE = "asset"

# Schema đúng như `apps/lab-repair/records/*-record.json` (APP-01, PR #69); chép sang `tests/data/` để test không phụ thuộc thứ tự merge.
_DATA = Path(__file__).with_name("data")
ROOM_SCHEMA: dict[str, Any] = json.loads((_DATA / "room-record.json").read_text(encoding="utf-8"))
ASSET_SCHEMA: dict[str, Any] = json.loads((_DATA / "asset-record.json").read_text(encoding="utf-8"))

# Bản ghi chép từ `data/rooms.json` và `data/assets.json` của APP-03 (PR #55).
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
        "description": "Phòng thực hành chuyên ngành Khoa học máy tính, trang bị máy trạm thực hành lập trình và tính toán."
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
        "description": "Phòng thực hành lập trình ứng dụng và hệ thống phân tán."
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
        "description": "Phòng thực hành thiết kế, cấu hình mạng và an toàn thông tin."
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
        "description": "Phòng thí nghiệm đo lường điện, khí cụ điện và mạch vi điều khiển."
    }
]

ASSETS: list[dict[str, Any]] = [
    {
        "id": "AST-PC-305-01",
        "code": "TS-2024-00101",
        "name": "Máy tính trạm Dell OptiPlex 7090",
        "category": "computer",
        "room_id": "lab-a1-305",
        "room_code": "A1-305",
        "org_path": "/haui/sict/khmt/lab-a1-305",
        "tech_unit_path": "/haui/tt-cntt",
        "model": "Dell OptiPlex 7090 Tower",
        "serial_number": "SN-DELL-7090-00101",
        "purchase_year": 2023,
        "warranty_expiry": "2026-12-31",
        "original_value_vnd": 24500000,
        "current_value_vnd": 18000000,
        "status": "in_use",
        "specifications": {
            "cpu": "Intel Core i7-11700",
            "ram": "32GB DDR4",
            "storage": "512GB NVMe SSD + 1TB HDD",
            "os": "Ubuntu 24.04 LTS"
        }
    },
    {
        "id": "AST-PC-305-02",
        "code": "TS-2024-00102",
        "name": "Máy tính giảng viên HP ProDesk 400 G7",
        "category": "computer",
        "room_id": "lab-a1-305",
        "room_code": "A1-305",
        "org_path": "/haui/sict/khmt/lab-a1-305",
        "tech_unit_path": "/haui/tt-cntt",
        "model": "HP ProDesk 400 G7 SFF",
        "serial_number": "SN-HP-400G7-00102",
        "purchase_year": 2023,
        "warranty_expiry": "2026-11-30",
        "original_value_vnd": 19500000,
        "current_value_vnd": 14000000,
        "status": "in_use",
        "specifications": {
            "cpu": "Intel Core i5-10500",
            "ram": "16GB DDR4",
            "storage": "256GB SSD",
            "os": "Windows 11 Pro Education"
        }
    }
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

SOP_NETWORK = """# Mất kết nối mạng LAN (SOP-IT-04)

## Mục đích
Hướng dẫn xử lý phòng thực hành bị mất mạng.
Từ khóa tìm kiếm: `mat mang`, `mất mạng lan`, `không vào được mạng`.

## Các bước
1. Kiểm tra dây mạng RJ45 cắm chặt vào cổng switch.
2. Khởi động lại switch tầng và kiểm tra đèn tín hiệu.
"""

QUOTE_TEXT = """Báo giá thay bộ nguồn máy tính không lên: 1.850.000 đồng.
Nhà cung cấp A, hiệu lực đến 30/11/2026.
"""
