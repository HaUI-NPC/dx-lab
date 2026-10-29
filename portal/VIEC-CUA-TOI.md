<!--
SPDX-FileCopyrightText: 2026 DX-Lab contributors

SPDX-License-Identifier: CC-BY-4.0
-->

# Việc của tôi

Sau khi đăng nhập, chọn **Việc của tôi** để xem các bước core giao cho tài khoản. Chọn tên bước để xem chi tiết phiếu, lịch sử và form xử lý; nhập dữ liệu rồi chọn **Hoàn thành**. Phiếu quá hạn được đánh dấu trong hộp việc. Thông tin cá nhân chỉ xuất hiện khi core cho phép xem.

Trường danh sách báo giá nhận một mảng JSON, mỗi phần tử là một báo giá với các khóa được schema yêu cầu. Ví dụ: `[{"supplier_name":"Công ty A", "quote_amount_vnd":1000000, "quote_reference":"BG-01"}]`. Core kiểm tra dữ liệu và quyền khi hoàn thành bước.
