# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

"""Cổng duy nhất nạp định nghĩa ứng dụng vào core (docs/ARCHITECTURE.md mục 7, 4 cửa kiểm soát).

1. Đúng người: quyền nạp theo loại tệp thay đổi (`rule_admin` chỉ `.dmn`, `process_admin` mọi loại).
2. An toàn: validator từ chối mã chạy được (script, điều kiện ngoài so sánh, phần tử BPMN lạ).
3. Phiên bản: mỗi lần nạp là một phiên bản mới chờ `process_owner` duyệt; việc đang chạy giữ phiên bản cũ.
4. Lịch sử: audit `definition.publish`, `definition.activate`.
"""
